from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime
from .. import models, schemas, security, database
from ..services import school_context, student_lifecycle

router = APIRouter(prefix="/attendance", tags=["Attendance"])

@router.post("/batch", response_model=List[schemas.AttendanceResponse])
def batch_update_attendance(
    batch_data: schemas.AttendanceBatchUpdate,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db)
):
    if current_user.role not in [models.UserRole.SCHOOL_ADMIN, models.UserRole.SUPER_ADMIN, models.UserRole.TEACHER]:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Validate Timetable and Class/School
    timetable = db.query(models.Timetable).join(models.Class).filter(
        models.Timetable.id == batch_data.timetable_id,
        models.Class.school_id == current_user.school_id
    ).first()
    
    if not timetable:
         raise HTTPException(status_code=404, detail="Timetable not found or access denied")

    active_context = school_context.resolve_context(db, current_user)
    student_lifecycle.ensure_academic_year_is_editable(
        db,
        current_user=current_user,
        school_id=active_context.school_id,
        academic_year_id=active_context.academic_year_id,
        school_model_assignment_id=active_context.school_model_assignment_id,
        resource_type="attendance",
    )
    updated_records = []
    
    for student_update in batch_data.students:
        enrollment = student_lifecycle.active_enrollment_for_student_profile_id(
            db,
            student_update.student_id,
            school_id=active_context.school_id,
            school_model_assignment_id=active_context.school_model_assignment_id,
            academic_year_id=active_context.academic_year_id,
        )
        if not enrollment:
            raise HTTPException(status_code=403, detail="Eleve hors du contexte d'inscription actif.")
        student_profile_id = enrollment.student_global_profile.student_profile_id
        # Check if record exists
        attendance_record = db.query(models.Attendance).filter(
            models.Attendance.timetable_id == batch_data.timetable_id,
            models.Attendance.date == batch_data.date,
            models.Attendance.student_id == student_profile_id
        ).first()
        
        if attendance_record:
            # Update existing
            attendance_record.status = student_update.status
            attendance_record.remarks = student_update.remarks
            attendance_record.recorded_by_id = current_user.id
            attendance_record.updated_at = func.now()
        else:
            # Create new
            attendance_record = models.Attendance(
                date=batch_data.date,
                status=student_update.status,
                remarks=student_update.remarks,
                student_id=student_profile_id,
                student_enrollment_id=enrollment.id,
                timetable_id=batch_data.timetable_id,
                recorded_by_id=current_user.id
            )
            db.add(attendance_record)
            
        updated_records.append(attendance_record)

    db.commit()
    
    # Refresh all
    for record in updated_records:
        db.refresh(record)
        
    return updated_records

@router.get("/", response_model=List[schemas.AttendanceResponse])
def get_attendance(
    timetable_id: Optional[int] = None,
    class_id: Optional[int] = None,
    date: Optional[datetime] = None,
    student_id: Optional[int] = None,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db)
):
    if not current_user.school_id:
        raise HTTPException(status_code=400, detail="User not part of a school")
        
    query = db.query(models.Attendance).join(models.Timetable).join(models.Class).filter(
        models.Class.school_id == current_user.school_id
    )
    
    if timetable_id:
        query = query.filter(models.Attendance.timetable_id == timetable_id)
    if class_id:
         query = query.filter(models.Timetable.class_id == class_id)
    if date:
        query = query.filter(models.Attendance.date == date)
    if student_id:
        query = query.filter(models.Attendance.student_id == student_id)
        
    return query.all()

@router.get("/stats", response_model=schemas.AttendanceStats)
def get_attendance_stats(
    class_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(database.get_db)
):
    if not current_user.school_id:
        raise HTTPException(status_code=400, detail="User not part of a school")

    # Base query
    query = db.query(models.Attendance).join(models.Timetable).join(models.Class).filter(
        models.Class.school_id == current_user.school_id,
        models.Timetable.class_id == class_id
    )
    
    if start_date:
        query = query.filter(models.Attendance.date >= start_date)
    if end_date:
        query = query.filter(models.Attendance.date <= end_date)
        
    total = query.count()
    present = query.filter(models.Attendance.status == models.AttendanceStatus.PRESENT).count()
    absent = query.filter(models.Attendance.status == models.AttendanceStatus.ABSENT).count()
    late = query.filter(models.Attendance.status == models.AttendanceStatus.LATE).count()
    excused = query.filter(models.Attendance.status == models.AttendanceStatus.EXCUSED).count()
    
    return schemas.AttendanceStats(
        total=total,
        present=present,
        absent=absent,
        late=late,
        excused=excused
    )
