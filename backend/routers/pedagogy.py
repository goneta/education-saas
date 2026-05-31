from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import database, models, schemas, security

router = APIRouter(prefix="/pedagogy", tags=["Pedagogy & Portals"])


PEDAGOGY_MANAGERS = {
    models.UserRole.SCHOOL_ADMIN,
    models.UserRole.SUPER_ADMIN,
    models.UserRole.REGISTRAR,
    models.UserRole.DIRECTION,
    models.UserRole.TEACHER,
}

OFFICE_MANAGERS = {
    models.UserRole.SCHOOL_ADMIN,
    models.UserRole.SUPER_ADMIN,
    models.UserRole.REGISTRAR,
    models.UserRole.DIRECTION,
}


def _school_id(current_user: models.User) -> int:
    if not current_user.school_id:
        raise HTTPException(status_code=400, detail="School context is required")
    return current_user.school_id


def _student_profile_for_user(db: Session, current_user: models.User) -> Optional[models.StudentProfile]:
    if current_user.role == models.UserRole.STUDENT:
        return db.query(models.StudentProfile).filter(models.StudentProfile.user_id == current_user.id).first()
    return None


def _assert_student_access(student: models.StudentProfile, current_user: models.User, db: Session) -> None:
    if current_user.role in OFFICE_MANAGERS:
        if current_user.school_id and student.user.school_id != current_user.school_id:
            raise HTTPException(status_code=403, detail="Student belongs to another school")
        return
    if current_user.role == models.UserRole.STUDENT and student.user_id == current_user.id:
        return
    if current_user.role == models.UserRole.PARENT:
        link = db.query(models.ParentStudentLink).filter(
            models.ParentStudentLink.parent_user_id == current_user.id,
            models.ParentStudentLink.student_id == student.id,
            models.ParentStudentLink.is_active == True,
        ).first()
        if link:
            return
    raise HTTPException(status_code=403, detail="Not authorized for this student")


def _get_student(db: Session, student_id: int, current_user: models.User) -> models.StudentProfile:
    student = db.query(models.StudentProfile).filter(models.StudentProfile.id == student_id).first()
    if not student or not student.user:
        raise HTTPException(status_code=404, detail="Student not found")
    _assert_student_access(student, current_user, db)
    return student


@router.get("/materials", response_model=List[schemas.CourseMaterialResponse])
def list_materials(
    class_id: Optional[int] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    school_id = _school_id(current_user)
    query = db.query(models.CourseMaterial).filter(models.CourseMaterial.school_id == school_id)
    student = _student_profile_for_user(db, current_user)
    if student:
        query = query.filter(models.CourseMaterial.class_id == student.current_class_id)
    elif class_id:
        query = query.filter(models.CourseMaterial.class_id == class_id)
    return query.order_by(models.CourseMaterial.created_at.desc()).all()


@router.post("/materials", response_model=schemas.CourseMaterialResponse)
def create_material(
    material: schemas.CourseMaterialCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    if current_user.role not in PEDAGOGY_MANAGERS:
        raise HTTPException(status_code=403, detail="Not authorized")
    school_id = _school_id(current_user)
    cls = db.query(models.Class).filter(models.Class.id == material.class_id, models.Class.school_id == school_id).first()
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")
    row = models.CourseMaterial(**material.model_dump(), school_id=school_id, teacher_id=current_user.id)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("/assignments", response_model=List[schemas.AssignmentResponse])
def list_assignments(
    class_id: Optional[int] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    school_id = _school_id(current_user)
    query = db.query(models.Assignment).filter(models.Assignment.school_id == school_id)
    student = _student_profile_for_user(db, current_user)
    if student:
        query = query.filter(models.Assignment.class_id == student.current_class_id)
    elif class_id:
        query = query.filter(models.Assignment.class_id == class_id)
    return query.order_by(models.Assignment.created_at.desc()).all()


@router.post("/assignments", response_model=schemas.AssignmentResponse)
def create_assignment(
    assignment: schemas.AssignmentCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    if current_user.role not in PEDAGOGY_MANAGERS:
        raise HTTPException(status_code=403, detail="Not authorized")
    school_id = _school_id(current_user)
    cls = db.query(models.Class).filter(models.Class.id == assignment.class_id, models.Class.school_id == school_id).first()
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")
    row = models.Assignment(**assignment.model_dump(), school_id=school_id, teacher_id=current_user.id)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.post("/assignments/{assignment_id}/submissions", response_model=schemas.AssignmentSubmissionResponse)
def submit_assignment(
    assignment_id: int,
    submission: schemas.AssignmentSubmissionCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    student = _student_profile_for_user(db, current_user)
    if not student:
        raise HTTPException(status_code=403, detail="Only students can submit assignments")
    assignment = db.query(models.Assignment).filter(
        models.Assignment.id == assignment_id,
        models.Assignment.school_id == current_user.school_id,
        models.Assignment.class_id == student.current_class_id,
    ).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    row = models.AssignmentSubmission(
        assignment_id=assignment.id,
        student_id=student.id,
        **submission.model_dump(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("/assignments/{assignment_id}/submissions", response_model=List[schemas.AssignmentSubmissionResponse])
def list_submissions(
    assignment_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    assignment = db.query(models.Assignment).filter(models.Assignment.id == assignment_id).first()
    if not assignment or assignment.school_id != current_user.school_id:
        raise HTTPException(status_code=404, detail="Assignment not found")
    if current_user.role not in PEDAGOGY_MANAGERS:
        student = _student_profile_for_user(db, current_user)
        if not student:
            raise HTTPException(status_code=403, detail="Not authorized")
        return db.query(models.AssignmentSubmission).filter(
            models.AssignmentSubmission.assignment_id == assignment_id,
            models.AssignmentSubmission.student_id == student.id,
        ).all()
    return db.query(models.AssignmentSubmission).filter(models.AssignmentSubmission.assignment_id == assignment_id).all()


@router.put("/submissions/{submission_id}/grade", response_model=schemas.AssignmentSubmissionResponse)
def grade_submission(
    submission_id: int,
    grade: schemas.AssignmentSubmissionGrade,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    if current_user.role not in PEDAGOGY_MANAGERS:
        raise HTTPException(status_code=403, detail="Not authorized")
    submission = db.query(models.AssignmentSubmission).join(models.Assignment).filter(
        models.AssignmentSubmission.id == submission_id,
        models.Assignment.school_id == current_user.school_id,
    ).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    submission.score = grade.score
    submission.feedback = grade.feedback
    submission.status = models.SubmissionStatus.GRADED
    submission.graded_at = datetime.utcnow()
    db.commit()
    db.refresh(submission)
    return submission


@router.post("/parent-links", response_model=schemas.ParentStudentLinkResponse)
def create_parent_link(
    link: schemas.ParentStudentLinkCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    if current_user.role not in OFFICE_MANAGERS:
        raise HTTPException(status_code=403, detail="Not authorized")
    parent = db.query(models.User).filter(
        models.User.id == link.parent_user_id,
        models.User.school_id == current_user.school_id,
        models.User.role == models.UserRole.PARENT,
    ).first()
    student = db.query(models.StudentProfile).join(models.User).filter(
        models.StudentProfile.id == link.student_id,
        models.User.school_id == current_user.school_id,
    ).first()
    if not parent or not student:
        raise HTTPException(status_code=404, detail="Parent or student not found")
    row = models.ParentStudentLink(
        parent_user_id=link.parent_user_id,
        student_id=link.student_id,
        relation=link.relationship,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("/portal/children")
def list_portal_children(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    if current_user.role == models.UserRole.STUDENT:
        student = _student_profile_for_user(db, current_user)
        return [_serialize_student(student)] if student else []
    if current_user.role != models.UserRole.PARENT:
        raise HTTPException(status_code=403, detail="Parent or student portal only")
    links = db.query(models.ParentStudentLink).filter(
        models.ParentStudentLink.parent_user_id == current_user.id,
        models.ParentStudentLink.is_active == True,
    ).all()
    return [_serialize_student(link.student) for link in links]


def _serialize_student(student: models.StudentProfile):
    return {
        "id": student.id,
        "registration_number": student.registration_number,
        "current_class_id": student.current_class_id,
        "parent_name": student.parent_name,
        "parent_phone": student.parent_phone,
        "user": {
            "id": student.user.id if student.user else None,
            "full_name": student.user.full_name if student.user else None,
            "email": student.user.email if student.user else None,
        },
    }


@router.get("/requests", response_model=List[schemas.AdministrativeRequestResponse])
def list_requests(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    query = db.query(models.AdministrativeRequest)
    if current_user.role in PEDAGOGY_MANAGERS:
        query = query.filter(models.AdministrativeRequest.school_id == current_user.school_id)
    elif current_user.role == models.UserRole.STUDENT:
        student = _student_profile_for_user(db, current_user)
        query = query.filter(models.AdministrativeRequest.student_id == student.id)
    elif current_user.role == models.UserRole.PARENT:
        student_ids = [
            link.student_id for link in db.query(models.ParentStudentLink).filter(
                models.ParentStudentLink.parent_user_id == current_user.id,
                models.ParentStudentLink.is_active == True,
            ).all()
        ]
        query = query.filter(models.AdministrativeRequest.student_id.in_(student_ids or [-1]))
    else:
        raise HTTPException(status_code=403, detail="Not authorized")
    return query.order_by(models.AdministrativeRequest.created_at.desc()).all()


@router.post("/requests", response_model=schemas.AdministrativeRequestResponse)
def create_request(
    request: schemas.AdministrativeRequestCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    student = _get_student(db, request.student_id, current_user)
    row = models.AdministrativeRequest(
        **request.model_dump(),
        school_id=student.user.school_id,
        requested_by_id=current_user.id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.put("/requests/{request_id}", response_model=schemas.AdministrativeRequestResponse)
def update_request(
    request_id: int,
    request_update: schemas.AdministrativeRequestUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user),
):
    if current_user.role not in OFFICE_MANAGERS:
        raise HTTPException(status_code=403, detail="Not authorized")
    row = db.query(models.AdministrativeRequest).filter(
        models.AdministrativeRequest.id == request_id,
        models.AdministrativeRequest.school_id == current_user.school_id,
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="Request not found")
    row.status = request_update.status
    row.response = request_update.response
    row.handled_by_id = current_user.id
    row.handled_at = datetime.utcnow()
    db.commit()
    db.refresh(row)
    return row


@router.get("/internships", response_model=List[schemas.InternshipResponse])
def list_internships(db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    return db.query(models.Internship).filter(models.Internship.school_id == _school_id(current_user)).order_by(models.Internship.created_at.desc()).all()


@router.post("/internships", response_model=schemas.InternshipResponse)
def create_internship(internship: schemas.InternshipCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    if current_user.role not in OFFICE_MANAGERS:
        raise HTTPException(status_code=403, detail="Not authorized")
    student = _get_student(db, internship.student_id, current_user)
    row = models.Internship(**internship.model_dump(), school_id=student.user.school_id, created_by_id=current_user.id)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.post("/school-exits", response_model=schemas.SchoolExitResponse)
def create_school_exit(exit_in: schemas.SchoolExitCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    if current_user.role not in OFFICE_MANAGERS:
        raise HTTPException(status_code=403, detail="Not authorized")
    student = _get_student(db, exit_in.student_id, current_user)
    row = models.SchoolExit(**exit_in.model_dump(), school_id=student.user.school_id, created_by_id=current_user.id)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.post("/orientations", response_model=schemas.StudentOrientationResponse)
def create_orientation(orientation: schemas.StudentOrientationCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(security.get_current_user)):
    if current_user.role not in OFFICE_MANAGERS:
        raise HTTPException(status_code=403, detail="Not authorized")
    student = _get_student(db, orientation.student_id, current_user)
    row = models.StudentOrientation(**orientation.model_dump(), school_id=student.user.school_id, created_by_id=current_user.id)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
