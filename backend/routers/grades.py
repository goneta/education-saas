from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from .. import models, schemas, security, database
from ..services import automation

router = APIRouter(prefix="/grades", tags=["Grades & Evaluations"])

# ---------------------------------------------------------
# Assessments Endpoints
# ---------------------------------------------------------

@router.post("/assessments", response_model=schemas.AssessmentResponse)
def create_assessment(
    assessment_in: schemas.AssessmentCreate,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db)
):
    # Only Teachers and Admins can create assessments
    if current_user.role not in [models.UserRole.SCHOOL_ADMIN, models.UserRole.SUPER_ADMIN, models.UserRole.TEACHER]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Verify Class and Subject exist and belong to school (if scoped)
    # Simplified check:
    # If teacher, ideally verify they teach this class/subject
    
    new_assessment = models.Assessment(**assessment_in.model_dump())
    db.add(new_assessment)
    db.commit()
    db.refresh(new_assessment)
    return new_assessment

@router.get("/assessments", response_model=List[schemas.AssessmentResponse])
def list_assessments(
    class_id: Optional[int] = None,
    subject_id: Optional[int] = None,
    term_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db)
):
    query = db.query(models.Assessment)
    
    # Filter by school via Class relationship
    query = query.join(models.Class)
    if current_user.school_id:
        query = query.filter(models.Class.school_id == current_user.school_id)
        
    if class_id:
        query = query.filter(models.Assessment.class_id == class_id)
    if subject_id:
        query = query.filter(models.Assessment.subject_id == subject_id)
    if term_id:
        query = query.filter(models.Assessment.term_id == term_id)
        
    return query.offset(skip).limit(limit).all()

@router.get("/assessments/{assessment_id}", response_model=schemas.AssessmentResponse)
def get_assessment(
    assessment_id: int,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db)
):
    assessment = db.query(models.Assessment).filter(models.Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
        
    # Security check: Ensure assessment belongs to user's school
    # (Assuming assessment -> class -> school relationship)
    if current_user.school_id:
        # Check via join if strict scoping needed, or rely on ID obscurity + auth
        pass 
        
    return assessment

@router.put("/assessments/{assessment_id}", response_model=schemas.AssessmentResponse)
def update_assessment(
    assessment_id: int,
    assessment_in: schemas.AssessmentCreate,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db)
):
    if current_user.role not in [models.UserRole.SCHOOL_ADMIN, models.UserRole.SUPER_ADMIN, models.UserRole.TEACHER]:
        raise HTTPException(status_code=403, detail="Not authorized")

    assessment = db.query(models.Assessment).filter(models.Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    # Update fields
    for key, value in assessment_in.model_dump().items():
        setattr(assessment, key, value)

    db.commit()
    db.refresh(assessment)
    return assessment

@router.delete("/assessments/{assessment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_assessment(
    assessment_id: int,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db)
):
    if current_user.role not in [models.UserRole.SCHOOL_ADMIN, models.UserRole.SUPER_ADMIN, models.UserRole.TEACHER]:
        raise HTTPException(status_code=403, detail="Not authorized")

    assessment = db.query(models.Assessment).filter(models.Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    db.delete(assessment)
    db.commit()

# ---------------------------------------------------------
# Grades Endpoints
# ---------------------------------------------------------

@router.post("/entry/bulk", status_code=status.HTTP_200_OK)
def enter_grades_bulk(
    bulk_in: schemas.GradeBulkCreate,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db)
):
    if current_user.role not in [models.UserRole.SCHOOL_ADMIN, models.UserRole.SUPER_ADMIN, models.UserRole.TEACHER]:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    assessment = db.query(models.Assessment).filter(models.Assessment.id == bulk_in.assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
        
    # Process each grade
    count = 0
    touched_students = set()
    for g in bulk_in.grades:
        # Check existing
        existing = db.query(models.Grade).filter(
            models.Grade.assessment_id == bulk_in.assessment_id,
            models.Grade.student_id == g.student_id
        ).first()
        
        if existing:
            existing.score = g.score
            existing.comment = g.comment
        else:
            new_grade = models.Grade(
                assessment_id=bulk_in.assessment_id,
                student_id=g.student_id,
                score=g.score,
                comment=g.comment
            )
            db.add(new_grade)
        touched_students.add(g.student_id)
        count += 1
    school_id = assessment.current_class.school_id if assessment.current_class else current_user.school_id
    if school_id:
        for student_id in touched_students:
            automation.automate_report_card(db, student_id, assessment.term_id, school_id, current_user)
    db.commit()
    return {"message": f"Successfully processed {count} grades"}

@router.get("/assessments/{assessment_id}/grades", response_model=List[schemas.GradeResponse])
def get_assessment_grades(
    assessment_id: int,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db)
):
    # Determine authorization (Teacher of class or Admin)
    assessment = db.query(models.Assessment).filter(models.Assessment.id == assessment_id).first()
    if not assessment:
         raise HTTPException(status_code=404, detail="Assessment not found")
         
    grades = db.query(models.Grade).filter(models.Grade.assessment_id == assessment_id).all()
    return grades

@router.get("/reports/student/{student_id}/term/{term_id}", response_model=schemas.ReportCardResponse)
def get_report_card(
    student_id: int,
    term_id: int,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db)
):
    # Fetch all grades for this student in this term
    # Join Assessment to filter by term, and Subject for info
    grades = db.query(models.Grade).join(models.Assessment).filter(
        models.Grade.student_id == student_id,
        models.Assessment.term_id == term_id
    ).options(joinedload(models.Grade.assessment).joinedload(models.Assessment.subject)).all()
    
    # Check permissions (Student themselves, Parent, Teacher, Admin)
    # Skipping strict check for MVP velocity, but ideally check user.id or role.

    # Group by Subject
    subjects_map = {}
    for grade in grades:
        sub_id = grade.assessment.subject_id
        if sub_id not in subjects_map:
            subjects_map[sub_id] = {
                "subject": grade.assessment.subject,
                "grades": [],
                "total_weighted_normalized_score": 0,
                "total_weight": 0
            }
        
        # Normalize to 20
        max_score = grade.assessment.max_score or 20
        normalized_score = (grade.score / max_score) * 20
        weight = grade.assessment.weight or 1
        
        # Add to report assessments list
        subjects_map[sub_id]["grades"].append(schemas.ReportAssessment(
            assessment=grade.assessment.title,
            score=grade.score,
            max=max_score,
            weight=weight
        ))
        
        subjects_map[sub_id]["total_weighted_normalized_score"] += normalized_score * weight
        subjects_map[sub_id]["total_weight"] += weight

    # Build Report
    report_subjects = []
    total_coeff_score = 0
    total_coeff = 0
    
    for sub_id, data in subjects_map.items():
        subject_avg = 0
        if data["total_weight"] > 0:
            subject_avg = data["total_weighted_normalized_score"] / data["total_weight"]
            
        coeff = data["subject"].coefficient or 1
        total_coeff_score += subject_avg * coeff
        total_coeff += coeff
        
        report_subjects.append(schemas.ReportSubject(
            subject_id=sub_id,
            subject_name=data["subject"].name,
            coefficient=coeff,
            average=round(subject_avg, 2),
            assessments=data["grades"]
        ))
        
    overall_avg = 0
    if total_coeff > 0:
        overall_avg = total_coeff_score / total_coeff
        
    return schemas.ReportCardResponse(
        student_id=student_id,
        term_id=term_id,
        subjects=report_subjects,
        overall_average=round(overall_avg, 2)
    )
