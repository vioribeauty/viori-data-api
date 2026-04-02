"""
Viori Data Hub API
Lightweight FastAPI service providing authenticated read/write access
to the shared Viori financial database for all AI bots.
"""
import os
import hashlib
import json
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends, Header, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import text, inspect
from models import Base, get_engine, get_session, ApiKey

app = FastAPI(
    title="Viori Data Hub API",
    description="Shared financial database for Viori AI bot fleet",
    version="1.0.0",
)

# CORS - allow cross-origin requests for migration and bot access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# AUTH
# ============================================================

def hash_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


async def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")):
    session = get_session()
    try:
        key_record = session.query(ApiKey).filter(
            ApiKey.key_hash == hash_key(x_api_key),
            ApiKey.is_active == True
        ).first()
        if not key_record:
            raise HTTPException(status_code=401, detail="Invalid API key")
        key_record.last_used = datetime.utcnow()
        session.commit()
        return key_record
    finally:
        session.close()


async def verify_write_key(key: ApiKey = Depends(verify_api_key)):
    if key.role not in ("write", "admin"):
        raise HTTPException(status_code=403, detail="Write access required")
    return key


async def verify_admin_key(key: ApiKey = Depends(verify_api_key)):
    if key.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return key


# ============================================================
# HEALTH & INFO
# ============================================================

@app.get("/health")
async def health():
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return JSONResponse(status_code=503, content={"status": "unhealthy", "error": str(e)})


@app.get("/info")
async def info(key: ApiKey = Depends(verify_api_key)):
    engine = get_engine()
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    table_info = {}
    with engine.connect() as conn:
        for table in tables:
            if table == "api_keys":
                continue
            result = conn.execute(text(f'SELECT COUNT(*) FROM "{table}"'))
            table_info[table] = result.scalar()
    return {
        "tables": len(table_info),
        "total_rows": sum(table_info.values()),
        "table_counts": table_info,
        "timestamp": datetime.utcnow().isoformat(),
    }


# ============================================================
# GENERIC QUERY ENDPOINT (read-only SQL)
# ============================================================

class QueryRequest(BaseModel):
    sql: str
    params: Optional[dict] = None


@app.post("/query")
async def run_query(req: QueryRequest, key: ApiKey = Depends(verify_api_key)):
    """Execute a read-only SQL query. Only SELECT statements allowed."""
    sql_upper = req.sql.strip().upper()
    if not sql_upper.startswith("SELECT") and not sql_upper.startswith("WITH"):
        raise HTTPException(status_code=400, detail="Only SELECT/WITH queries allowed. Use /write for mutations.")

    engine = get_engine()
    try:
        with engine.connect() as conn:
            result = conn.execute(text(req.sql), req.params or {})
            columns = list(result.keys())
            rows = [dict(zip(columns, row)) for row in result.fetchall()]
            return {"columns": columns, "rows": rows, "row_count": len(rows)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================
# WRITE ENDPOINTS
# ============================================================

class WriteRequest(BaseModel):
    sql: str
    params: Optional[dict] = None


@app.post("/write")
async def run_write(req: WriteRequest, key: ApiKey = Depends(verify_write_key)):
    """Execute a write SQL statement (INSERT, UPDATE, DELETE). Requires write key."""
    sql_upper = req.sql.strip().upper()
    forbidden = ["DROP TABLE", "DROP DATABASE", "TRUNCATE", "ALTER TABLE"]
    for f in forbidden:
        if f in sql_upper:
            raise HTTPException(status_code=400, detail=f"Statement contains forbidden operation: {f}")

    engine = get_engine()
    try:
        with engine.connect() as conn:
            result = conn.execute(text(req.sql), req.params or {})
            conn.commit()
            return {"status": "ok", "rows_affected": result.rowcount}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class BulkWriteRequest(BaseModel):
    statements: list[WriteRequest]


@app.post("/write/bulk")
async def run_bulk_write(req: BulkWriteRequest, key: ApiKey = Depends(verify_write_key)):
    """Execute multiple write statements in a transaction."""
    engine = get_engine()
    try:
        with engine.connect() as conn:
            total_affected = 0
            for stmt in req.statements:
                sql_upper = stmt.sql.strip().upper()
                forbidden = ["DROP TABLE", "DROP DATABASE", "TRUNCATE", "ALTER TABLE"]
                for f in forbidden:
                    if f in sql_upper:
                        raise HTTPException(status_code=400, detail=f"Statement contains forbidden operation: {f}")
                result = conn.execute(text(stmt.sql), stmt.params or {})
                total_affected += result.rowcount
            conn.commit()
            return {"status": "ok", "statements_executed": len(req.statements), "total_rows_affected": total_affected}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================
# TABLE-LEVEL ENDPOINTS
# ============================================================

@app.get("/tables")
async def list_tables(key: ApiKey = Depends(verify_api_key)):
    engine = get_engine()
    inspector = inspect(engine)
    tables = [t for t in inspector.get_table_names() if t != "api_keys"]
    return {"tables": tables}


@app.get("/tables/{table_name}")
async def get_table_data(
    table_name: str,
    limit: int = Query(default=100, le=10000),
    offset: int = Query(default=0),
    key: ApiKey = Depends(verify_api_key)
):
    engine = get_engine()
    inspector = inspect(engine)
    if table_name not in inspector.get_table_names() or table_name == "api_keys":
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")

    with engine.connect() as conn:
        count = conn.execute(text(f'SELECT COUNT(*) FROM "{table_name}"')).scalar()
        result = conn.execute(text(f'SELECT * FROM "{table_name}" LIMIT :limit OFFSET :offset'),
                              {"limit": limit, "offset": offset})
        columns = list(result.keys())
        rows = [dict(zip(columns, row)) for row in result.fetchall()]
        return {"table": table_name, "total_rows": count, "columns": columns, "rows": rows}


@app.get("/tables/{table_name}/schema")
async def get_table_schema(table_name: str, key: ApiKey = Depends(verify_api_key)):
    engine = get_engine()
    inspector = inspect(engine)
    if table_name not in inspector.get_table_names() or table_name == "api_keys":
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")

    columns = inspector.get_columns(table_name)
    return {
        "table": table_name,
        "columns": [{"name": c["name"], "type": str(c["type"]), "nullable": c["nullable"]} for c in columns]
    }


# ============================================================
# SYNC LOG
# ============================================================

class SyncEntry(BaseModel):
    source: str
    status: str
    records_pulled: int = 0
    error_message: Optional[str] = None
    date_range_from: Optional[str] = None
    date_range_to: Optional[str] = None


@app.post("/sync/log")
async def log_sync(entry: SyncEntry, key: ApiKey = Depends(verify_write_key)):
    engine = get_engine()
    now = datetime.utcnow().isoformat()
    with engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO sync_log (source, sync_start, sync_end, status, records_pulled, error_message, date_range_from, date_range_to)
            VALUES (:source, :now, :now, :status, :records, :error, :from_date, :to_date)
        """), {
            "source": entry.source, "now": now, "status": entry.status,
            "records": entry.records_pulled, "error": entry.error_message,
            "from_date": entry.date_range_from, "to_date": entry.date_range_to,
        })
        conn.commit()
    return {"status": "logged"}


@app.get("/sync/status")
async def sync_status(key: ApiKey = Depends(verify_api_key)):
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT DISTINCT ON (source) source, sync_end, status, records_pulled, error_message
            FROM sync_log ORDER BY source, sync_end DESC
        """))
        columns = list(result.keys())
        rows = [dict(zip(columns, row)) for row in result.fetchall()]
        return {"sources": rows}


# ============================================================
# ADMIN: API KEY MANAGEMENT
# ============================================================

class CreateKeyRequest(BaseModel):
    name: str
    role: str = "read"  # read, write, admin


@app.post("/admin/keys")
async def create_api_key(req: CreateKeyRequest, key: ApiKey = Depends(verify_admin_key)):
    import secrets
    new_key = f"viori_{secrets.token_hex(24)}"
    session = get_session()
    try:
        api_key = ApiKey(
            key_hash=hash_key(new_key),
            name=req.name,
            role=req.role,
        )
        session.add(api_key)
        session.commit()
        return {"key": new_key, "name": req.name, "role": req.role, "warning": "Save this key — it cannot be retrieved later."}
    finally:
        session.close()


# ============================================================
# STARTUP: Create tables
# ============================================================

@app.on_event("startup")
async def startup():
    engine = get_engine()
    Base.metadata.create_all(engine)

    # Bootstrap: create admin key if no keys exist
    session = get_session()
    try:
        count = session.query(ApiKey).count()
        if count == 0:
            bootstrap_key = os.environ.get("BOOTSTRAP_API_KEY", "viori_bootstrap_change_me")
            admin_key = ApiKey(
                key_hash=hash_key(bootstrap_key),
                name="bootstrap-admin",
                role="admin",
            )
            session.add(admin_key)
            session.commit()
            print(f"[BOOTSTRAP] Admin API key created. Set BOOTSTRAP_API_KEY env var to use it.")
    finally:
        session.close()
