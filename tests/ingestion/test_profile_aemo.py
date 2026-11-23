import pytest
from energy_platform.ingestion.profile_aemo import extract_table, profile_missing_values,profile_duplicate_keys,validate_timestamps

def test_extract_regionsum_table():
    records = [
        ["I", "DISPATCH", "REGIONSUM", "9","SETTLEMENTDATE", "REGIONID", "TOTALDEMAND"],
        ["D", "DISPATCH", "REGIONSUM", "9","2026/11/14 13:00:00", "VIC1", "4010.89"],
        ["D", "DISPATCH", "REGIONSUM", "9","2026/11/14 13:00:00", "NSW1", "6098.34"],
        ["I", "DISPATCH", "PRICE", "5","SETTLEMENTDATE", "REGIONID", "RRP"],
        ["D", "DISPATCH", "PRICE", "5","2026/11/14 13:00:00", "VIC1", "1.15"],
    ]

    columns, rows = extract_table(records,("DISPATCH", "REGIONSUM", "9"))

    assert len(columns) == 3
    assert len(rows) == 2
    assert columns == ["SETTLEMENTDATE", "REGIONID", "TOTALDEMAND"]
    assert rows[0][1] == "VIC1"
    assert rows[1][1] == "NSW1"

def test_profile_missing_values():
    columns = ["REGIONID", "TOTALDEMAND", "AVAILABLELOAD"]
    rows = [["VIC1", "4010.89", ""],["NSW1", "6098.34", "1914"],["QLD1", "", ""]]
    result = profile_missing_values(columns, rows)

    assert result.total_rows == 3
    assert result.missing_counts == {"REGIONID": 0,"TOTALDEMAND": 1,"AVAILABLELOAD": 2}

def test_profile_duplicate_columns():
    columns = ["REGIONID", "TOTALDEMAND", "TOTALDEMAND"]
    rows = [["VIC1", "4010.89", "4020.50"]]
    with pytest.raises(ValueError):
        profile_missing_values(columns, rows)

def test_profile_mismatched_row_lengths():
    columns = ["REGIONID", "TOTALDEMAND", "AVAILABLELOAD"]
    rows = [["VIC1", "4010.89", ""],["NSW1", "6098.34"]]
    with pytest.raises(ValueError):
        profile_missing_values(columns, rows)

def test_profile_empty_table():
    columns = ["REGIONID", "TOTALDEMAND"]
    rows = []
    result = profile_missing_values(columns, rows)
    assert result.total_rows == 0
    assert result.missing_counts == {"REGIONID": 0,"TOTALDEMAND": 0}

def test_profile_duplicate_keys():
    columns = ["SETTLEMENTDATE", "REGIONID", "RUNNO"]
    rows = [
        ["2026/11/14 13:00:00", "VIC1", "1"],
        ["2026/11/14 13:00:00", "NSW1", "1"],
        ["2026/11/14 13:00:00", "VIC1", "1"],
    ]

    result = profile_duplicate_keys(
        columns,
        rows,
        ["SETTLEMENTDATE", "REGIONID", "RUNNO"],
    )
    assert result.total_rows == 3
    assert result.unique_keys == 2
    assert result.duplicate_rows == 1

def test_validate_timestamps():
    columns = ["SETTLEMENTDATE", "REGIONID"]
    rows = [
        ["2026/11/14 13:00:00", "VIC1"],
        ["2026/11/14 13:05:00", "NSW1"],
        ["invalid-date", "QLD1"],
        ["", "SA1"],
    ]
    result = validate_timestamps(
        columns,
        rows,
        "SETTLEMENTDATE",
    )
    assert result == 2