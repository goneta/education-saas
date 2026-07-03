"""Séquence builder (automation D, teachers group).

Generates a term's lesson sequence for a (class, subject) pair from the REAL
timetable: the number of weekly slots and their durations come from the
class's actual `Timetable` entries, the week count from the chosen `Term`'s
dates. The AI lesson generator then pre-fills the whole progression —
week-by-week sessions with title, objectives, activities and a short
assessment idea — in one generation (credit-gated on the teacher).

The generated sequence is also recorded as a `sequence.generated` notification
to the teacher, so it stays retrievable after the page is closed.
"""

from datetime import datetime, time

from fastapi import HTTPException
from sqlalchemy.orm import Session

from .. import models
from ..services.ai_service import ai_service
from . import ai_credits, automation


def _slot_minutes(entry: models.Timetable) -> int:
    if entry.duration_minutes:
        return entry.duration_minutes
    if isinstance(entry.start_time, time) and isinstance(entry.end_time, time):
        return max((entry.end_time.hour * 60 + entry.end_time.minute) - (entry.start_time.hour * 60 + entry.start_time.minute), 0)
    return 0


def list_sequence_options(db: Session, school_id: int) -> dict:
    """(class, subject) pairs that actually have timetable slots + the school's terms."""
    entries = (
        db.query(models.Timetable, models.Class, models.Subject)
        .join(models.Class, models.Class.id == models.Timetable.class_id)
        .join(models.Subject, models.Subject.id == models.Timetable.subject_id)
        .filter(models.Class.school_id == school_id)
        .all()
    )
    pairs: dict = {}
    for entry, cls, subject in entries:
        key = (cls.id, subject.id)
        if key not in pairs:
            pairs[key] = {"class_id": cls.id, "class_name": cls.name, "level": cls.level,
                          "subject_id": subject.id, "subject_name": subject.name,
                          "weekly_slots": 0, "weekly_minutes": 0}
        pairs[key]["weekly_slots"] += 1
        pairs[key]["weekly_minutes"] += _slot_minutes(entry)

    terms = (
        db.query(models.Term)
        .join(models.AcademicYear, models.AcademicYear.id == models.Term.academic_year_id)
        .filter(models.AcademicYear.school_id == school_id, models.AcademicYear.is_current == True)  # noqa: E712
        .order_by(models.Term.start_date.asc())
        .all()
    )
    return {
        "pairs": sorted(pairs.values(), key=lambda p: (p["class_name"], p["subject_name"])),
        "terms": [
            {"id": term.id, "name": term.name, "start_date": term.start_date, "end_date": term.end_date}
            for term in terms
        ],
    }


def build_sequence(
    db: Session,
    school_id: int,
    current_user: models.User,
    *,
    class_id: int,
    subject_id: int,
    term_id: int,
    topic: str = "",
    language: str = "fr",
) -> dict:
    """Generate the term's lesson sequence from the pair's real weekly slots."""
    cls = db.query(models.Class).filter(models.Class.id == class_id, models.Class.school_id == school_id).first()
    if not cls:
        raise HTTPException(status_code=404, detail="Classe introuvable dans votre établissement.")
    subject = db.query(models.Subject).filter(models.Subject.id == subject_id).first()
    term = db.query(models.Term).filter(models.Term.id == term_id).first()
    if not subject or not term:
        raise HTTPException(status_code=404, detail="Matière ou période introuvable.")

    entries = db.query(models.Timetable).filter(
        models.Timetable.class_id == class_id,
        models.Timetable.subject_id == subject_id,
    ).all()
    if not entries:
        raise HTTPException(status_code=422, detail="Aucun créneau dans l'emploi du temps pour cette classe et cette matière.")

    weekly_slots = len(entries)
    weekly_minutes = sum(_slot_minutes(entry) for entry in entries)
    weeks = 12
    if isinstance(term.start_date, datetime) and isinstance(term.end_date, datetime) and term.end_date > term.start_date:
        weeks = max((term.end_date - term.start_date).days // 7, 1)
    sessions = weekly_slots * weeks

    prompt = (
        f"Create a complete term lesson sequence ('séquence pédagogique') in {language} for subject "
        f"'{subject.name}', class '{cls.name}'{f' (level {cls.level})' if cls.level else ''}, term "
        f"'{term.name}'. The real timetable gives {weekly_slots} session(s) per week "
        f"({weekly_minutes} minutes weekly) over about {weeks} weeks — roughly {sessions} sessions in total. "
        f"{f'Focus of the term: {topic}. ' if topic else ''}"
        "Structure it week by week: for each session give a title, the objective, the main activities and, "
        "every few weeks, a short formative assessment. End with the term's summative assessment. "
        "Keep each session entry compact and classroom-ready."
    )
    ai_credits.ensure_credits(db, current_user, ai_credits.estimate_credits(prompt))
    result = ai_service.generate_response_from_config(prompt, {"module": "automation_sequence"}, db)
    content = result.get("data") or result.get("message") or ""
    ai_credits.record_usage(db, current_user, prompt, content, "automation_sequence", "sequence")

    automation.record_notification(
        db,
        event_type="sequence.generated",
        subject=f"Séquence {subject.name} — {cls.name} ({term.name})",
        message=content,
        school_id=school_id,
        recipient_user=current_user,
        source_type="timetable_sequence",
        source_id=class_id,
        current_user=current_user,
    )

    return {
        "class_name": cls.name,
        "subject_name": subject.name,
        "term_name": term.name,
        "weekly_slots": weekly_slots,
        "weekly_minutes": weekly_minutes,
        "weeks": weeks,
        "sessions": sessions,
        "sequence": content,
    }
