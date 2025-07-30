import os
import sys
import logging
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).parent.resolve()))

# Import after path setup
from database import init_db, engine
from models import User, UserRole
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext
from sqlalchemy import text
from config.settings import settings

# Initialize password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def setup_directories():
    """Create required directories if they don't exist."""
    dirs = [
        "data",
        "data/db",
        "data/uploads",
        "data/vector_store",
        "data/chat_history",
        "logs",
        "models",
        "static",
        "templates"
    ]
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured directory exists: {dir_path}")

def create_admin_user():
    """Create an admin user if it doesn't exist."""
    Session = sessionmaker(bind=engine)
    db = Session()
    
    try:
        # Check if admin user exists
        admin = db.query(User).filter(User.email == settings.ADMIN_EMAIL).first()
        if not admin:
            # Create admin role if it doesn't exist
            admin_role = db.query(UserRole).filter(UserRole.name == "admin").first()
            if not admin_role:
                admin_role = UserRole(name="admin", description="Administrator")
                db.add(admin_role)
                db.commit()
            
            # Create admin user
            admin = User(
                email=settings.ADMIN_EMAIL,
                hashed_password=pwd_context.hash(settings.ADMIN_PASSWORD),
                full_name="System Administrator",
                role_id=admin_role.id,
                is_active=True,
                created_at=datetime.utcnow()
            )
            db.add(admin)
            db.commit()
            logger.info("Created admin user")
        else:
            logger.info("Admin user already exists")
            
    except Exception as e:
        logger.error(f"Error creating admin user: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def init_database():
    """Initialize the database and create required data."""
    try:
        # Create required directories
        setup_directories()
        
        # Initialize database tables
        init_db()
        
        # Test database connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            assert result.scalar() == 1, "Database connection test failed"
            logger.info("Database connection test successful")
        
        # Create admin user
        create_admin_user()
        
        logger.info("Database initialization completed successfully")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

if __name__ == "__main__":
    init_database()
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
