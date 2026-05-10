import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Di Render (production), gunakan /tmp yang writable
# Di lokal, gunakan ./dispatcher.db seperti biasa
IS_PRODUCTION = os.environ.get("RENDER", False)

if IS_PRODUCTION:
    DB_URL = "sqlite:////tmp/dispatcher.db"
else:
    DB_URL = "sqlite:///./dispatcher.db"

engine = create_engine(
    DB_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
