from energy_platform.ingestion.aemo_parser import read_aemo_file, validate_aemo_records


def test_read_aemo_file(tmp_path):
    csv_file = tmp_path / "test_invalid_dispatch.csv"
    csv_file.write_text(
        "I,DISPATCH,REGIONSUM,9,SETTLEMENTDATE,REGIONID,TOTALDEMAND\n"
        'D,DISPATCH,REGIONSUM,9,"2026/11/14 13:00:00",VIC1,4010.89\n'
        'D,DISPATCH,REGIONSUM,9,"2026/11/14 13:00:00",NSW1,\n',
        encoding="utf-8",
    )
    first_read = read_aemo_file(csv_file)
    second_read = read_aemo_file(csv_file)
    assert len(first_read) == 3
    assert len(second_read) == 3
    assert first_read == second_read
    assert first_read is not second_read

def test_valid_aemo_records():
    records = [
        ["I","DISPATCH","REGIONSUM","9","SETTLEMENTDATE","REGIONID","TOTALDEMAND"],
        ["D","DISPATCH","REGIONSUM","9","2026/11/14 13:00:00","VIC1","4010.89"],
        ["D", "DISPATCH","REGIONSUM","9","2026/11/14 13:00:00","NSW1","6098.34",]
    ]

    validation_results = validate_aemo_records(records)
    table_key = ("DISPATCH", "REGIONSUM", "9")
    assert validation_results.record_counts[table_key] == 2
    assert validation_results.schemas[table_key] == ["SETTLEMENTDATE","REGIONID","TOTALDEMAND",]
    assert sum(validation_results.missing_schemas.values()) == 0
    assert sum(validation_results.schema_mismatches.values()) == 0
    assert sum(validation_results.malformed_records.values()) == 0


def test_missing_schema():
    records = [
        ["I", "DISPATCH", "REGIONSUM", "9","SETTLEMENTDATE", "REGIONID", "TOTALDEMAND"],
        ["D", "DISPATCH", "REGIONSUM", "9","2026/11/14 13:00:00", "VIC1", "4010.89",],
        ["D", "DISPATCH", "UNKNOWN_TABLE", "1","2026/11/14 13:00:00", "NSW1", "6098.34",],
    ]
    result = validate_aemo_records(records)
    missing_key = ("DISPATCH", "UNKNOWN_TABLE", "1")

    assert result.missing_schemas[missing_key] == 1
    assert sum(result.record_counts.values()) == 2
    assert sum(result.schema_mismatches.values()) == 0
    assert sum(result.malformed_records.values()) == 0

def test_schema_field_count_mismatch():
    records = [
        ["I", "DISPATCH", "REGIONSUM", "9","SETTLEMENTDATE", "REGIONID", "TOTALDEMAND",],
        ["D", "DISPATCH", "REGIONSUM", "9","2026/11/14 13:00:00", "VIC1",],
        ["D", "DISPATCH", "REGIONSUM", "9","2026/11/14 13:00:00", "VIC1","300","45"],
    ]
    result = validate_aemo_records(records)
    table_key = ("DISPATCH", "REGIONSUM", "9")

    assert result.schema_mismatches[table_key] == 2
    assert result.record_counts[table_key] == 2
    assert sum(result.missing_schemas.values()) == 0
    assert sum(result.malformed_records.values()) == 0

def test_malformed_records():
    # Arrange
    records = [
        ["I", "DISPATCH", "REGIONSUM", "9","SETTLEMENTDATE", "REGIONID", "TOTALDEMAND"],
        ["D", "DISPATCH"],  # Incomplete data record
        ["I", "DISPATCH"],  # Incomplete schema record
        ["D", "DISPATCH", "REGIONSUM", "9","2026/11/14 13:00:00", "VIC1", "4010.89"]]
    result = validate_aemo_records(records)
    assert result.malformed_records["D"] == 1
    assert result.malformed_records["I"] == 1
    assert sum(result.missing_schemas.values()) == 0
    assert sum(result.schema_mismatches.values()) == 0
    assert sum(result.record_counts.values()) == 1