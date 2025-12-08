import os
import json
from flask import config
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from urllib.parse import quote_plus


def load_config():
    """Load DB config from config.json."""
    ENV = os.getenv("ENV", "development")

    config_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        (
            "prod_config.json"
            if ENV == "production"
            else "dev_config.json" if ENV == "development" else "config.json"
        ),
    )

    with open(config_path, "r") as f:
        return json.load(f)


def create_database():
    config = load_config()

    # db_user = config["DB_USER"]
    # db_pass = config["DB_PASS"]
    # db_name = config["DB_NAME"]
    # db_host = config["DB_HOST"]
    # db_port = config["DB_PORT"]

    # instance_connection_name = config["INSTANCE_CONNECTION_NAME"]

    # db_socket_dir = config.get("DB_SOCKET_DIR", "/cloudsql")
    # db_host = f"{db_socket_dir}/{instance_connection_name}"

    # db_url = (
    #     f"postgresql+pg8000://{db_user}:{db_pass}@/{db_name}"
    #     f"?unix_sock={db_host}/.s.PGSQL.5432"
    # )

    # db_url = f"postgresql+pg8000://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"

    db_user = quote_plus(config["DB_USER"])
    db_pass = quote_plus(config["DB_PASS"])
    db_name = config["DB_NAME"]
    db_host = config["DB_HOST"]
    db_port = config["DB_PORT"]

    db_url = f"postgresql+pg8000://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"

    engine = create_engine(db_url, poolclass=NullPool, future=True)

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    return engine, SessionLocal


def get_db(SessionLocal):
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
