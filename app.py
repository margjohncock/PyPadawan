import io
import tempfile
import zipfile
from pathlib import Path

import streamlit as st

from inspector import inspect_project

from gitignore_generator import (
    GITIGNORE_TEMPLATES,
    generate_gitignore,
)

st.title("PyPadawan")
st.write(
    "Upload a Python project to see its structure "
    "and existing software engineering configuration."
)

uploaded = st.file_uploader(
    "Upload your Python project as a ZIP",
    type=["zip"],
)

if uploaded is not None:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)

        with zipfile.ZipFile(io.BytesIO(uploaded.getvalue())) as archive:
            files = archive.infolist()

            # Basic safeguards for this first local prototype.
            if len(files) > 200:
                st.error("Too many files in this archive.")
                st.stop()

            if sum(f.file_size for f in files) > 10_000_000:
                st.error("Archive is too large when extracted.")
                st.stop()

            for entry in files:
                path = Path(entry.filename)

                if (
                    path.is_absolute()
                    or ".." in path.parts
                    or "\\" in entry.filename
                    or entry.is_dir() and entry.filename == ""
                ):
                    st.error("Archive contains an unsafe path.")
                    st.stop()

                # Reject Unix symbolic links.
                if (entry.external_attr >> 16) & 0o170000 == 0o120000:
                    st.error("Symbolic links are not supported.")
                    st.stop()

            for entry in files:
                if entry.is_dir():
                    continue

                target = root / entry.filename
                target.parent.mkdir(parents=True, exist_ok=True)

                with archive.open(entry) as source:
                    with target.open("wb") as destination:
                        import shutil
                        shutil.copyfileobj(source, destination)

        result = inspect_project(project_root)

        st.write("DEBUG: Project root:", project_root)
        st.write("DEBUG: All gitignore files:", result["gitignore_files"])
        st.write("DEBUG: Root gitignore:", result["has_gitignore"])

        st.subheader("Project inspection results")

        st.write("Python files:")
        st.write(result["python_files"])

        st.write("Detected imports:")
        st.write(result["imports"])

        st.subheader("Project configuration")

        checks = {
            "pyproject.toml": result["has_pyproject"],
            ".gitignore": result["has_gitignore"],
            "Tests directory": result["has_tests"],
            "GitHub Actions": result["has_ci"],
        }

        for name, exists in checks.items():
            if exists:
                st.success(f"{name}: Found")
            else:
                st.warning(f"{name}: Not found")

        if result["errors"]:
            st.subheader("Inspection warnings")
            st.write(result["errors"])

st.divider()

st.header("Generate a .gitignore")

st.write(
    "Choose which tools your project uses. "
    "PyPadawan will generate a .gitignore file "
    "containing the appropriate patterns."
)

selected_options = st.multiselect(
    "Select tools and environments",
    options=list(GITIGNORE_TEMPLATES.keys()),
    default=[
        "Python",
        "Virtual environments",
        "pytest",
    ],
)

gitignore_content = generate_gitignore(selected_options)

st.subheader("Preview")

st.code(
    gitignore_content or "# No options selected",
    language="text",
)

st.download_button(
    label="Download .gitignore",
    data=gitignore_content,
    file_name=".gitignore",
    mime="text/plain",
    disabled=not gitignore_content,
)
