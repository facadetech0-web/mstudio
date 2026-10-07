import sqlite3
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def ensure_schema():
    Base.metadata.create_all(bind=engine)
    if "sqlite" in settings.DATABASE_URL:
        try:
            with engine.connect() as conn:
                # Check clips columns
                cursor = conn.exec_driver_sql("PRAGMA table_info(clips);")
                existing_cols = {row[1] for row in cursor.fetchall()}
                if existing_cols:
                    if "negative_prompt" not in existing_cols:
                        conn.exec_driver_sql("ALTER TABLE clips ADD COLUMN negative_prompt TEXT DEFAULT '';")
                    if "lora_path" not in existing_cols:
                        conn.exec_driver_sql("ALTER TABLE clips ADD COLUMN lora_path VARCHAR(500) DEFAULT '';")

                # Check jobs columns
                cursor = conn.exec_driver_sql("PRAGMA table_info(jobs);")
                job_cols = {row[1] for row in cursor.fetchall()}
                if job_cols:
                    if "negative_prompt" not in job_cols:
                        conn.exec_driver_sql("ALTER TABLE jobs ADD COLUMN negative_prompt TEXT DEFAULT '';")
                    if "lora_path" not in job_cols:
                        conn.exec_driver_sql("ALTER TABLE jobs ADD COLUMN lora_path VARCHAR(500) DEFAULT '';")
                conn.commit()
        except Exception:
            pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
