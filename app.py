"""Streamlit interface for PyPadawan."""
import io
import tempfile
import zipfile
from pathlib import Path

import streamlit as st

from archive_handler import extract_project_zip
from gitignore_generator import GITIGNORE_TEMPLATES, generate_gitignore
from inspector import find_project_root, inspect_project

st.title('PyPadawan')
st.write('Upload a Python project to inspect its structure and configuration.')

uploaded = st.file_uploader('Upload your Python project as a ZIP', type=['zip'])
if uploaded is not None:
    with tempfile.TemporaryDirectory() as temporary:
        extraction_root = Path(temporary)
        try:
            extract_project_zip(io.BytesIO(uploaded.getvalue()), extraction_root)
            project_root = find_project_root(extraction_root)
            result = inspect_project(project_root)
        except (ValueError, zipfile.BadZipFile, OSError) as error:
            st.error(f'Unable to inspect ZIP: {error}')
            st.stop()

        st.subheader('Project inspection results')
        st.caption(f'Project root: {project_root.relative_to(extraction_root).as_posix()}')
        st.write('Python files:', result['python_files'])
        st.write('Detected imports (not necessarily dependencies):', result['imports'])

        st.subheader('Project configuration')
        categories = {
            'pyproject.toml': ('has_pyproject', 'pyproject_files'),
            '.gitignore': ('has_gitignore', 'gitignore_files'),
            'Tests directory': ('has_tests', 'test_directories'),
            'GitHub Actions': ('has_ci', 'ci_files'),
        }
        for label, (root_key, paths_key) in categories.items():
            locations = result[paths_key]
            if result[root_key]:
                st.success(f'{label}: Found at project root')
            elif locations:
                st.info(f'{label}: Found only in subdirectories')
            else:
                st.warning(f'{label}: Not found')
            if locations:
                with st.expander(f'Show {label} locations ({len(locations)})'):
                    for location in locations:
                        st.code(location, language=None)

        if result['errors']:
            st.subheader('Inspection warnings')
            for error in result['errors']:
                st.warning(error)

st.divider()
st.header('Generate a .gitignore')
st.write('Select the tools used by your project, preview the patterns, then download the file.')
selected_options = st.multiselect(
    'Select tools and environments',
    options=list(GITIGNORE_TEMPLATES),
    default=['Python', 'Virtual environments', 'pytest'],
)
gitignore_content = generate_gitignore(selected_options)
st.subheader('Preview')
st.code(gitignore_content or '# No options selected', language='text')
st.download_button(
    'Download .gitignore', data=gitignore_content, file_name='.gitignore',
    mime='text/plain', disabled=not gitignore_content,
)
st.caption('Review existing .gitignore rules before replacing any file.')
