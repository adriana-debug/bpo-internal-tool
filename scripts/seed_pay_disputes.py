"""
Seed script for Pay Disputes sample data
"""
import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.pay_dispute import PayDispute


# Sample data
DISPUTE_TYPES = ["Overtime", "Deduction", "Bonus", "Allowance", "Tax", "Others"]
PRIORITIES = ["Low", "Medium", "Medium", "High", "Urgent"]  # Medium weighted higher
STATUSES = ["Open", "Open", "Under Review", "Pending Payroll", "Resolved", "Resolved", "Rejected", "Escalated"]

SUBJECTS = [
    "Missing overtime pay for {month}",
    "Incorrect deduction on payslip",
    "Performance bonus not received",
    "Night differential not computed",
    "Holiday pay discrepancy",
    "Tax computation error",
    "Transportation allowance missing",
    "Meal allowance not included",
    "Attendance incentive not credited",
    "Commission calculation incorrect",
    "Back pay not received",
    "13th month pay computation issue",
    "Leave conversion not processed",
    "Salary adjustment not reflected",
    "Training allowance missing",
]

DESCRIPTIONS = [
    "I worked {hours} hours of overtime on {dates} but this was not reflected in my payslip for {month}. Please review and process the payment.",
    "My payslip shows a deduction of ${amount} but I was not informed about this. Please clarify the reason for this deduction.",
    "According to the announcement, I should have received a performance bonus for {quarter} quarter but it's not in my pay.",
    "I have been working night shifts for the past {weeks} weeks but the night differential is not properly computed in my salary.",
    "The holiday pay for {holiday} was not included in my salary. I worked on that day and should receive holiday premium.",
    "My tax withholding seems incorrect. The amount deducted is higher than expected based on my income bracket.",
    "My transportation allowance for {month} was not included in the payroll. This is a regular benefit that I receive monthly.",
    "The meal allowance that is supposed to be included every payday was missing from my recent payslip.",
    "I met the attendance requirements for the incentive program but did not receive the attendance bonus.",
    "My sales commission for {month} appears to be miscalculated. Based on my records, I should receive ${amount}.",
]

RESOLUTION_NOTES = [
    "Verified the overtime records. Payment has been processed and will be credited in the next payroll.",
    "After review, the deduction was found to be in error. Full amount has been refunded.",
    "Confirmed eligibility for the bonus. Amount has been processed for payment.",
    "Night differential has been recalculated and adjusted. Back pay will be included in next payroll.",
    "Holiday pay has been computed and approved for payment.",
    "Tax computation has been corrected. Adjustment will reflect in next pay period.",
    "Dispute rejected after review. The deduction was valid per company policy signed by employee.",
    "Escalated to Finance department for further review and approval.",
]

MONTHS = ["January 2026", "December 2025", "November 2025", "October 2025", "September 2025"]
PAY_PERIODS = ["Jan 1-15, 2026", "Jan 16-31, 2026", "Dec 1-15, 2025", "Dec 16-31, 2025", "Nov 1-15, 2025", "Nov 16-30, 2025"]


def generate_ticket_number(db: Session, year: int, sequence: int) -> str:
    """Generate a unique ticket number"""
    return f"PAY-{year}-{sequence:04d}"


def seed_pay_disputes(db: Session, count: int = 50):
    """Seed sample pay disputes into the database"""

    # Check if we already have pay disputes
    existing_count = db.query(PayDispute).count()
    if existing_count >= count:
        print(f"Database already has {existing_count} pay disputes. Skipping seed.")
        return

    # Get employees to create disputes for
    employees = db.query(User).filter(User.employee_no != "E001").limit(100).all()
    if not employees:
        print("No employees found. Please seed employees first.")
        return

    # Get admin user for created_by
    admin = db.query(User).filter(User.employee_no == "E001").first()
    admin_id = admin.id if admin else None

    print(f"Seeding {count - existing_count} pay disputes...")

    current_year = datetime.now().year
    ticket_sequence = existing_count + 1

    disputes_to_create = count - existing_count
    for i in range(disputes_to_create):
        employee = random.choice(employees)
        dispute_type = random.choice(DISPUTE_TYPES)
        status = random.choice(STATUSES)
        priority = random.choice(PRIORITIES)

        # Generate subject
        subject_template = random.choice(SUBJECTS)
        subject = subject_template.format(
            month=random.choice(MONTHS),
            quarter=random.choice(["Q1", "Q2", "Q3", "Q4"]),
            holiday="Christmas Day"
        )

        # Generate description
        desc_template = random.choice(DESCRIPTIONS)
        description = desc_template.format(
            hours=random.randint(4, 20),
            dates="multiple dates in " + random.choice(MONTHS),
            month=random.choice(MONTHS),
            weeks=random.randint(2, 8),
            holiday=random.choice(["Christmas Day", "New Year's Day", "Independence Day"]),
            quarter=random.choice(["Q1", "Q2", "Q3", "Q4"]),
            amount=random.randint(50, 500)
        )

        # Generate disputed amount
        if dispute_type in ["Overtime", "Bonus", "Allowance"]:
            disputed_amount = round(random.uniform(50, 800), 2)
        elif dispute_type == "Deduction":
            disputed_amount = round(random.uniform(20, 300), 2)
        else:
            disputed_amount = round(random.uniform(30, 500), 2) if random.random() > 0.3 else None

        # Generate resolution data for resolved/rejected disputes
        resolution_notes = None
        resolution_amount = None
        resolved_date = None

        if status in ["Resolved", "Rejected"]:
            resolution_notes = random.choice(RESOLUTION_NOTES)
            if status == "Resolved" and disputed_amount:
                resolution_amount = disputed_amount if random.random() > 0.3 else round(disputed_amount * random.uniform(0.5, 1.0), 2)
            resolved_date = datetime.now().date() - timedelta(days=random.randint(1, 30))

        # Create the dispute
        dispute = PayDispute(
            ticket_no=generate_ticket_number(db, current_year, ticket_sequence),
            employee_id=employee.id,
            dispute_type=dispute_type,
            pay_period=random.choice(PAY_PERIODS),
            disputed_amount=disputed_amount,
            subject=subject,
            description=description,
            status=status,
            priority=priority,
            resolution_notes=resolution_notes,
            resolution_amount=resolution_amount,
            resolved_date=resolved_date,
            created_by=admin_id,
            created_at=datetime.now() - timedelta(days=random.randint(1, 60))
        )

        db.add(dispute)
        ticket_sequence += 1

        if (i + 1) % 10 == 0:
            print(f"  Created {i + 1} disputes...")

    db.commit()
    print(f"Successfully seeded {disputes_to_create} pay disputes!")


if __name__ == "__main__":
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        seed_pay_disputes(db)
    finally:
        db.close()
