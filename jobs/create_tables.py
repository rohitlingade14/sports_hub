"""Create all Delta tables from ddl/schema.sql.   python -m jobs.create_tables"""
import re
from pathlib import Path

from jobs.common import absolute_base, get_spark

DDL_FILE = Path(__file__).resolve().parent.parent / "ddl" / "schema.sql"


def statements(base: str) -> list[str]:
    text = DDL_FILE.read_text().replace("{base}", base)
    text = re.sub(r"^\s*--.*$", "", text, flags=re.M)
    return [s.strip() for s in text.split(";") if s.strip()]


def main() -> None:
    spark = get_spark("create-tables")
    base = absolute_base()
    for stmt in statements(base):
        try:
            spark.sql(stmt)
        except Exception as exc:  # ADD CONSTRAINT is not idempotent
            if stmt.upper().startswith("ALTER") and "already exists" in str(exc).lower():
                continue
            raise
    print(f"Delta tables ready under {base}")
    spark.stop()


if __name__ == "__main__":
    main()
