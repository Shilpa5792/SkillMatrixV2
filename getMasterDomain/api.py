"""
FastAPI service that exposes `/get_master_domain` so you can fetch rows from
the MasterDomain table via Postman or any HTTP client.
"""

import os
from typing import Any, Dict, List

import psycopg2
from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv


load_dotenv()

app = FastAPI(title="Master Domain API")


def get_db_connection():
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        dbname=os.getenv("DB_NAME"),
        port=int(os.getenv("DB_PORT", "5432")),
        options=f"-c search_path={os.getenv('DB_SCHEMA')}",
    )
    return conn


def fetch_master_domain() -> List[Dict[str, Any]]:
    sql = 'SELECT * FROM "MasterDomain" ORDER BY id'
    with get_db_connection() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(sql)
        return cur.fetchall()


@app.get("/get_master_domain")
def get_master_domain():
    try:
        data = fetch_master_domain()
    except psycopg2.Error as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {"count": len(data), "results": jsonable_encoder(data)}


# Run locally:
# uvicorn api:app --reload --port 8003
# Test in Postman:
# GET http://127.0.0.1:8003/get_master_domain


