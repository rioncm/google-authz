from pathlib import Path


def test_readme_present():
    assert Path("README.md").is_file(), "README.md should exist at repo root"
