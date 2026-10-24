"""Load sample data.
   python -m jobs.seed                      # Spark MERGE into tables created by create_tables
   python -m jobs.seed --engine delta-rs    # no Java/Spark needed (dev and tests)
"""
import argparse

from jobs.common import table_path
from jobs.seed_data import KEYS, PARTITIONS, build_all


def seed_spark(base: str | None = None) -> None:
    from jobs.common import get_spark, upsert

    spark = get_spark("seed")
    for table, rows in build_all().items():
        upsert(spark, table, rows, KEYS[table], base)
        print(f"{table}: {len(rows)} rows")
    spark.stop()


def seed_delta_rs(base: str | None = None) -> None:
    import pyarrow as pa
    from deltalake import write_deltalake

    for table, rows in build_all().items():
        write_deltalake(table_path(table, base), pa.Table.from_pylist(rows), mode="overwrite",
                        partition_by=PARTITIONS.get(table))
        print(f"{table}: {len(rows)} rows")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", choices=["spark", "delta-rs"], default="spark")
    args = ap.parse_args()
    seed_spark() if args.engine == "spark" else seed_delta_rs()
