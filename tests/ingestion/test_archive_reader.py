from io import BytesIO
from zipfile import ZipFile
from energy_platform.ingestion.archive_reader import process_daily_archive

def test_process_daily_archive(tmp_path):
    # Create a sample AEMO CSV
    csv_content = (
        "I,DISPATCH,REGIONSUM,9,REGIONID,TOTALDEMAND\n"
        "D,DISPATCH,REGIONSUM,9,VIC1,4010.89\n"
    )

    inner_buffer = BytesIO()
    with ZipFile(inner_buffer, "w") as inner_zip:
        inner_zip.writestr("dispatch.csv", csv_content)

    archive_path = tmp_path / "daily.zip"
    with ZipFile(archive_path, "w") as outer_zip:
        outer_zip.writestr("dispatch_001.zip", inner_buffer.getvalue())

    result = process_daily_archive(archive_path)

    assert result.files_processed == 1
    assert result.files_with_errors == 0
