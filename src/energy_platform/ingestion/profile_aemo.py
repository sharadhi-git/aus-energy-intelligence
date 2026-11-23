"""
File        : profile_aemo.py
Project     : aus enregy intelligence 
Description : data profiling from the raw data

Author      : Sharadhi Gunathilake
Created     : 2026-11-23
Version     : 1.0

"""
from dataclasses import dataclass
from datetime import datetime

@dataclass
class MissingValueProfile:
    total_rows: int
    missing_counts: dict[str, int]

@dataclass
class DuplicateKeyProfile:
    total_rows: int
    unique_keys: int
    duplicate_rows: int

#extract the particular table
def extract_table(
        records: list[list[str]],
        table_key:tuple[str,str,str]
    )->tuple[list[str],list[list[str]]]:
    columns=[]
    rows=[]
    for record in records:
        if len(record) < 4:
            continue
        if tuple(record[1:4]) == table_key:
            if record[0] == "I":
                columns=record[4:]
            if record[0] == "D":
                rows.append(record[4:])

    return columns, rows


#find the missing values from the previously extracted data cols and rows
def profile_missing_values(
        columns:list[str],
        rows:list[list[str]]
    )->MissingValueProfile:

    #check for duplicate col names
    if len(columns) != len(set(columns)):
        raise ValueError("Duplicate column names detected!")
    for row in rows:
        if len(row) != len(columns):
            raise ValueError("Row length doesnt match to col count")
    missing_counts={}
    
    #initialize zero missing count columns (Not considering zero or white space-only strings)
    for column in columns:
        missing_counts[column]=0
    #counting missing values
    for row in rows:
        for index, column in enumerate(columns):
            if row[index] == "":
                missing_counts[column]+=1

    return MissingValueProfile(
        total_rows=len(rows),
        missing_counts=missing_counts
    )

#find the duplicate rows.only counts duplicates. It doesn't delete or modify records. For that, we decide a key->(set of rows deciding the uniqueness)
def profile_duplicate_keys(
        columns:list[str],
        rows:list[list[str]],
        key_columns:list[str],
)->DuplicateKeyProfile:
    if len(columns) != len(set(columns)):
        raise ValueError("Duplicate column names detected!")
    if not key_columns:
        raise ValueError("Key columns cannot be empty")
    if len(key_columns) != len(set(key_columns)):
        raise ValueError("Duplicate key columns detected")
    for column in key_columns:
        if column not in columns:
            raise ValueError(f"{column} is not available in the given columns")
    for row in rows:
            if len(row) != len(columns):
                raise ValueError("Row length doesnt match to col count")

    #find key column positions
    key_indices = [columns.index(column) for column in key_columns]
    seen_keys=set()
    duplicate_count = 0

    for row in rows:
        #create the key for the row based on given key_column
        key = tuple(row[index] for index in key_indices)
        #check whether key alrdy exsit in the seen_keys or not
        if key in seen_keys:
            duplicate_count+=1
        else:
            seen_keys.add(key)

    return DuplicateKeyProfile(
        total_rows=len(rows),
        unique_keys=len(seen_keys),
        duplicate_rows=duplicate_count
    )

#time stamp validation
def validate_timestamps(
        columns:list[str],
        rows:list[list[str]],
        timestamp_col:str
)->int:
    invalid_count=0
    timestamp_index =columns.index(timestamp_col)
    for row in rows:
        timestamp = row[timestamp_index]
        try:
            datetime.strptime(timestamp,"%Y/%m/%d %H:%M:%S")
        except ValueError:
            invalid_count+=1

    return invalid_count