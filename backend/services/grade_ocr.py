"""Grade-entry autopilot (automation D, teachers group) — OCR by vision AI.

The teacher photographs a marked paper list; a vision-capable provider
(OpenAI or Anthropic, per platform decision) extracts (name, score) pairs;
the pairs are fuzzy-matched against the ASSESSMENT'S REAL ROSTER and returned
as proposals — nothing is written until the teacher confirms. Confirmation
upserts `Grade` rows (update if the student already has one).

Design rules:
- Vision has no local fallback: without a reachable vision provider the scan
  fails honestly (503), it never fabricates scores.
- The AI only transcribes; the roster mapping is deterministic
  (difflib ratio on normalized names) so a low-confidence match is visible
  and editable before anything is saved.
- Scans are AI-credit-gated on the teacher (images billed with a flat
  surcharge on top of the prompt estimate).
"""

import base64
import json
import re
import unicodedata
from difflib import SequenceMatcher

from fastapi import HTTPException
from sqlalchemy.orm import Session

from .. import models
from ..services.ai_service import ai_service
from . import ai_credits

IMAGE_MIME_TYPES = {"image/png", "image/jpeg", "image/webp"}
MAX_IMAGE_BYTES = 8 * 1024 * 1024
IMAGE_CREDIT_SURCHARGE = 6  # flat credits added per scanned image
MATCH_THRESHOLD = 0.55


def _normalize(name: str) -> str:
    text = unicodedata.normalize("NFKD", name or "").encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z ]", "", text.lower()).strip()


def _similarity(a: str, b: str) -> float:
    na, nb = _normalize(a), _normalize(b)
    if not na or not nb:
        return 0.0
    direct = SequenceMatcher(None, na, nb).ratio()
    # Order-insensitive pass: "DUPONT Marie" vs "Marie Dupont".
    sorted_ratio = SequenceMatcher(None, " ".join(sorted(na.split())), " ".join(sorted(nb.split()))).ratio()
    return max(direct, sorted_ratio)


def _assessment_with_roster(db: Session, assessment_id: int, school_id: int):
    row = (
        db.query(models.Assessment, models.Class)
        .join(models.Class, models.Class.id == models.Assessment.class_id)
        .filter(models.Assessment.id == assessment_id, models.Class.school_id == school_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Évaluation introuvable dans votre établissement.")
    assessment, cls = row
    roster = (
        db.query(models.StudentProfile, models.User)
        .join(models.User, models.User.id == models.StudentProfile.user_id)
        .filter(models.StudentProfile.current_class_id == cls.id, models.User.is_active == True)  # noqa: E712
        .all()
    )
    return assessment, cls, roster


def _parse_entries(content: str) -> list:
    """Tolerant JSON-array extraction from the vision response."""
    stripped = (content or "").strip()
    match = re.search(r"\[.*\]", stripped, flags=re.DOTALL)
    if not match:
        return []
    try:
        parsed = json.loads(match.group(0))
    except json.JSONDecodeError:
        return []
    entries = []
    for item in parsed if isinstance(parsed, list) else []:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        try:
            score = float(item.get("score"))
        except (TypeError, ValueError):
            continue
        if name:
            entries.append({"name": name, "score": score})
    return entries


def scan_grade_sheet(
    db: Session,
    assessment_id: int,
    school_id: int,
    current_user: models.User,
    *,
    image_bytes: bytes,
    mime_type: str,
) -> dict:
    """Vision-extract (name, score) pairs and map them onto the real roster."""
    if mime_type not in IMAGE_MIME_TYPES:
        raise HTTPException(status_code=415, detail="Format non accepté. Utilisez une photo JPG, PNG ou WebP.")
    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Image trop lourde (limite 8 Mo).")
    assessment, cls, roster = _assessment_with_roster(db, assessment_id, school_id)
    if not roster:
        raise HTTPException(status_code=422, detail="Aucun élève actif dans la classe de cette évaluation.")
    max_score = assessment.max_score or 20

    prompt = (
        "This photo shows a teacher's marked paper list of student scores. Transcribe every "
        "(student name, score) pair you can read. Scores are out of "
        f"{max_score}. Return ONLY a JSON array like "
        '[{"name": "...", "score": 12.5}] — no commentary, no markdown. Transcribe names exactly '
        "as written; do not guess unreadable entries (skip them)."
    )
    ai_credits.ensure_credits(db, current_user, ai_credits.estimate_credits(prompt) + IMAGE_CREDIT_SURCHARGE)
    image_base64 = base64.b64encode(image_bytes).decode("ascii")
    try:
        result = ai_service.generate_vision_response(prompt, image_base64, mime_type, db)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    ai_credits.record_usage(db, current_user, prompt, result.get("content") or "", "automation_grade_ocr", "grade_scan")

    extracted = _parse_entries(result.get("content") or "")
    existing_scores = {
        grade.student_id: grade.score
        for grade in db.query(models.Grade).filter(models.Grade.assessment_id == assessment.id).all()
    }

    proposals, unmatched, used_students = [], [], set()
    for entry in extracted:
        best_profile, best_user, best_ratio = None, None, 0.0
        for profile, user in roster:
            if profile.id in used_students:
                continue
            ratio = _similarity(entry["name"], user.full_name or "")
            if ratio > best_ratio:
                best_profile, best_user, best_ratio = profile, user, ratio
        if best_profile and best_ratio >= MATCH_THRESHOLD:
            used_students.add(best_profile.id)
            proposals.append({
                "student_id": best_profile.id,
                "student_name": best_user.full_name,
                "extracted_name": entry["name"],
                "score": entry["score"],
                "confidence": round(best_ratio, 2),
                "existing_score": existing_scores.get(best_profile.id),
                "out_of_range": not (0 <= entry["score"] <= max_score),
            })
        else:
            unmatched.append(entry)

    missing = [
        {"student_id": profile.id, "student_name": user.full_name}
        for profile, user in roster if profile.id not in used_students
    ]
    return {
        "assessment_id": assessment.id,
        "assessment_title": assessment.title,
        "class_name": cls.name,
        "max_score": max_score,
        "model_name": result.get("model_name"),
        "proposals": proposals,
        "unmatched": unmatched,
        "missing_students": missing,
    }


def confirm_grades(
    db: Session,
    assessment_id: int,
    school_id: int,
    current_user: models.User,
    *,
    entries: list,
) -> dict:
    """Teacher-confirmed upsert of the proposed scores."""
    assessment, _cls, roster = _assessment_with_roster(db, assessment_id, school_id)
    max_score = assessment.max_score or 20
    roster_ids = {profile.id for profile, _user in roster}

    created, updated = 0, 0
    for entry in entries:
        student_id, score = entry.student_id, entry.score
        if student_id not in roster_ids:
            raise HTTPException(status_code=422, detail=f"L'élève #{student_id} n'appartient pas à la classe de cette évaluation.")
        if not (0 <= score <= max_score):
            raise HTTPException(status_code=422, detail=f"Note {score} hors barème (0–{max_score}).")
        grade = db.query(models.Grade).filter(
            models.Grade.assessment_id == assessment.id,
            models.Grade.student_id == student_id,
        ).first()
        if grade:
            grade.score = score
            updated += 1
        else:
            db.add(models.Grade(assessment_id=assessment.id, student_id=student_id, score=score))
            created += 1
    return {"assessment_id": assessment.id, "created": created, "updated": updated}
