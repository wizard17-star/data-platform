import os
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, text

PG_HOST = os.getenv("PG_HOST", "postgres")
PG_PORT = os.getenv("PG_PORT", "5432")
PG_DB   = os.getenv("PG_DB", "appdb")
PG_USER = os.getenv("PG_USER", "app")
PG_PASS = os.getenv("PG_PASS", "app")

DATA_DIR = Path(os.getenv("DATA_DIR", "/data"))

def sanitize_table_name(name: str) -> str:
    out = []
    for ch in name.lower():
        if ch.isalnum() or ch == "_":
            out.append(ch)
        elif ch in (" ", "-", "."):
            out.append("_")
    s = "".join(out).strip("_")
    return s or "table"

def main():
    if not DATA_DIR.exists():
        raise RuntimeError(f"DATA_DIR not found: {DATA_DIR}")

    csv_files = sorted(DATA_DIR.glob("*.csv"))
    if len(csv_files) < 3:
        raise RuntimeError(f"Expected at least 3 CSV files in {DATA_DIR}, found {len(csv_files)}")

    engine = create_engine(
        f"postgresql+psycopg2://{PG_USER}:{PG_PASS}@{PG_HOST}:{PG_PORT}/{PG_DB}",
        pool_pre_ping=True,
    )

    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))

    for csv_path in csv_files[:3]:
        table = sanitize_table_name(csv_path.stem)
        print(f"\n=== Loading {csv_path.name} -> table: {table} ===")

        df = pd.read_csv(csv_path)
        df.columns = [sanitize_table_name(c) for c in df.columns]

        df.to_sql(table, engine, if_exists="replace", index=False)

        with engine.connect() as conn:
            cnt = conn.execute(text(f'SELECT COUNT(*) FROM "{table}"')).scalar_one()
        print(f"Inserted rows: {cnt}")

    print("\nDONE ✅")

if __name__ == "__main__":
    main()
