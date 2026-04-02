"""
Migrate data from SQLite (viori.db) to PostgreSQL.
Run with --if-empty to only migrate if Postgres tables are empty.
Run without flags to force migration (will skip existing rows via ON CONFLICT).
"""
import os
import sys
import sqlite3
from sqlalchemy import text, inspect
from models import Base, get_engine

SQLITE_PATH = os.environ.get("SQLITE_PATH", "viori.db")

# Tables to migrate (in order — no FK dependencies)
TABLES_TO_MIGRATE = [
    "proforma_cash_flow_monthly",
    "proforma_expenses_monthly",
    "proforma_sku_monthly",
    "proforma_rdata_monthly",
    "proforma_contractors_monthly",
    "proforma_contractors_detail",
    "proforma_financing_monthly",
    "proforma_loans",
    "proforma_metadata",
    "proforma_temp_workers",
    "ad_daily_platform",
    "ad_monthly_performance",
    "facebook_ads_daily",
    "retail_monthly",
    "retail_yoy_monthly",
    "quickbooks_pl_monthly",
    "quickbooks_cashflow_monthly",
    "shopify_orders_daily",
    "cash_runway",
    "sync_log",
]


def migrate(if_empty=False):
    db_url = os.environ.get("DATABASE_URL", "")
    if not db_url:
        print("[MIGRATE] No DATABASE_URL set, skipping migration.")
        return

    if not os.path.exists(SQLITE_PATH):
        print(f"[MIGRATE] SQLite file not found at {SQLITE_PATH}, skipping.")
        return

    engine = get_engine()

    # Ensure all tables exist
    Base.metadata.create_all(engine)

    sqlite_conn = sqlite3.connect(SQLITE_PATH)
    sqlite_conn.row_factory = sqlite3.Row

    total_migrated = 0

    with engine.connect() as pg_conn:
        for table_name in TABLES_TO_MIGRATE:
            # Check if table exists in SQLite
            cursor = sqlite_conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table_name,)
            )
            if not cursor.fetchone():
                print(f"[MIGRATE] Table {table_name} not in SQLite, skipping.")
                continue

            # Check row count in SQLite
            cursor = sqlite_conn.execute(f"SELECT COUNT(*) FROM [{table_name}]")
            sqlite_count = cursor.fetchone()[0]
            if sqlite_count == 0:
                continue

            # If --if-empty, check if Postgres already has data
            if if_empty:
                try:
                    pg_count = pg_conn.execute(text(f'SELECT COUNT(*) FROM "{table_name}"')).scalar()
                    if pg_count > 0:
                        print(f"[MIGRATE] {table_name}: Postgres already has {pg_count} rows, skipping.")
                        continue
                except Exception:
                    pass

            # Get columns from SQLite
            cursor = sqlite_conn.execute(f"PRAGMA table_info([{table_name}])")
            sqlite_cols = [row[1] for row in cursor.fetchall()]

            # Get columns from Postgres
            inspector = inspect(engine)
            try:
                pg_cols = [c["name"] for c in inspector.get_columns(table_name)]
            except Exception:
                print(f"[MIGRATE] Table {table_name} not in Postgres schema, skipping.")
                continue

            # Use intersection of columns (handle schema differences)
            common_cols = [c for c in sqlite_cols if c in pg_cols]
            if not common_cols:
                print(f"[MIGRATE] No common columns for {table_name}, skipping.")
                continue

            # Read all data from SQLite
            col_list = ", ".join(f"[{c}]" for c in common_cols)
            cursor = sqlite_conn.execute(f"SELECT {col_list} FROM [{table_name}]")
            rows = cursor.fetchall()

            if not rows:
                continue

            # Build INSERT statement
            pg_col_list = ", ".join(f'"{c}"' for c in common_cols)
            placeholders = ", ".join(f":{c}" for c in common_cols)
            insert_sql = f'INSERT INTO "{table_name}" ({pg_col_list}) VALUES ({placeholders}) ON CONFLICT DO NOTHING'

            # Batch insert
            batch_size = 500
            inserted = 0
            for i in range(0, len(rows), batch_size):
                batch = rows[i:i + batch_size]
                params = [{c: row[j] for j, c in enumerate(common_cols)} for row in batch]
                for p in params:
                    try:
                        pg_conn.execute(text(insert_sql), p)
                        inserted += 1
                    except Exception as e:
                        print(f"[MIGRATE] Error inserting into {table_name}: {e}")

            pg_conn.commit()
            total_migrated += inserted
            print(f"[MIGRATE] {table_name}: {inserted}/{len(rows)} rows migrated.")

    sqlite_conn.close()
    print(f"[MIGRATE] Complete. Total rows migrated: {total_migrated}")


if __name__ == "__main__":
    if_empty = "--if-empty" in sys.argv
    migrate(if_empty=if_empty)
