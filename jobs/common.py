"""Shared helpers for Spark + Delta jobs."""
import os
from pathlib import Path

from delta import DeltaTable, configure_spark_with_delta_pip
from pyspark.sql import SparkSession

BASE = os.getenv("DELTA_BASE_PATH", "./warehouse").rstrip("/")


def absolute_base(base: str | None = None) -> str:
    b = (base or BASE).rstrip("/")
    return b if "://" in b else str(Path(b).resolve())


def table_path(name: str, base: str | None = None) -> str:
    return f"{absolute_base(base)}/{name}"


def get_spark(app: str = "sportshub") -> SparkSession:
    builder = (
        SparkSession.builder.appName(app)
        .master(os.getenv("SPARK_MASTER", "local[2]"))
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
        .config("spark.sql.shuffle.partitions", "4")
        .config("spark.ui.enabled", "false")
    )
    return configure_spark_with_delta_pip(builder).getOrCreate()


def upsert(spark: SparkSession, table: str, rows: list[dict], keys: list[str], base: str | None = None) -> None:
    """MERGE rows into a Delta table. Schema is taken from the table itself."""
    if not rows:
        return
    path = table_path(table, base)
    schema = spark.read.format("delta").load(path).schema
    df = spark.createDataFrame(rows, schema)
    cond = " AND ".join(f"t.{k} = s.{k}" for k in keys)
    (
        DeltaTable.forPath(spark, path).alias("t")
        .merge(df.alias("s"), cond)
        .whenMatchedUpdateAll()
        .whenNotMatchedInsertAll()
        .execute()
    )
