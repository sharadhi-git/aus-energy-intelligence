from io import BytesIO
from zipfile import ZipFile
import pyarrow.parquet as pq
from energy_platform.ingestion.daily_ingestion import ingest_dispatch_records, ingest_daily_archive

def test_ingest_dispatch_records(tmp_path):
    records = [
        ["I", "DISPATCH", "REGIONSUM", "9","REGIONID", "TOTALDEMAND"],
        ["D", "DISPATCH", "REGIONSUM", "9","VIC1", "4010.89"],
        ["I", "DISPATCH", "PRICE", "5", "REGIONID", "RRP"],
        ["D", "DISPATCH", "PRICE", "5", "VIC1", "35.50"],
    ]

    table_keys = [
        ("DISPATCH", "REGIONSUM", "9"),
        ("DISPATCH", "PRICE", "5"),
    ]

    ingest_dispatch_records(
        records=records,
        output_dir=tmp_path,
        source_id="202611140005",
        table_keys=table_keys,
    )

    regionsum_path = (tmp_path / "dispatch" / "regionsum" / "v9"/ "202611140005.parquet")
    price_path = (tmp_path / "dispatch" / "price" / "v5"/ "202611140005.parquet")

    assert regionsum_path.exists()
    assert price_path.exists()
    regionsum = pq.read_table(regionsum_path)
    price = pq.read_table(price_path)
    assert regionsum.to_pydict() == {"REGIONID": ["VIC1"],"TOTALDEMAND": ["4010.89"]}
    assert price.to_pydict() == {"REGIONID": ["VIC1"],"RRP": ["35.50"]}

def test_ingest_daily_archive(tmp_path):
    table_keys = [
        ("DISPATCH", "REGIONSUM", "9"),
        ("DISPATCH", "PRICE", "5"),
    ]
    archive_path = tmp_path / "daily.zip"
    
    #create zip files structure at temp location
    with ZipFile(archive_path, "w") as daily_zip:
        for timestamp in ["202611140005", "202611140010"]:
            csv_content = (
                "I,DISPATCH,REGIONSUM,9,REGIONID,TOTALDEMAND\n"
                f"D,DISPATCH,REGIONSUM,9,VIC1,{timestamp}\n"
                "I,DISPATCH,PRICE,5,REGIONID,RRP\n"
                "D,DISPATCH,PRICE,5,VIC1,35.50\n"
            )
            inner_buffer = BytesIO()
            with ZipFile(inner_buffer, "w") as inner_zip:
                inner_zip.writestr(f"PUBLIC_DISPATCHIS_{timestamp}_123.CSV",csv_content)
            daily_zip.writestr(f"PUBLIC_DISPATCHIS_{timestamp}_123.zip",inner_buffer.getvalue())
    
    ingest_daily_archive(archive_path, tmp_path, table_keys)

    # Assert: two tables x two intervals = four files
    for timestamp in ["202611140005", "202611140010"]:
        regionsum_path = (tmp_path / "dispatch" / "regionsum" / "v9"/ f"{timestamp}.parquet")
        price_path = (tmp_path / "dispatch" / "price" / "v5"/ f"{timestamp}.parquet")

        assert regionsum_path.exists()
        assert price_path.exists()
        regionsum = pq.read_table(regionsum_path)
        assert regionsum.to_pydict()["TOTALDEMAND"] == [timestamp]
    assert len(list(tmp_path.rglob("*.parquet"))) == 4
