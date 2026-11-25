"""
File        : archive_reader.py
Project     : aus enregy intelligence 
Description : Read csv data fiels inside zip folders

Author      : Sharadhi Gunathilake
Created     : 2026-11-23
Version     : 1.0
"""

from dataclasses import dataclass

@dataclass
class ArchiveProcessingResult:
    files_processed: int
    files_with_errors: int

from pathlib import Path
from zipfile import ZipFile
from io import BytesIO, TextIOWrapper
from energy_platform.ingestion.aemo_parser import (parse_aemo_csv,validate_aemo_records,TableKey)

def process_daily_archive(archive_path:str|Path)->None:
    files_processed = 0
    files_with_errors = 0
    with ZipFile(archive_path) as archive:
        for filename in archive.namelist():
            if not filename.lower().endswith(".zip"):
                continue
            with ZipFile(BytesIO(archive.read(filename))) as nested_archive:
                for csv_filename in nested_archive.namelist():
                    if not csv_filename.lower().endswith(".csv"):
                        continue
                    with nested_archive.open(csv_filename) as csv_file:
                        with TextIOWrapper(csv_file, encoding="utf-8", newline="") as text_file:
                            records = parse_aemo_csv(text_file)
        
                    result = validate_aemo_records(records)
                    files_processed += 1
                    if (
                        sum(result.malformed_records.values()) > 0
                        or sum(result.missing_schemas.values()) > 0
                        or sum(result.schema_mismatches.values()) > 0
                    ):
                        files_with_errors += 1 

    return ArchiveProcessingResult(
        files_processed=files_processed,
        files_with_errors=files_with_errors,
    )

