"""
File        : ingestion_manifest.py
Project     : aus enregy intelligence 
Description : create the JSON record for a compeleted archieve to parquet landing

Author      : Sharadhi Gunathilake
Created     : 2026-11-25
Version     : 1.0
"""
import json
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class IngestionManifest:
    source_archive: str
    reporting_date: str
    source_files_processed: int
    parquet_files_written: int
    total_rows_written: int
    status: str

def save_manifest(
    manifest: IngestionManifest,
    output_path: str | Path,
) -> None:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(asdict(manifest), file, indent=2)

    