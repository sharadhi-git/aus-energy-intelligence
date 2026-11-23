"""
File        : explore_aemo.py
Project     : aus enregy intelligence
Description : create the parser to read the csv file

Author      : Sharadhi Gunathilake
Created     : 2026-11-16
Version     : 1.0

"""
from pathlib import Path
from energy_platform.ingestion.aemo_parser import read_aemo_file, validate_aemo_records
from energy_platform.ingestion.profile_aemo import extract_table,profile_missing_values,profile_duplicate_keys,validate_timestamps


PROJECT_ROOT = Path(__file__).resolve().parents[3]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
file_path = RAW_DATA_DIR / "PUBLIC_DISPATCHIS_202611141300_0000000548525946.CSV"
#PUBLIC_DISPATCHIS_202611141300_0000000548525946.CSV
records=read_aemo_file(file_path)
validation_results = validate_aemo_records(records)
print("\nTable schemas:")
for table_key, columns in validation_results.schemas.items():
    print(f"{table_key[1]}: {len(columns)} columns")

print("\n data record counts")
for table_key, count in validation_results.record_counts.items():
    print(f"{table_key}:{count} records")  

print(f"total data records ={sum(validation_results.record_counts.values())}")
print(f"Total malformed records = {sum(validation_results.malformed_records.values())}")
print(f"total_missing_schemas = {sum(validation_results.missing_schemas.values())}") 
print(f"total_mismatched_schemas = {sum(validation_results.schema_mismatches.values())}") 

columns, rows = extract_table(records,("DISPATCH", "REGIONSUM", "9"))
print("Number of columns in the REGIONSUM TABLE:", len(columns))
print("Number of rows in the REGIONSUM TABLE:", len(rows))
print("First five columns in the REGIONSUM TABLE:", columns[:5])
    
region_sum_missing_value_results=profile_missing_values(columns,rows)
print("Number of rows in the REGIONSUM TABLE:",region_sum_missing_value_results.total_rows)
print("Missing value count\n")
for column, count in region_sum_missing_value_results.missing_counts.items():
    if count > 0:
        print(f"{column}: {count} missing values")

key_columns = [
    "SETTLEMENTDATE",
    "REGIONID",
    "RUNNO",
    "INTERVENTION",
]
result = profile_duplicate_keys(columns, rows, key_columns)
print("Total rows in the REGIONSUM TABLE:", result.total_rows)
print("Unique keys in the REGIONSUM TABLE:", result.unique_keys)
print("Duplicate rows in the REGIONSUM TABLE:", result.duplicate_rows)

invalid_timestamps = validate_timestamps(
    columns,
    rows,
    "SETTLEMENTDATE",
)
print("Invalid timestamps in the REGIONSUM TABLE:", invalid_timestamps)