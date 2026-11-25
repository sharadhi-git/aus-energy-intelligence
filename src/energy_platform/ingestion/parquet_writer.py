"""
File        : parquet_writer.py
Project     : aus energy intelligence 
Description : perform the parquet file creation

Author      : Sharadhi Gunathilake
Created     : 2026-11-23
Version     : 1.0
"""
import os
import tempfile
import pyarrow as pa
import pyarrow.parquet as pq
from pathlib import Path

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

    temp_path = None
    try:
        # 4. Create a temporary file in the same directory
        with tempfile.NamedTemporaryFile(
            suffix=".parquet.tmp",
            dir=output_path.parent,
            delete=False,
        ) as temp_file:
            temp_path = Path(temp_file.name)

        # 5. Write Parquet data to the temporary file
        pq.write_table(
            table,
            temp_path,
            compression="snappy",
        )

        # 6. Replace the destination only after successful writing
        os.replace(temp_path, output_path)

    finally:
        # 7. Remove any leftover temporary file
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
