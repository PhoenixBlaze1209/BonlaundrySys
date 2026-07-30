# config/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Update credentials based on your local MySQL setup
DATABASE_URL = "mysql+pymysql://root:@localhost:3307/bon_laundry_db"
engine = create_engine(
    DATABASE_URL, 
    pool_recycle=3600, 
    echo=True # Turn this to False in production; True helps you debug during defense prep
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency to get db session safely
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()