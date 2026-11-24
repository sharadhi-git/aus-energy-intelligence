"""
File        : daily_ingestion.py
Project     : aus enregy intelligence
Description : create ingestion from raw zip files till parquet file landing

Author      : Sharadhi Gunathilake
Created     : 2026-11-24
Version     : 1.0

"""
from pathlib import Path
from zipfile import ZipFile
from io import BytesIO, TextIOWrapper
from energy_platform.ingestion.aemo_parser import (parse_aemo_csv,validate_aemo_records,TableKey)
from energy_platform.ingestion.profile_aemo import extract_table
from energy_platform.ingestion.parquet_writer import write_parquet

def ingest_dispatch_records(
        records:list[list[str]],
        output_dir:Path,
        source_id:str,
        table_keys: list[TableKey],
)->None:
    result = validate_aemo_records(records)
    if (
        sum(result.malformed_records.values()) > 0
        or sum(result.missing_schemas.values()) > 0
        or sum(result.schema_mismatches.values()) > 0
    ):
        raise ValueError("AEMO sturucutral validation failed")

    #extract and write each table
    for table_key in table_keys:
        if table_key not in result.schemas:
            raise ValueError(f"Missing required table: {table_key}")
        columns,rows = extract_table(records,table_key)
        output_path = (output_dir / table_key[0].lower() / table_key[1].lower() / f"v{table_key[2]}" / f"{source_id}.parquet")
        write_parquet(columns,rows,output_path)

def ingest_daily_archive(
        archive_path: str | Path,
        output_dir:Path,
        table_keys:list[TableKey]
)-> None:
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
                                source_id = Path(csv_filename).stem.split("_")[2]
                                ingest_dispatch_records(records=records, output_dir=output_dir, source_id=source_id, table_keys=table_keys )
                                   
                                
                            
        