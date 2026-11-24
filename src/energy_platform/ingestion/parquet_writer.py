"""
File        : parquet_writer.py
Project     : aus energy intelligence 
Description : perform the parquet file creation

Author      : Sharadhi Gunathilake
Created     : 2026-11-23
Version     : 1.0
"""
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

def write_parquet(
        columns:list[str],
        rows:list[list[str]],
        output_path: str|Path
)-> None:
    #check for duplicate col names
    if len(columns) != len(set(columns)):
        raise ValueError("Duplicate column names detected!")
    for row in rows:
        if len(row) != len(columns):
            raise ValueError("Row length doesnt match to col count")

    #convert row based data to col-based data
    column_data = {
        column :[row[index] for row in rows]
        for index, column in enumerate(columns)
    }

    #create schema
    schema = pa.schema([
        pa.field(column, pa.string())
        for column in columns
    ])
    #create PyArrow table
    table = pa.table(column_data, schema=schema)

    #create output path/directory
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    #wirte compress Parquet
    pq.write_table(table,output_path,compression="snappy")
    