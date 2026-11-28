from sqlmodel import create_engine, Session
from core.config import settings

# SQLite 需要 check_same_thread=False，MySQL/PG 不需要
is_sqlite = settings.db_url.startswith("sqlite")

if settings.app == 'dev':
    engine = create_engine(
        settings.db_url,
        echo=True,
        connect_args={'check_same_thread': False} if is_sqlite else {}
    )
else:
    engine = create_engine(
        settings.db_url,
        echo=False,
        pool_size=15,
        connect_args={'check_same_thread': False} if is_sqlite else {}
    )

def get_db():
    with Session(engine) as session:
        yield session