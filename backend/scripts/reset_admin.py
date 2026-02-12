import sys
import os

sys.path.append(os.getcwd())

from sqlalchemy import create_engine, text, Column, Integer, String, Boolean, Enum as SqlEnum
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.security import get_password_hash
import enum
import bcrypt

# Monkey patch bcrypt for passlib compatibility
if not hasattr(bcrypt, "__about__"):
    try:
        class About:
            __version__ = bcrypt.__version__
        bcrypt.__about__ = About()
    except Exception:
        pass

# Hardcoded for reliability
DATABASE_URL = "postgresql://user_iot:password123@localhost:5433/vending_machine"

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    STAFF = "STAFF"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String, nullable=True)
    role = Column(SqlEnum(UserRole), default=UserRole.STAFF)

def reset_admin():
    # Drop and create
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS users CASCADE"))
        # Clean up enum type if exists
        try:
             conn.execute(text("DROP TYPE IF EXISTS userrole CASCADE"))
        except:
             pass
        conn.commit()
    
    Base.metadata.create_all(bind=engine)

    # Seed
    db = SessionLocal()
    try:
        # Use direct bcrypt hashing to avoid passlib/bcrypt version issues during seeding
        hashed = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        admin = User(
            username="admin",
            hashed_password=hashed,
            full_name="Administrator",
            role=UserRole.ADMIN
        )
        db.add(admin)
        db.commit()
        print("Admin user created successfully (Port 5433)!")
    except Exception as e:
        print(f"Error seeding: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    reset_admin()
