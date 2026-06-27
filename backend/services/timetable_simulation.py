"""Explainable AI and what-if simulation for timetables.

`explain_candidate` turns an optimiser candidate's score breakdown into plain
statements (explainable AI). `simulate` re-runs the optimiser under a modified
scenario (teacher absent, extra working day) and reports the impact versus the
baseline so admins can answer "what happens if…" questions.
"""

from typing import Any, Optional

from sqlalchemy.orm import Session

from . import timetable_optimizer


def explain_candidate(candidate) -> list[str]:
    b = candidate.breakdown or {}
    placed = b.get("placed_sessions", 0)
    required = b.get("required_sessions", 0)
    fill = b.get("fill_rate", 0)
    statements = [f"Score de qualité: {candidate.score}/100."]
    statements.append(f"{placed}/{required} séances placées ({round(fill * 100)}% de remplissage).")
    if b.get("soft_penalty"):
        statements.append(f"{b['soft_penalty']} pénalité(s) de règle souple appliquée(s) (créneaux non idéaux).")
    else:
        statements.append("Aucune règle souple enfreinte.")
    if b.get("unplaced"):
        statements.append(f"{b['unplaced']} séance(s) n'ont pas pu être placées sans conflit.")
    return statements


def _best(candidates) -> Optional[Any]:
    return candidates[0] if candidates else None


def _summary(candidate) -> dict:
    if not candidate:
        return {"score": 0, "placed_sessions": 0, "required_sessions": 0, "unplaced": 0}
    b = candidate.breakdown or {}
    return {
        "score": candidate.score,
        "placed_sessions": b.get("placed_sessions", 0),
        "required_sessions": b.get("required_sessions", 0),
        "unplaced": b.get("unplaced", 0),
    }


def simulate(db: Session, school_id: int, scenario: str, params: Optional[dict] = None) -> dict:
    """Run a what-if scenario and compare to the baseline.

    Scenarios: 'teacher_absent' {teacher_id}, 'extra_working_day' {day}.
    """
    params = params or {}
    baseline = _best(timetable_optimizer.generate_candidates(db, school_id, candidate_count=1))

    if scenario == "teacher_absent":
        teacher_id = params.get("teacher_id")
        if not teacher_id:
            return {"error": "teacher_id is required"}
        variant = _best(timetable_optimizer.generate_candidates(db, school_id, candidate_count=1, exclude_teacher_ids={teacher_id}))
    elif scenario == "extra_working_day":
        day = str(params.get("day", "saturday")).lower()
        variant = _best(timetable_optimizer.generate_candidates(db, school_id, candidate_count=1, extra_days=[day]))
    else:
        return {"error": f"Unknown scenario: {scenario}"}

    base_summary = _summary(baseline)
    var_summary = _summary(variant)
    score_delta = round(var_summary["score"] - base_summary["score"], 2)
    unplaced_delta = var_summary["unplaced"] - base_summary["unplaced"]

    impact = []
    if scenario == "teacher_absent":
        if unplaced_delta > 0:
            impact.append(f"L'absence laisse {unplaced_delta} séance(s) supplémentaire(s) non couverte(s) ; des remplacements sont nécessaires.")
        else:
            impact.append("L'absence peut être absorbée sans séance non couverte supplémentaire.")
    elif scenario == "extra_working_day":
        if score_delta > 0 or unplaced_delta < 0:
            impact.append("Ouvrir ce jour améliore le remplissage / réduit les séances non placées.")
        else:
            impact.append("Ouvrir ce jour n'améliore pas significativement l'emploi du temps.")

    return {
        "scenario": scenario,
        "params": params,
        "baseline": base_summary,
        "scenario_result": var_summary,
        "score_delta": score_delta,
        "unplaced_delta": unplaced_delta,
        "impact": impact,
        "explanation": explain_candidate(variant) if variant else [],
    }
