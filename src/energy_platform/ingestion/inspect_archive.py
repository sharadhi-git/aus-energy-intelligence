"""
File        : inspect_archive.py
Project     : aus enregy intelligence
Description : inspect raw data zip files, and then create ingestion with parquet file landing

Author      : Sharadhi Gunathilake
Created     : 2026-11-23
Version     : 1.0

"""
import pyarrow.parquet as pq
from pathlib import Path
from time import perf_counter
from energy_platform.ingestion.archive_reader import process_daily_archive
from energy_platform.ingestion.daily_ingestion import run_daily_ingestion
PROJECT_ROOT = Path(__file__).resolve().parents[3]

archive_path = (PROJECT_ROOT/ "data"/ "raw"/ "dispatchis"/ "2026-11-14"/ "PUBLIC_DISPATCHIS_20261114.zip")
result = process_daily_archive(archive_path)

print("CSV files processed:", result.files_processed)
print("Files with validation errors:", result.files_with_errors)

selected_tables = [
    ("DISPATCH", "REGIONSUM", "9"),
    ("DISPATCH", "PRICE", "5"),
]

output_dir = PROJECT_ROOT / "data" / "processed" / "parquet"
mainfest_dir = PROJECT_ROOT / "data" / "manifest" 
start = perf_counter()
run_daily_ingestion(
    archive_path=archive_path,
    output_dir=output_dir,
    manifest_dir=mainfest_dir,
    table_keys=selected_tables,
)
elapsed = perf_counter() - start
print(f"Ingestion time: {elapsed:.2f} seconds")

parquet_files = list(output_dir.rglob("*.parquet"))
total_bytes = sum(path.stat().st_size for path in parquet_files)

print("Parquet file count:",len(parquet_files))
print(f"Total size (MB): {round(total_bytes/(1024**2),2):.2f}")

for file in output_dir.rglob("*.parquet"):
    metadata = pq.read_metadata(file)

    print(
        file.name,
        "Rows:", metadata.num_rows,
        "Size (MB):", round(file.stat().st_size / 1024**2, 2),
    )
