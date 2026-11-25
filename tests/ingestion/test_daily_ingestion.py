import json
from io import BytesIO
from zipfile import ZipFile
import pyarrow.parquet as pq
from energy_platform.ingestion.daily_ingestion import ingest_dispatch_records, ingest_daily_archive, run_daily_ingestion

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
    output_dir=tmp_path / "parquet"
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
    
    result = ingest_daily_archive(archive_path, output_dir, table_keys)

    # Assert: ingestion summary
    assert result.source_files_processed == 2
    assert result.parquet_files_written == 2
    assert result.total_rows_written == 4

    # Assert: daily output files
    regionsum_path = (output_dir / "dispatch" / "regionsum" / "v9"/ "2026-11-14.parquet")
    price_path = (output_dir / "dispatch" / "price" / "v5"/ "2026-11-14.parquet")
    assert regionsum_path.exists()
    assert price_path.exists()

    # Assert: all records are preserved
    regionsum = pq.read_table(regionsum_path)
    price = pq.read_table(price_path)
    assert regionsum.num_rows == 2
    assert price.num_rows == 2
    assert regionsum.to_pydict()["TOTALDEMAND"] == ["202611140005","202611140010"]
    # Verify PRICE records are preserved
    assert price.to_pydict()["RRP"] == ["35.50", "35.50"]

    # Verify exactly two Parquet files were generated
    assert len(list(output_dir.rglob("*.parquet"))) == 2

    second_result = ingest_daily_archive(
        archive_path,
        output_dir,
        table_keys,
    )

    # Verify the second run
    assert second_result.source_files_processed == 2
    assert second_result.parquet_files_written == 2
    assert second_result.total_rows_written == 4

    # Verify that no additional files were created
    assert len(list(output_dir.rglob("*.parquet"))) == 2

    # Verify that records were not duplicated
    regionsum = pq.read_table(regionsum_path)
    price = pq.read_table(price_path)

    assert regionsum.num_rows == 2
    assert price.num_rows == 2

def test_ingest_daily_archive_midnight(tmp_path):
    table_keys = [("DISPATCH", "REGIONSUM", "9")]
    archive_path = tmp_path / "daily.zip"
    output_dir = tmp_path / "parquet"

    with ZipFile(archive_path, "w") as daily_zip:
        for timestamp in ["202611142355", "202611150000"]:
            csv_content = (
                "I,DISPATCH,REGIONSUM,9,REGIONID,TOTALDEMAND\n"
                "D,DISPATCH,REGIONSUM,9,VIC1,4010.89\n"
            )
            inner_buffer = BytesIO()
            with ZipFile(inner_buffer, "w") as inner_zip:
                inner_zip.writestr(f"PUBLIC_DISPATCHIS_{timestamp}_123.CSV",csv_content)
            daily_zip.writestr(f"PUBLIC_DISPATCHIS_{timestamp}_123.zip",inner_buffer.getvalue())
    result = ingest_daily_archive(archive_path, output_dir, table_keys)
    output_path = (output_dir / "dispatch" / "regionsum" / "v9"/ "2026-11-14.parquet")

    assert result.source_files_processed == 2
    assert result.total_rows_written == 2
    assert output_path.exists()
    assert pq.read_metadata(output_path).num_rows == 2

def test_run_daily_ingestion_creates_manifest(tmp_path):
    table_keys = [
        ("DISPATCH", "REGIONSUM", "9"),
        ("DISPATCH", "PRICE", "5"),
    ]
    archive_path = tmp_path / "daily.zip"
    output_dir = tmp_path / "parquet"
    manifest_dir = tmp_path / "manifests"

    # Create synthetic daily archive
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
 
    result = run_daily_ingestion(
        archive_path=archive_path,
        output_dir=output_dir,
        manifest_dir=manifest_dir,
        table_keys=table_keys,
    )

    # Assert: ingestion result
    assert result.reporting_date == "2026-11-14"
    assert result.source_files_processed == 2
    assert result.parquet_files_written == 2
    assert result.total_rows_written == 4

    # Assert: manifest exists
    manifest_path = manifest_dir / "2026-11-14.json"
    assert manifest_path.exists()

    # Read manifest
    with manifest_path.open("r", encoding="utf-8") as file:
        manifest = json.load(file)

    # Assert: manifest contents
    assert manifest == {
        "source_archive": "daily.zip",
        "reporting_date": "2026-11-14",
        "source_files_processed": 2,
        "parquet_files_written": 2,
        "total_rows_written": 4,
        "status": "success",
    }

    # Assert: Parquet files were created
    parquet_files = list(output_dir.rglob("*.parquet"))
    assert len(parquet_files) == 2

    # Assert: correct total number of records
    total_rows = sum(
        pq.read_metadata(path).num_rows
        for path in parquet_files
    )

    assert total_rows == 4


