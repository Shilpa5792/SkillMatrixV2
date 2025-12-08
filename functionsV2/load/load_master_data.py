"""
Load master data from the INFOLDER_Master_Skills.csv file into PostgreSQL.

Mapping from CSV columns to tables:
    Category         -> MasterDomain.domain_name
    Sub-Category     -> MasterDiscipline.discipline_name
    Sub-Sub-Category -> MasterSkill.skill_name
    Tools            -> MasterFramework.framework_name
    L1               -> MasterFramework.basic
    L2               -> MasterFramework.intermediate
    L3               -> MasterFramework.expert

Each row also creates/updates the SkillHierarchyLink entry tying the
domain/discipline/skill/framework together.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, Optional, Set, Tuple, Any

import pandas as pd
import psycopg
from psycopg import sql

from db_setup import DatabaseSettings, maybe_load_env


def normalize(value: Optional[str]) -> str:
    if value is None:
        return ""
    return str(value).strip()


def canonical(value: str) -> str:
    """Normalized key used for de-duplication (case-insensitive)."""
    return normalize(value).lower()


def get_or_create(
    cur: psycopg.Cursor,
    cache: Dict[str, int],
    table: str,
    column: str,
    value: str,
    extra_columns: Optional[Dict[str, Any]] = None,
    cache_key: Optional[str] = None,
) -> int:
    key = cache_key or value
    if key in cache:
        return cache[key]

    cur.execute(
        sql.SQL('SELECT id FROM {} WHERE {} = %s').format(
            sql.Identifier(table),
            sql.Identifier(column),
        ),
        (value,),
    )
    row = cur.fetchone()
    if row:
        cache[key] = row[0]
        return row[0]

    columns = [column]
    values = [value]

    if extra_columns:
        for col, val in extra_columns.items():
            columns.append(col)
            values.append(val)

    insert_query = sql.SQL("INSERT INTO {} ({}) VALUES ({}) RETURNING id").format(
        sql.Identifier(table),
        sql.SQL(", ").join(sql.Identifier(col) for col in columns),
        sql.SQL(", ").join(sql.Placeholder() for _ in columns),
    )

    cur.execute(insert_query, tuple(values))
    new_id = cur.fetchone()[0]
    cache[key] = new_id
    return new_id


def load_data(csv_path: Path) -> None:
    maybe_load_env()
    settings = DatabaseSettings.from_env()
    df = pd.read_csv(csv_path).fillna("")

    domain_cache: Dict[str, int] = {}
    discipline_cache: Dict[str, int] = {}
    skill_cache: Dict[str, int] = {}
    framework_cache: Dict[str, int] = {}

    with settings.connect() as conn, conn.cursor() as cur:
        cur.execute(sql.SQL("SET search_path TO {}, public").format(sql.Identifier(settings.schema)))

        created_hierarchy = 0
        processed_links: Set[Tuple[str, str, str, str]] = set()
        for _, row in df.iterrows():
            category = normalize(row.get("Category"))
            subcategory = normalize(row.get("Sub-Category"))
            subsubcategory = normalize(row.get("Sub-Sub-Category"))
            tool = normalize(row.get("Tools"))
            lvl1 = normalize(row.get("L1", ""))
            lvl2 = normalize(row.get("L2", ""))
            lvl3 = normalize(row.get("L3", ""))

            if not (category and subcategory and subsubcategory and tool):
                continue

            link_key = (
                canonical(category),
                canonical(subcategory),
                canonical(subsubcategory),
                canonical(tool),
            )
            if link_key in processed_links:
                continue
            processed_links.add(link_key)

            domain_id = get_or_create(
                cur,
                domain_cache,
                "MasterDomain",
                "domain_name",
                category,
                {"description": "", "isMandatory": False},
                cache_key=link_key[0],
            )
            discipline_id = get_or_create(
                cur,
                discipline_cache,
                "MasterDiscipline",
                "discipline_name",
                subcategory,
                {"description": "", "isMandatory": False},
                cache_key=link_key[1],
            )
            skill_id = get_or_create(
                cur,
                skill_cache,
                "MasterSkill",
                "skill_name",
                subsubcategory,
                {"description": "", "isMandatory": False},
                cache_key=link_key[2],
            )
            framework_id = get_or_create(
                cur,
                framework_cache,
                "MasterFramework",
                "framework_name",
                tool,
                {
                    "basic": lvl1,
                    "intermediate": lvl2,
                    "expert": lvl3,
                    "description": "",
                    "isMandatory": False,
                },
                cache_key=link_key[3],
            )

            cur.execute(
                """
                SELECT id FROM "SkillHierarchyLink"
                WHERE domain_id = %s AND discipline_id = %s
                  AND skill_id = %s AND framework_id = %s
                """,
                (domain_id, discipline_id, skill_id, framework_id),
            )
            existing = cur.fetchone()
            if existing:
                continue

            cur.execute(
                """
                INSERT INTO "SkillHierarchyLink"
                    (domain_id, discipline_id, skill_id, framework_id)
                VALUES (%s, %s, %s, %s)
                """,
                (domain_id, discipline_id, skill_id, framework_id),
            )
            created_hierarchy += 1

        conn.commit()
        print(f"Inserted/linked {created_hierarchy} hierarchy rows from {len(df)} CSV rows.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Load master data into PostgreSQL.")
    parser.add_argument(
        "--csv",
        type=Path,
        default=Path("INFOLDER_Master_Skills.csv"),
        help="Path to the master skills CSV file.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    load_data(args.csv)

