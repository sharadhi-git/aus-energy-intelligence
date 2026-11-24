import pyarrow.parquet as pq
from energy_platform.ingestion.parquet_writer import write_parquet

def test_write_parquet(tmp_path):
    columns = ["REGIONID", "TOTALDEMAND"]
    rows = [
        ["VIC1", "4010.89"],
        ["NSW1", "6098.34"],
        ["QLD1", ""],
    ]
    output_path = tmp_path / "test_regionsum.parquet"
    write_parquet(columns, rows, output_path)
    table = pq.read_table(output_path)

    assert table.num_rows == 3
    assert table.column_names == columns
    assert table.to_pydict() == {
        "REGIONID": ["VIC1", "NSW1", "QLD1"],
        "TOTALDEMAND": ["4010.89", "6098.34", ""],
    }