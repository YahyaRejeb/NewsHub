from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

# Replicating the old credentials
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:@127.0.0.1/newshub1"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True, # check connection before using
    pool_size=10,
    max_overflow=20
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
