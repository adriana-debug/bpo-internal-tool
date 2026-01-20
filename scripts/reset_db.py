from app.core.database import engine, Base
from app.models.user import User
from app.models.rbac import Role, Module

def create_fresh_database():
    # Drop all tables
    Base.metadata.drop_all(bind=engine)
    
    # Create all tables with new schema
    Base.metadata.create_all(bind=engine)
    
    print("Database tables created successfully!")
    
    # Print the User table columns to verify
    from sqlalchemy import inspect
    inspector = inspect(engine)
    columns = inspector.get_columns('users')
    print("\nUser table columns:")
    for col in columns:
        print(f"  {col['name']}: {col['type']}")

if __name__ == "__main__":
    create_fresh_database()