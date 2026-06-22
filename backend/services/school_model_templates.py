from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from .. import models


MODEL_TEMPLATES = {
    "PRIMARY": {
        "classes": ["CP1", "CP2", "CE1", "CE2", "CM1", "CM2"],
        "subjects": ["Francais", "Mathematiques", "Sciences", "Histoire-Geographie", "Education civique"],
        "programs": [],
        "periods": ["Trimestre 1", "Trimestre 2", "Trimestre 3"],
        "diplomas": ["Certificat de fin de cycle primaire"],
        "certifications": ["Passage en classe superieure", "Assiduite"],
        "assessments": ["Devoir", "Composition", "Lecture", "Evaluation continue"],
        "fees": ["Inscription", "Scolarite", "Assurance"],
    },
    "GENERAL_SECONDARY": {
        "classes": ["6eme", "5eme", "4eme", "3eme", "2nde", "1ere", "Terminale"],
        "subjects": ["Francais", "Mathematiques", "Physique-Chimie", "SVT", "Anglais", "Histoire-Geographie", "Philosophie"],
        "programs": [],
        "periods": ["Trimestre 1", "Trimestre 2", "Trimestre 3"],
        "diplomas": ["BEPC", "Baccalaureat"],
        "certifications": ["BEPC", "Baccalaureat", "Attestation de scolarite"],
        "assessments": ["Interrogation", "Devoir surveille", "Composition", "Examen blanc"],
        "fees": ["Inscription", "Scolarite", "Assurance", "Examens"],
    },
    "VOCATIONAL": {
        "classes": ["CAP 1", "CAP 2", "BEP 1", "BEP 2"],
        "subjects": ["Pratique professionnelle", "Technologie", "Entrepreneuriat", "Francais professionnel"],
        "programs": ["Cuisine", "Mecanique"],
        "periods": ["Session 1", "Session 2"],
        "diplomas": ["CAP", "BEP", "Certificat professionnel"],
        "certifications": ["Competence metier", "Attestation de stage", "Certification pratique"],
        "assessments": ["Evaluation pratique", "Competence", "Projet", "Examen final"],
        "fees": ["Inscription", "Scolarite", "Equipement"],
    },
    "TECHNICAL": {
        "classes": ["2nde Technique", "1ere Technique", "Terminale Technique", "BTS 1", "BTS 2"],
        "subjects": ["Mathematiques appliquees", "Technologie", "Atelier", "Gestion", "Anglais technique"],
        "programs": ["Electrotechnique", "Maintenance industrielle"],
        "periods": ["Semestre 1", "Semestre 2", "Semestre 3", "Semestre 4"],
        "diplomas": ["BT", "BTS", "Certificat technique"],
        "certifications": ["Certification atelier", "Attestation de stage", "BTS"],
        "assessments": ["Controle continu", "Pratique atelier", "Rapport de stage", "Examen final"],
        "fees": ["Inscription", "Scolarite", "Atelier", "Assurance"],
    },
    "PROFESSIONAL": {
        "classes": ["CAP 1", "CAP 2", "BTS Pro 1", "BTS Pro 2"],
        "subjects": ["Pratique professionnelle", "Gestion de projet", "Stage", "Communication professionnelle"],
        "programs": ["Commerce", "Informatique de gestion"],
        "periods": ["Session 1", "Session 2", "Session 3", "Session 4"],
        "diplomas": ["CAP", "BTS Pro", "Certificat professionnel"],
        "certifications": ["Certification metier", "Attestation de stage", "Certification pratique"],
        "assessments": ["Evaluation pratique", "Competence", "Projet", "Rapport de stage"],
        "fees": ["Inscription", "Scolarite", "Stage"],
    },
    "UNIVERSITY": {
        "classes": ["Licence 1", "Licence 2", "Licence 3", "Master 1", "Master 2"],
        "subjects": ["Methodologie", "Anglais", "Informatique", "Projet tutore"],
        "programs": ["Licence Gestion", "Master Management"],
        "periods": [f"Semestre {index}" for index in range(1, 7)],
        "diplomas": ["Licence", "Master", "Doctorat"],
        "certifications": ["Releve certifie", "Diplome certifie", "Attestation ECTS"],
        "assessments": ["Controle continu", "Partiel", "Examen final", "Memoire", "Soutenance"],
        "fees": ["Inscription", "Credits pedagogiques", "Bibliotheque"],
    },
}

SCHOOL_TYPE_TO_MODEL = {
    "primary": "PRIMARY",
    "secondary": "GENERAL_SECONDARY",
    "general": "GENERAL_SECONDARY",
    "vocational": "VOCATIONAL",
    "technical": "TECHNICAL",
    "professional": "PROFESSIONAL",
    "university": "UNIVERSITY",
}

MODEL_NAMES = {
    "PRIMARY": "Primaire",
    "GENERAL_SECONDARY": "General / Secondaire",
    "VOCATIONAL": "Vocationnel",
    "TECHNICAL": "Technique",
    "PROFESSIONAL": "Professionnel",
    "UNIVERSITY": "Universitaire",
}


def ensure_school_foundation(
    db: Session,
    school: models.School,
    *,
    owner_user_id: int | None = None,
    model_codes: list[str] | None = None,
    seed_defaults: bool = True,
) -> tuple[models.Organization, list[models.SchoolModelAssignment], dict[str, dict[str, int]]]:
    organization = school.organization
    if not organization:
        organization = models.Organization(
            name=school.name,
            legal_name=school.name,
            phone=school.phone,
            email=school.email,
            address=school.formatted_address or school.address,
            country=school.country_code or "CI",
            currency=school.currency_code or "XOF",
            timezone=school.timezone or "Africa/Abidjan",
            owner_user_id=owner_user_id,
            subscription_plan=school.subscription_plan or "free",
        )
        db.add(organization)
        db.flush()
        school.organization_id = organization.id
    elif owner_user_id and not organization.owner_user_id:
        organization.owner_user_id = owner_user_id

    selected_codes = model_codes or [
        SCHOOL_TYPE_TO_MODEL.get(getattr(school.school_type, "value", str(school.school_type)).lower(), "GENERAL_SECONDARY")
    ]
    assignments: list[models.SchoolModelAssignment] = []
    seeded: dict[str, dict[str, int]] = {}
    for raw_code in selected_codes:
        code = raw_code.upper()
        if code not in MODEL_TEMPLATES:
            continue
        school_model = db.query(models.SchoolModel).filter(models.SchoolModel.code == code).first()
        if not school_model:
            school_model = models.SchoolModel(
                code=code,
                name=MODEL_NAMES[code],
                description=f"Modele systeme {MODEL_NAMES[code]}",
                is_system_template=True,
                is_active=True,
            )
            db.add(school_model)
            db.flush()
        assignment = db.query(models.SchoolModelAssignment).filter(
            models.SchoolModelAssignment.school_id == school.id,
            models.SchoolModelAssignment.school_model_id == school_model.id,
        ).first()
        if not assignment:
            assignment = models.SchoolModelAssignment(
                school_id=school.id,
                school_model_id=school_model.id,
                display_name=school_model.name,
                is_active=True,
            )
            db.add(assignment)
            db.flush()
        assignments.append(assignment)
        if seed_defaults:
            seeded[code] = seed_assignment_defaults(db, assignment)
    return organization, assignments, seeded


def seed_assignment_defaults(db: Session, assignment: models.SchoolModelAssignment) -> dict[str, int]:
    code = assignment.school_model.code
    template = MODEL_TEMPLATES.get(code)
    if not template:
        return {}
    school_id = assignment.school_id
    created = {"academic_years": 0, "classes": 0, "subjects": 0, "programs": 0, "fees": 0, "reference_data": 0}
    now = datetime.utcnow()
    year_name = f"{now.year}-{now.year + 1}"
    year = db.query(models.AcademicYear).filter(
        models.AcademicYear.school_id == school_id,
        models.AcademicYear.school_model_assignment_id == assignment.id,
        models.AcademicYear.name == year_name,
    ).first()
    if not year:
        year = models.AcademicYear(
            name=year_name,
            start_date=datetime(now.year, 9, 1),
            end_date=datetime(now.year + 1, 7, 31),
            is_current=True,
            school_id=school_id,
            school_model_assignment_id=assignment.id,
        )
        db.add(year)
        db.flush()
        created["academic_years"] += 1

    for class_name in template["classes"]:
        if not db.query(models.Class.id).filter(
            models.Class.school_id == school_id,
            models.Class.school_model_assignment_id == assignment.id,
            models.Class.name == class_name,
        ).first():
            db.add(models.Class(
                name=class_name,
                level=class_name,
                school_id=school_id,
                school_model_assignment_id=assignment.id,
                is_system_default=True,
            ))
            created["classes"] += 1

    for subject_name in template["subjects"]:
        if not db.query(models.Subject.id).filter(
            models.Subject.school_id == school_id,
            models.Subject.school_model_assignment_id == assignment.id,
            models.Subject.name == subject_name,
        ).first():
            db.add(models.Subject(
                name=subject_name,
                code=subject_name.upper().replace(" ", "_")[:24],
                school_id=school_id,
                school_model_assignment_id=assignment.id,
                is_system_default=True,
            ))
            created["subjects"] += 1

    for program_name in template["programs"]:
        if not db.query(models.AcademicProgram.id).filter(
            models.AcademicProgram.school_id == school_id,
            models.AcademicProgram.school_model_assignment_id == assignment.id,
            models.AcademicProgram.name == program_name,
        ).first():
            db.add(models.AcademicProgram(
                name=program_name,
                sector=code.lower(),
                school_id=school_id,
                school_model_assignment_id=assignment.id,
                is_system_default=True,
            ))
            created["programs"] += 1

    for order, fee_name in enumerate(template["fees"], start=1):
        if not db.query(models.FeeSchedule.id).filter(
            models.FeeSchedule.school_id == school_id,
            models.FeeSchedule.school_model_assignment_id == assignment.id,
            models.FeeSchedule.name == fee_name,
            models.FeeSchedule.academic_year_id == year.id,
        ).first():
            db.add(models.FeeSchedule(
                name=fee_name,
                amount=0,
                category_order=order,
                is_required=True,
                is_current=True,
                is_system_default=True,
                academic_year_id=year.id,
                school_id=school_id,
                school_model_assignment_id=assignment.id,
            ))
            created["fees"] += 1

    reference_groups = {
        "periods": template["periods"],
        "diplomas": template["diplomas"],
        "certifications": template["certifications"],
        "assessment_types": template["assessments"],
    }
    for category, values in reference_groups.items():
        for order, value in enumerate(values, start=1):
            key = f"{assignment.id}_{value.lower().replace(' ', '_').replace('-', '_')}"
            if not db.query(models.ReferenceData.id).filter(
                models.ReferenceData.school_id == school_id,
                models.ReferenceData.category == category,
                models.ReferenceData.key == key,
            ).first():
                db.add(models.ReferenceData(
                    category=category,
                    key=key,
                    value={"fr": value, "en": value, "es": value, "sw": value},
                    order=order,
                    school_id=school_id,
                ))
                created["reference_data"] += 1
    db.flush()
    return created
