"""Streamlit interface for PyPadawan."""
import hashlib
import io
import tempfile
import zipfile
from pathlib import Path

import streamlit as st

from archive_handler import extract_project_zip
from gitignore_generator import GITIGNORE_TEMPLATES, generate_gitignore
from guidance import GUIDANCE, all_root_components_present
from inspector import find_project_root, inspect_project


def show_guidance(key, found_at_root, locations):
    """Display an inspection status and an expandable explanation."""
    info = GUIDANCE[key]
    title = info['title']
    if found_at_root:
        st.success(f'{title}: Found at project root')
    elif locations:
        st.info(f'{title}: Found only in subdirectories')
    else:
        st.warning(f'{title}: Not found')

    with st.expander(f'Learn about {title} and what to do'):
        st.markdown('**What is it?**')
        st.write(info['what'])
        st.markdown('**Why might I need it?**')
        st.write(info['why'])
        st.markdown('**What should I do?**')
        st.write(info['how'])
        st.markdown('**Example**')
        st.code(info['example'], language=info['language'])
        if locations:
            st.markdown('**Locations found in this upload**')
            for location in locations:
                st.code(location, language=None)
        if key == 'gitignore':
            st.caption('Use the .gitignore generator further down this page to create suggested patterns.')


st.title('PyPadawan')
st.write('Upload a Python project to inspect its structure and configuration.')

uploaded = st.file_uploader('Upload your Python project as a ZIP', type=['zip'])
if uploaded is not None:
    uploaded_bytes = uploaded.getvalue()
    with tempfile.TemporaryDirectory() as temporary:
        extraction_root = Path(temporary)
        try:
            extract_project_zip(io.BytesIO(uploaded_bytes), extraction_root)
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
        show_guidance('pyproject', result['has_pyproject'], result['pyproject_files'])
        show_guidance('gitignore', result['has_gitignore'], result['gitignore_files'])
        show_guidance('tests', result['has_tests'], result['test_directories'])
        show_guidance('ci', result['has_ci'], result['ci_files'])

        if all_root_components_present(result):
            st.success('🎉 All four configuration components were found at the project root! The Force is strong with this one.')
            project_id = hashlib.sha256(uploaded_bytes).hexdigest()
            if st.session_state.get('celebrated_project') != project_id:
                st.balloons()
                st.session_state['celebrated_project'] = project_id
            st.caption('Presence does not guarantee valid configuration, meaningful tests or passing CI.')

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
