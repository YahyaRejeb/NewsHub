from sqlalchemy import create_engine, inspect, text
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


def ensure_schema_extensions():
    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        return

    existing_columns = {column["name"] for column in inspector.get_columns("users")}
    if "profile_photo" not in existing_columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE users ADD COLUMN profile_photo LONGTEXT NULL"))

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
