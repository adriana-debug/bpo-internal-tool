from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, distinct
from datetime import datetime, timedelta, date
from app.models.user import User, ShiftSchedule
from app.schemas.employee import EmployeeResponse
from typing import List, Optional, Dict, Any

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
                ShiftSchedule.schedule_date >= week_start_date.date(),
                ShiftSchedule.schedule_date <= week_end_date.date()
            )).all()
            
            # Build daily schedule
            daily_shifts = {}
            for i, day_name in enumerate(day_names):
                day_date = (week_start_date + timedelta(days=i)).date()
                
                # Find schedule for this day
                day_schedule = next((s for s in week_schedules if s.schedule_date == day_date), None)
                
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
            ShiftSchedule.schedule_date >= week_start_date.date(),
            ShiftSchedule.schedule_date <= (week_start_date + timedelta(days=6)).date(),
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

    @staticmethod
    def get_schedule_statistics(
        db: Session,
        week_start_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get shift schedule statistics

        Args:
            db: Database session
            week_start_date: Optional week start date for filtering

        Returns:
            Dictionary with schedule statistics
        """
        # Default to current week if not specified
        if not week_start_date:
            today = datetime.now()
            week_start_date = today - timedelta(days=today.weekday())

        week_end_date = week_start_date + timedelta(days=6)

        # Count total employees with schedules this week
        total_employees = db.query(User).filter(User.is_active == True).count()

        # Count schedules for this week
        week_schedules = db.query(ShiftSchedule).filter(and_(
            ShiftSchedule.schedule_date >= week_start_date.date(),
            ShiftSchedule.schedule_date <= week_end_date.date()
        ))

        total_schedules = week_schedules.count()
        published_schedules = week_schedules.filter(ShiftSchedule.is_published == True).count()
        unpublished_schedules = total_schedules - published_schedules

        # Count by shift type
        morning_count = week_schedules.filter(
            or_(
                ShiftSchedule.shift_time.ilike('%9am%'),
                ShiftSchedule.shift_time.ilike('%6am%'),
                ShiftSchedule.shift_time.ilike('%7am%'),
                ShiftSchedule.shift_time.ilike('%8am%')
            )
        ).count()

        afternoon_count = week_schedules.filter(
            or_(
                ShiftSchedule.shift_time.ilike('%12pm%'),
                ShiftSchedule.shift_time.ilike('%1pm%'),
                ShiftSchedule.shift_time.ilike('%2pm%')
            )
        ).count()

        night_count = week_schedules.filter(
            or_(
                ShiftSchedule.shift_time.ilike('%11pm%'),
                ShiftSchedule.shift_time.ilike('%10pm%'),
                ShiftSchedule.shift_time.ilike('%9pm%')
            )
        ).count()

        # Count employees with complete schedules (all 7 days)
        employees_with_schedules = db.query(ShiftSchedule.user_id).filter(and_(
            ShiftSchedule.schedule_date >= week_start_date.date(),
            ShiftSchedule.schedule_date <= week_end_date.date()
        )).group_by(ShiftSchedule.user_id).having(func.count() >= 5).count()

        return {
            "total_employees": total_employees,
            "total_schedules": total_schedules,
            "published_schedules": published_schedules,
            "unpublished_schedules": unpublished_schedules,
            "morning_shifts": morning_count,
            "afternoon_shifts": afternoon_count,
            "night_shifts": night_count,
            "employees_with_schedules": employees_with_schedules,
            "coverage_percentage": round((employees_with_schedules / total_employees * 100), 1) if total_employees > 0 else 0
        }

    @staticmethod
    def get_filter_options(db: Session) -> Dict[str, List]:
        """
        Get unique values for filter dropdowns

        Returns:
            Dictionary with campaigns, shifts, and employees
        """
        # Get unique campaigns
        campaigns = db.query(distinct(User.campaign)).filter(
            User.is_active == True,
            User.campaign.isnot(None)
        ).all()
        campaigns = [c[0] for c in campaigns if c[0]]

        # Get unique shifts
        shifts = db.query(distinct(ShiftSchedule.shift_time)).filter(
            ShiftSchedule.shift_time.isnot(None)
        ).all()
        shifts = [s[0] for s in shifts if s[0]]

        # If no shifts in database, provide default options
        if not shifts:
            shifts = ["9am to 5pm", "11pm to 7am", "12pm to 8pm", "6am to 2pm", "10pm to 6am"]

        # Get employees for dropdown
        employees = db.query(User).filter(User.is_active == True).order_by(User.full_name).all()
        employees_list = [
            {"id": emp.id, "employee_no": emp.employee_no, "full_name": emp.full_name, "campaign": emp.campaign}
            for emp in employees
        ]

        return {
            "campaigns": sorted(campaigns),
            "shifts": shifts,
            "employees": employees_list
        }

    @staticmethod
    def get_schedules_for_export(
        db: Session,
        week_start_date: datetime,
        search: Optional[str] = None,
        campaign: Optional[str] = None
    ) -> List[Dict]:
        """
        Get schedules formatted for CSV export

        Args:
            db: Database session
            week_start_date: Start date of the week
            search: Optional search term
            campaign: Optional campaign filter

        Returns:
            List of schedule records for export
        """
        week_end_date = week_start_date + timedelta(days=6)

        # Query schedules with employee data
        query = db.query(ShiftSchedule, User).join(User).filter(and_(
            ShiftSchedule.schedule_date >= week_start_date.date(),
            ShiftSchedule.schedule_date <= week_end_date.date(),
            User.is_active == True
        ))

        if search:
            query = query.filter(or_(
                User.full_name.ilike(f"%{search}%"),
                User.employee_no.ilike(f"%{search}%")
            ))

        if campaign:
            query = query.filter(User.campaign == campaign)

        schedules = query.order_by(User.full_name, ShiftSchedule.schedule_date).all()

        # Format for export
        result = []
        for schedule, user in schedules:
            result.append({
                "employee_no": user.employee_no,
                "employee_name": user.full_name,
                "campaign": user.campaign or "",
                "date": schedule.schedule_date.isoformat(),
                "day_of_week": schedule.day_of_week,
                "shift_time": schedule.shift_time,
                "is_published": "Yes" if schedule.is_published else "No",
                "notes": schedule.notes or ""
            })

        return result

    @staticmethod
    def delete_schedule(db: Session, schedule_id: int) -> bool:
        """
        Delete a shift schedule

        Args:
            db: Database session
            schedule_id: ID of the schedule to delete

        Returns:
            True if deleted, False if not found
        """
        schedule = db.query(ShiftSchedule).filter(ShiftSchedule.id == schedule_id).first()
        if not schedule:
            return False

        db.delete(schedule)
        db.commit()
        return True

    @staticmethod
    def get_schedule_by_id(db: Session, schedule_id: int) -> Optional[ShiftSchedule]:
        """
        Get a single schedule by ID

        Args:
            db: Database session
            schedule_id: ID of the schedule

        Returns:
            ShiftSchedule object or None
        """
        return db.query(ShiftSchedule).filter(ShiftSchedule.id == schedule_id).first()
