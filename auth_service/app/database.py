from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.get_redis import POSTGRES

engine = create_engine(POSTGRES[0])
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
