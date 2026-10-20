from inspector import inspect_project


def test_detects_python_files_and_imports(tmp_path):
    script = tmp_path / "analysis.py"
    script.write_text(
        "import pandas\nfrom pathlib import Path\n",
        encoding="utf-8",
    )

    result = inspect_project(tmp_path)

    assert result["python_files"] == ["analysis.py"]
    assert "pandas" in result["imports"]
    assert "pathlib" in result["imports"]
    assert result["has_pyproject"] is False


def test_detects_existing_configuration(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname = 'example'\n",
        encoding="utf-8",
    )
    (tmp_path / "tests").mkdir()

    result = inspect_project(tmp_path)

    assert result["has_pyproject"] is True
    assert result["has_tests"] is True
