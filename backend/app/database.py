from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from app.config import settings

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
    echo=settings.debug,
)


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    import app.models  # noqa: F401 – ensure models loaded
    Base.metadata.create_all(bind=engine)

    # migrate existing tables: add new columns if missing
    _migrate_add_column("print_records", "printer_name", "VARCHAR(64) DEFAULT ''")
    _migrate_add_column("print_records", "tray", "INTEGER DEFAULT 0")
    _migrate_add_column("print_records", "deducted", "BOOLEAN DEFAULT 0")


def _migrate_add_column(table: str, column: str, col_def: str):
    """Add a column if it doesn't exist (SQLite-compatible)."""
    try:
        conn = engine.raw_connection()
        cursor = conn.cursor()
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_def}")
        conn.commit()
        cursor.close()
        conn.close()
    except Exception:
        pass  # column already exists
