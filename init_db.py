import os
import sys
from pathlib import Path

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).parent.resolve()))

from database import init_db, engine
from models import User, UserRole
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

# Initialize password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_admin_user():
    """Create an admin user if it doesn't exist."""
    Session = sessionmaker(bind=engine)
    db = Session()
    
    try:
        # Check if admin user already exists
        admin = db.query(User).filter(User.username == "admin").first()
        if admin:
            print("Admin user already exists.")
            return
        
        # Create admin user
        admin = User(
            username="admin",
            email="admin@example.com",
            hashed_password=pwd_context.hash("admin"),
            full_name="Admin User",
            role=UserRole.ADMIN,
            is_active=True,
            user_preferences={"theme": "dark", "notifications": True}
        )
        
        db.add(admin)
        db.commit()
        print("Admin user created successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"Error creating admin user: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    print("Creating admin user...")
    create_admin_user()
    print("Database initialization complete!")
