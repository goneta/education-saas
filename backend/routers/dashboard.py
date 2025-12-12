from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, Time
from typing import List, Dict, Any
from datetime import datetime, date
import calendar

from .. import models, schemas, database, auth, security

router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"]
)

@router.get("/stats", response_model=Dict[str, Any])
def get_dashboard_stats(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """
    Get statistics for the dashboard:
    - Total Students
    - Upcoming Classes (Today)
    - Recent Activities (New Users)
    """
    
    # 1. Total Students
    # Filter by school if applicable (multi-tenancy)
    # Assuming current_user.school_id is available for strict multi-tenancy
    # For now, we'll implement robustly assuming usage of current_user.school_id if set
    
    student_query = db.query(models.StudentProfile)
    if current_user.school_id:
         student_query = student_query.join(models.User).filter(models.User.school_id == current_user.school_id)
    
    total_students = student_query.count()

    # 2. Upcoming Classes Today
    # Get current day of week (Monday=0, Sunday=6)
    # Our DB Enum: MONDAY...SUNDAY
    # We need to map python datetime weekday to DB Enum
    
    today = date.today()
    day_name = today.strftime('%A').lower() # e.g. "thursday"
    
    # Map to Enum just to be safe, though lower string match should work with auto-conversion usually
    # But let's verify exact enum values in models.py: MONDAY = "monday"
    
    classes_query = db.query(models.Timetable).filter(models.Timetable.day_of_week == day_name)
    
    if current_user.school_id:
        classes_query = classes_query.join(models.Class).filter(models.Class.school_id == current_user.school_id)
        
    upcoming_classes_today = classes_query.count()

    # 3. Active Classes (Currently in Session)
    # Filter by: 
    # - Day of week = Today
    # - Start Time <= Current Time
    # - End Time >= Current Time
    
    current_time = datetime.now().time()
    
    active_classes_query = db.query(models.Timetable).filter(
        models.Timetable.day_of_week == day_name,
        models.Timetable.start_time <= current_time,
        models.Timetable.end_time >= current_time
    )
    
    if current_user.school_id:
        active_classes_query = active_classes_query.join(models.Class).filter(models.Class.school_id == current_user.school_id)
        
    active_classes_count = active_classes_query.count()

    # 4. Recent Activities
    # For now, we'll just track "New User Joined"
    users_query = db.query(models.User).order_by(models.User.created_at.desc())
    
    if current_user.school_id:
        users_query = users_query.filter(models.User.school_id == current_user.school_id)
        
    recent_users = users_query.limit(5).all()
    
    activities = []
    for user in recent_users:
        activities.append({
            "id": user.id,
            "description": f"New {user.role.value} joined: {user.full_name}",
            "time": user.created_at,
            "type": "registration"
        })
        
    return {
        "total_students": total_students,
        "upcoming_classes_today": upcoming_classes_today,
        "active_classes_count": active_classes_count,
        "recent_activities": activities
    }
