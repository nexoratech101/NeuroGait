from pathlib import Path

from app.pipeline.file_validator import validate_file

FIXTURE = Path(__file__).parent / "fixtures" / "session_20260813_111730.csv"


def test_valid_fixture_passes():
    result = validate_file(str(FIXTURE))
    assert result.valid
    assert result.errors == []
    assert result.n_rows > 1000


def test_missing_columns_rejected(tmp_path):
    bad_file = tmp_path / "bad.csv"
    bad_file.write_text("timestamp_ms,accel_x\n1,0.1\n2,0.2\n")
    result = validate_file(str(bad_file))
    assert not result.valid
    assert any("Missing required columns" in e for e in result.errors)


def test_empty_file_rejected(tmp_path):
    empty_file = tmp_path / "empty.csv"
    empty_file.write_text("timestamp_ms,accel_x,accel_y,accel_z,gyro_x,gyro_y,gyro_z\n")
    result = validate_file(str(empty_file))
    assert not result.valid


def test_unparseable_file_rejected(tmp_path):
    junk = tmp_path / "junk.csv"
    junk.write_bytes(b"\x00\x01\x02not,a,csv\xff\xfe")
    result = validate_file(str(junk))
    assert not result.valid
