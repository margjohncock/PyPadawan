
import ast
from pathlib import Path


def inspect_project(project_dir):
    root = Path(project_dir)

    # Find Python files
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

    # Find all pyproject.toml files
    pyproject_files = sorted(
        file for file in root.rglob("pyproject.toml")
        if file.is_file()
    )

    # Find all .gitignore files
    gitignore_files = sorted(
        file for file in root.rglob(".gitignore")
        if file.is_file()
    )

    # Find all test directories
    test_directories = sorted(
        directory for directory in root.rglob("tests")
        if directory.is_dir()
    )

    # Find GitHub Actions workflows
    ci_files = sorted(
        file
        for file in root.rglob("*")
        if (
            file.is_file()
            and file.suffix in (".yml", ".yaml")
            and file.parent.name == "workflows"
            and file.parent.parent.name == ".github"
        )
    )

    # Convert paths to relative paths
    def relative_paths(paths):
        return [
            str(path.relative_to(root))
            for path in paths
        ]

    return {
        "python_files": relative_paths(python_files),
        "imports": sorted(imports),

        # Root-level configuration checks
        "has_pyproject": (root / "pyproject.toml").is_file(),
        "has_gitignore": (root / ".gitignore").is_file(),
        "has_tests": (root / "tests").is_dir(),
        "has_ci": (
            root / ".github" / "workflows"
        ).is_dir() and any(
            file.parent == root / ".github" / "workflows"
            for file in ci_files
        ),

        # All discovered locations
        "pyproject_files": relative_paths(pyproject_files),
        "gitignore_files": relative_paths(gitignore_files),
        "test_directories": relative_paths(test_directories),
        "ci_files": relative_paths(ci_files),

        "errors": errors,
    }
