from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from datetime import datetime, timedelta
from app.models.user import User, ShiftSchedule
from app.schemas.employee import EmployeeResponse
from typing import List, Optional

class ShiftScheduleService:
    """Service for managing shift schedules"""
    
    @staticmethod
    def get_weekly_schedule(
        db: Session, 
        week_start_date: datetime,
        search: Optional[str] = None,
        campaign: Optional[str] = None,
        shift: Optional[str] = None
    ) -> List[dict]:
        """
        Get shift schedules for a week
        
        Args:
            db: Database session
            week_start_date: Start date of the week (Monday)
            search: Search term for employee name/number
            campaign: Filter by campaign
            shift: Filter by shift time
            
        Returns:
            List of schedules with employee details and daily shifts
        """
        # Calculate week end date (Sunday)
        week_end_date = week_start_date + timedelta(days=6)
        
        # Query employees
        query = db.query(User).filter(User.is_active == True)
        
        if search:
            query = query.filter(or_(
                User.full_name.ilike(f"%{search}%"),
                User.employee_no.ilike(f"%{search}%")
            ))
        
        employees = query.order_by(User.full_name).all()
        
        # Get schedules for each employee
        schedules = []
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        for employee in employees:
            # Get schedules for this employee for the week
            week_schedules = db.query(ShiftSchedule).filter(and_(
                ShiftSchedule.user_id == employee.id,
                ShiftSchedule.schedule_date >= week_start_date,
                ShiftSchedule.schedule_date <= week_end_date
            )).all()
            
            # Build daily schedule
            daily_shifts = {}
            for i, day_name in enumerate(day_names):
                day_date = week_start_date + timedelta(days=i)
                
                # Find schedule for this day
                day_schedule = next((s for s in week_schedules if s.schedule_date.date() == day_date.date()), None)
                
                # Apply filters
                if day_schedule:
                    if campaign and day_schedule.campaign != campaign:
                        daily_shifts[day_name] = None
                        continue
                    if shift and day_schedule.shift_time != shift:
                        daily_shifts[day_name] = None
                        continue
                    daily_shifts[day_name] = day_schedule.shift_time
                else:
                    daily_shifts[day_name] = None
            
            schedules.append({
                'employee_id': employee.id,
                'employee_name': employee.full_name,
                'employee_no': employee.employee_no,
                'campaign': employee.campaign if hasattr(employee, 'campaign') else 'N/A',
                'schedules': daily_shifts
            })
        
        return schedules
    
    @staticmethod
    def save_shift(
        db: Session,
        user_id: int,
        schedule_date: datetime,
        shift_time: str,
        campaign: str,
        notes: Optional[str] = None
    ) -> ShiftSchedule:
        """Save or update a shift schedule"""
        
        # Check if schedule exists for this date
        existing = db.query(ShiftSchedule).filter(and_(
            ShiftSchedule.user_id == user_id,
            ShiftSchedule.schedule_date == schedule_date.date()
        )).first()
        
        if existing:
            existing.shift_time = shift_time
            existing.campaign = campaign
            existing.notes = notes
            existing.updated_at = datetime.utcnow()
        else:
            day_of_week = schedule_date.strftime('%A')
            shift_start, shift_end = ShiftScheduleService._parse_shift_time(shift_time)
            
            existing = ShiftSchedule(
                user_id=user_id,
                schedule_date=schedule_date.date(),
                day_of_week=day_of_week,
                shift_time=shift_time,
                shift_start=shift_start,
                shift_end=shift_end,
                campaign=campaign,
                notes=notes,
                is_published=False
            )
            db.add(existing)
        
        db.commit()
        db.refresh(existing)
        return existing
    
    @staticmethod
    def _parse_shift_time(shift_time: str) -> tuple:
        """
        Parse shift time string to start and end times
        
        Args:
            shift_time: e.g., "9am to 5pm", "11pm to 7am"
            
        Returns:
            Tuple of (shift_start, shift_end) as time objects
        """
        try:
            parts = shift_time.split(' to ')
            if len(parts) == 2:
                start_str = parts[0].strip().lower()
                end_str = parts[1].strip().lower()
                
                # Parse time strings (simple format: 9am, 11pm, 12pm, etc.)
                def parse_time(time_str):
                    time_str = time_str.replace('am', '').replace('pm', '').strip()
                    is_pm = 'pm' in time_str.lower()
                    hour = int(time_str.split(':')[0])
                    
                    if is_pm and hour != 12:
                        hour += 12
                    elif not is_pm and hour == 12:
                        hour = 0
                    
                    return hour
                
                start_hour = parse_time(start_str)
                end_hour = parse_time(end_str)
                
                return start_hour, end_hour
        except Exception:
            pass
        
        return 0, 0
    
    @staticmethod
    def publish_schedules(db: Session, week_start_date: datetime) -> int:
        """Publish all schedules for a week"""
        result = db.query(ShiftSchedule).filter(and_(
            ShiftSchedule.schedule_date >= week_start_date,
            ShiftSchedule.schedule_date <= week_start_date + timedelta(days=6),
            ShiftSchedule.is_published == False
        )).update({ShiftSchedule.is_published: True})
        
        db.commit()
        return result
    
    @staticmethod
    def bulk_upload_schedules(db: Session, schedules_data: List[dict]) -> int:
        """
        Bulk upload schedules from file
        
        Args:
            db: Database session
            schedules_data: List of schedule data dicts
            
        Returns:
            Number of schedules created/updated
        """
        count = 0
        for data in schedules_data:
            try:
                user = db.query(User).filter(User.employee_no == data['employee_no']).first()
                if user:
                    ShiftScheduleService.save_shift(
                        db,
                        user.id,
                        datetime.fromisoformat(data['date']),
                        data['shift_time'],
                        data['campaign'],
                        data.get('notes')
                    )
                    count += 1
            except Exception as e:
                print(f"Error uploading schedule: {e}")
                continue
        
        return count
