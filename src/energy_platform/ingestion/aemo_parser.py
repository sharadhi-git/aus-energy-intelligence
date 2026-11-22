"""
File        : aemo_parser.py
Project     : aus enregy intelligence
Description : create the parser fiel to read records from csv files

Author      : Sharadhi Gunathilake
Created     : 2026-11-20
Version     : 1.0

"""

import csv
from dataclasses import dataclass
from pathlib import Path

#Type aliases
TableKey = tuple[str, str, str]

#data models for validation
@dataclass
class ValidationResult:
    schemas: dict[TableKey, list[str]]
    malformed_records: dict[str, int]
    record_counts: dict[TableKey, int]
    missing_schemas: dict[TableKey, int]
    schema_mismatches: dict[TableKey, int]

def read_aemo_file(file_path: str | Path) -> list[list[str]]:
    records = []
    with open(file_path, "r", newline="", encoding="utf-8") as file:
        reader = csv.reader(file)
        for line in reader:
            records.append(line)
    return records

def validate_aemo_records(records: list[list[str]])-> ValidationResult:
    schemas = {} # here schemas stand for col names in each table
    missing_schemas = {}
    malformed_records  = {}
    schema_mismatches  = {}
    record_counts = {}
    for line in records:
        if not line:
            continue
        if line[0] in ("I", "D") and len(line) < 4:
            record_type = line[0]
            malformed_records[record_type] = malformed_records.get(record_type, 0) + 1
            continue
        if line[0] =="I":
            table_key= tuple(line[1:4])
            columns = line[4:]
            schemas[table_key] = columns 

        if line[0] == "D":
            table_key = tuple(line[1:4])
            if table_key not in schemas:
                missing_schemas[table_key] = missing_schemas.get(table_key,0)+1
            else:
                expected_columns = len(schemas[table_key])
                actual_columns = len(line[4:])
                if expected_columns != actual_columns:
                    schema_mismatches[table_key]  = schema_mismatches.get(table_key,0)+1
            
            record_counts[table_key] = record_counts.get(table_key,0)+1

    return ValidationResult(
        schemas=schemas,
        record_counts=record_counts,
        missing_schemas=missing_schemas,
        schema_mismatches=schema_mismatches,
        malformed_records=malformed_records
    )