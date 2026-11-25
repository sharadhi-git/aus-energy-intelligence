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
from dataclasses import dataclass
from datetime import datetime, timedelta
from energy_platform.ingestion.aemo_parser import (parse_aemo_csv,validate_aemo_records,TableKey)
from energy_platform.ingestion.profile_aemo import extract_table
from energy_platform.ingestion.parquet_writer import write_parquet
from energy_platform.ingestion.ingestion_manifest import (IngestionManifest, save_manifest,)

@dataclass
class DailyIngestResult:
    reporting_date: str
    source_files_processed: int
    parquet_files_written:int
    total_rows_written : int

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
)-> DailyIngestResult:
    #create empty dict for daily_data with table key and (col and rows)
    daily_data:dict[TableKey,list[list[str]]]={table_key:[] for table_key in table_keys}
    #create schema dict to store column names for each table_key
    daily_schemas:dict[TableKey,list[str]] = {}
    source_files_processed = 0
    archive_date = None
    with ZipFile(archive_path) as archive:
        for filename in archive.namelist():
            if not filename.lower().endswith(".zip"):
                continue
            with ZipFile(BytesIO(archive.read(filename))) as nested_archive:
                    for csv_filename in nested_archive.namelist():
                        if not csv_filename.lower().endswith(".csv"):
                            continue
                        source_id = Path(csv_filename).stem.split("_")[2]
                        if len(source_id) != 12 or not source_id.isdigit():
                            raise ValueError(f"Invalid dispatch source ID: {source_id}")
                        dispatch_time = datetime.strptime(source_id, "%Y%m%d%H%M")
                        dispatch_date = dispatch_time.date()
                        if dispatch_time.hour == 0 and dispatch_time.minute == 0:
                            dispatch_date -= timedelta(days=1)
                        if archive_date is None:
                            archive_date = dispatch_date
                        elif archive_date != dispatch_date:
                            print("Archive date:", archive_date)
                            print("Different date found:", dispatch_date)
                            print("CSV filename:", csv_filename)
                            raise ValueError("Multiple dispatch dates found in daily archive")

                        with nested_archive.open(csv_filename) as csv_file:
                            with TextIOWrapper(csv_file, encoding="utf-8", newline="") as text_file:
                                records = parse_aemo_csv(text_file)
                                result = validate_aemo_records(records)
                                if (
                                        sum(result.malformed_records.values()) > 0
                                        or sum(result.missing_schemas.values()) > 0
                                        or sum(result.schema_mismatches.values()) > 0
                                    ):
                                        raise ValueError("AEMO sturucutral validation failed")
                                for table_key in table_keys:
                                    if table_key not in result.schemas:
                                        raise ValueError(f"Missing required table: {table_key}")
                                    columns,rows = extract_table(records,table_key)
                                    if  table_key not in daily_schemas :
                                        daily_schemas[table_key] = columns
                                    elif daily_schemas[table_key] != columns:
                                        raise ValueError(f"Schema mismatch for {table_key}")
                                    daily_data[table_key].extend(rows)
                                source_files_processed +=1
    
    # Write Parquet AFTER processing all nested ZIPs                   
    if archive_date is None:
        raise ValueError("No dispatch CSV files found")
    for table_key in table_keys: 
        columns = daily_schemas[table_key]
        rows = daily_data[table_key]
        output_path = (output_dir / table_key[0].lower() / table_key[1].lower() / f"v{table_key[2]}" / f"{archive_date.isoformat()}.parquet")
        write_parquet(columns,rows,output_path)

    return DailyIngestResult(
    reporting_date=archive_date.isoformat(),
    source_files_processed=source_files_processed,
    parquet_files_written=len(table_keys),
    total_rows_written=sum(len(rows) for rows in daily_data.values())
    )                           

def run_daily_ingestion(
    archive_path: str | Path,
    output_dir: Path,
    manifest_dir: Path,
    table_keys: list[TableKey],
) -> DailyIngestResult:

    # Process the daily archive
    result = ingest_daily_archive(
        archive_path=archive_path,
        output_dir=output_dir,
        table_keys=table_keys,
    )

    # Derive the reporting date from the generated daily output
    daily_files = list(output_dir.rglob("????-??-??.parquet"))
    if not daily_files:
        raise ValueError("No daily Parquet files were generated")
    reporting_date = result.reporting_date

    # Build the manifest
    manifest = IngestionManifest(
        source_archive=Path(archive_path).name,
        reporting_date=reporting_date,
        source_files_processed=result.source_files_processed,
        parquet_files_written=result.parquet_files_written,
        total_rows_written=result.total_rows_written,
        status="success",
    )

    # Save the manifest
    manifest_path = manifest_dir / f"{reporting_date}.json"
    save_manifest(manifest, manifest_path)

    return result                        
                            
        