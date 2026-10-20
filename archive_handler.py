"""Validate and extract small project ZIP archives."""
import shutil
import stat
import zipfile
from pathlib import Path, PurePosixPath


def extract_project_zip(uploaded_file, destination):
    destination = Path(destination)
    with zipfile.ZipFile(uploaded_file) as archive:
        entries = archive.infolist()
        if len(entries) > 200:
            raise ValueError('ZIP contains more than 200 entries')
        if sum(entry.file_size for entry in entries) > 10_000_000:
            raise ValueError('Uncompressed ZIP is larger than 10 MB')
        seen = set()
        for entry in entries:
            name = entry.filename
            path = PurePosixPath(name)
            mode = (entry.external_attr >> 16) & 0o170000
            if (not name or name.startswith('/') or '\\' in name or ':' in name or
                    any(part in {'.', '..'} for part in name.split('/')) or
                    mode == stat.S_IFLNK or mode not in (0, stat.S_IFREG, stat.S_IFDIR)):
                raise ValueError(f'Unsafe ZIP entry: {name!r}')
            normalized = str(path).rstrip('/')
            if normalized in seen:
                raise ValueError(f'Duplicate ZIP entry: {name!r}')
            seen.add(normalized)
        for entry in entries:
            if entry.is_dir():
                continue
            target = destination.joinpath(*PurePosixPath(entry.filename).parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(entry) as source, target.open('wb') as output:
                shutil.copyfileobj(source, output)
