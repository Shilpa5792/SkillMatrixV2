"""
FastAPI service that exposes `/master-skill` so you can fetch rows from
the MasterSkill table via Postman or any HTTP client.
"""

import os
from typing import Any, Dict, List, Optional

import psycopg2
from fastapi import FastAPI, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv


load_dotenv()

app = FastAPI(title="Skill Matrix API")


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


def fetch_master_skill(search: Optional[str] = None) -> List[Dict[str, Any]]:
    sql = """
        SELECT id, skill_name, description, "isMandatory", created_at, updated_at
        FROM "MasterSkill"
        WHERE (%(search)s IS NULL OR skill_name ILIKE %(pattern)s)
        ORDER BY updated_at DESC NULLS LAST
    """
    params = {"search": search, "pattern": f"%{search}%" if search else None}

    with get_db_connection() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(sql, params)
        return cur.fetchall()


@app.get("/get_master_skill")
def master_skill_endpoint(
    search: Optional[str] = Query(None, description="Case-insensitive skill_name filter"),
):
    try:
        data = fetch_master_skill(search=search)
    except psycopg2.Error as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    # jsonable_encoder converts datetime and other types into JSON‑serializable data
    return {"count": len(data), "results": jsonable_encoder(data)}

    #http://127.0.0.1:8000/get_master_skill if testing locally
    #uvicorn api:app --reload --port 8000 run locally

