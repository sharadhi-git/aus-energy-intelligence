
import pytest
import pyarrow.parquet as pq
import energy_platform.ingestion.parquet_writer as parquet_writer

def test_write_parquet(tmp_path):
    columns = ["REGIONID", "TOTALDEMAND"]
    rows = [
        ["VIC1", "4010.89"],
        ["NSW1", "6098.34"],
        ["QLD1", ""],
    ]
    output_path = tmp_path / "test_regionsum.parquet"
    parquet_writer.write_parquet(columns, rows, output_path)
    table = pq.read_table(output_path)

    assert table.num_rows == 3
    assert table.column_names == columns
    assert table.to_pydict() == {
        "REGIONID": ["VIC1", "NSW1", "QLD1"],
        "TOTALDEMAND": ["4010.89", "6098.34", ""],
    }


def test_failed_write_preserves_existing_file(tmp_path, monkeypatch):
    output_path = tmp_path / "regionsum.parquet"

    # First, write a valid Parquet file
    parquet_writer.write_parquet(
        ["REGIONID", "TOTALDEMAND"],
        [["VIC1", "4010.89"]],
        output_path,
    )

    # Simulate a failure when PyArrow writes the replacement
    def fail_write(*args, **kwargs):
        raise OSError("Simulated disk write failure")

    monkeypatch.setattr(parquet_writer.pq, "write_table", fail_write)

    # The second write should fail
    with pytest.raises(OSError, match="Simulated disk write failure"):
        parquet_writer.write_parquet(
            ["REGIONID", "TOTALDEMAND"],
            [["VIC1", "5000.00"]],
            output_path,
        )

    # The original file should remain unchanged
    original = pq.read_table(output_path)

    assert original.to_pydict()["TOTALDEMAND"] == ["4010.89"]

    # No temporary files should remain
    assert not list(tmp_path.glob("*.parquet.tmp"))