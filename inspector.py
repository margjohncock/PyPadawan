import ast
from pathlib import Path


def inspect_project(project_dir):
    root = Path(project_dir)

    python_files = sorted(root.rglob("*.py"))
    imports = set()
    errors = []

    for file in python_files:
        try:
            source = file.read_text(encoding="utf-8")
            tree = ast.parse(source)

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name.split(".")[0])

                elif isinstance(node, ast.ImportFrom):
                    if node.level == 0 and node.module:
                        imports.add(node.module.split(".")[0])

        except (SyntaxError, UnicodeError, OSError) as error:
            errors.append(f"{file.name}: {error}")

    return {
        "python_files": [
            str(file.relative_to(root))
            for file in python_files
        ],
        "imports": sorted(imports),
        "has_pyproject": (root / "pyproject.toml").is_file(),
        "has_gitignore": (root / ".gitignore").is_file(),
        "has_tests": (root / "tests").is_dir(),
        "has_ci": any(
            (root / ".github" / "workflows").glob("*.yml")
        ) or any(
            (root / ".github" / "workflows").glob("*.yaml")
        ),
        "errors": errors,
    }
