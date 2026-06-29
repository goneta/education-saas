"""Academic computations — automatic GPA from existing grades.

Slice 3 (Loop 3 gap). Pure computation over `Grade` + `Assessment` (each grade's
`score` against the assessment `max_score`, weighted by the assessment `weight`/
coefficient). No new tables; the single source of truth stays the grades data.
"""

from typing import Optional

from sqlalchemy.orm import Session

from .. import models


def compute_gpa(db: Session, student_id: int, term_id: Optional[int] = None) -> dict:
    """Weighted GPA for a student, optionally scoped to a term.

    Returns the percentage, a 0-20 average, a 4.0-scale GPA, the total weight and
    a per-subject breakdown. Subjects with no usable max_score are skipped.
    """
    query = (
        db.query(models.Grade, models.Assessment)
        .join(models.Assessment, models.Grade.assessment_id == models.Assessment.id)
        .filter(models.Grade.student_id == student_id)
    )
    if term_id is not None:
        query = query.filter(models.Assessment.term_id == term_id)
    rows = query.all()

    weighted_sum = 0.0
    weight_total = 0.0
    per_subject: dict[int, dict] = {}
    for grade, assessment in rows:
        max_score = assessment.max_score or 0
        if max_score <= 0:
            continue
        weight = assessment.weight or 1
        fraction = max(min(grade.score / max_score, 1.0), 0.0)
        weighted_sum += fraction * weight
        weight_total += weight
        bucket = per_subject.setdefault(assessment.subject_id, {"subject_id": assessment.subject_id, "weighted_sum": 0.0, "weight": 0.0})
        bucket["weighted_sum"] += fraction * weight
        bucket["weight"] += weight

    fraction = (weighted_sum / weight_total) if weight_total else 0.0
    subjects = [
        {
            "subject_id": bucket["subject_id"],
            "average_20": round((bucket["weighted_sum"] / bucket["weight"]) * 20, 2) if bucket["weight"] else 0.0,
        }
        for bucket in per_subject.values()
    ]
    return {
        "student_id": student_id,
        "term_id": term_id,
        "assessments_counted": len(rows),
        "percentage": round(fraction * 100, 2),
        "average_20": round(fraction * 20, 2),
        "gpa_4": round(fraction * 4, 2),
        "total_weight": weight_total,
        "subjects": subjects,
    }
