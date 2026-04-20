import os
from sqlalchemy import create_engine
from urllib.parse import quote_plus

DB_USER = "root"
DB_PASS = quote_plus("jVilN(lH)KrC7=qR5TXC8F")
DB_HOST = "localhost"
DB_NAME = "aipp"

engine = create_engine(
    f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}",
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False
)