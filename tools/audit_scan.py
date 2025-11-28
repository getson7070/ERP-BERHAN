import hashlib
import os
from pathlib import Path
from typing import Dict, List, Tuple

EXCLUDED_DIRS = {
    '.git',
    '.venv',
    'node_modules',
    '__pycache__',
    '.idea',
    '.vscode',
    'celerybeat-schedule',
    'audit_out',
}

THIS_FILE = Path(__file__).resolve()

PLACEHOLDER_PATTERNS = [
    'TODO', 'FIXME', 'TBD', 'PLACEHOLDER', 'LOREM IPSUM', 'LOREM', 'CHANGE ME', 'CHANGEME', 'UPDATE_ME', 'FILL ME',
]

MAX_HASH_SIZE_BYTES = 20 * 1024 * 1024


def iter_files(root: Path):
    for path in root.rglob('*'):
        if path.is_symlink():
            continue
        if any(part in EXCLUDED_DIRS for part in path.parts):
            continue
        if path.is_file():
            yield path


def hash_file(path: Path) -> str:
    h = hashlib.sha256()
    size = path.stat().st_size
    if size > MAX_HASH_SIZE_BYTES:
        return ''
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


def find_duplicates(files: List[Path]) -> List[Tuple[str, List[Path]]]:
    size_map: Dict[int, List[Path]] = {}
    for path in files:
        size_map.setdefault(path.stat().st_size, []).append(path)
    duplicates: List[Tuple[str, List[Path]]] = []
    for size, grouped in size_map.items():
        if len(grouped) < 2:
            continue
        hash_map: Dict[str, List[Path]] = {}
        for path in grouped:
            digest = hash_file(path)
            if digest:
                hash_map.setdefault(digest, []).append(path)
        for digest, dup_paths in hash_map.items():
            if len(dup_paths) > 1:
                duplicates.append((digest, dup_paths))
    return duplicates


def find_zero_or_short(files: List[Path], max_short: int = 4) -> List[Path]:
    return [p for p in files if p.stat().st_size <= max_short]


def find_placeholders(files: List[Path]) -> Dict[Path, List[str]]:
    results: Dict[Path, List[str]] = {}
    for path in files:
        if path.resolve() == THIS_FILE:
            # Skip self to avoid flagging the pattern list as placeholders.
            continue
        try:
            text = path.read_text(errors='ignore')
        except Exception:
            continue
        matches = [patt for patt in PLACEHOLDER_PATTERNS if patt in text]
        if matches:
            results[path] = matches
    return results


def generate_report():
    root = Path('.')
    files = list(iter_files(root))
    duplicates = find_duplicates(files)
    tiny_files = find_zero_or_short(files)
    placeholders = find_placeholders(files)

    report_lines = []
    report_lines.append('# Automated Audit Scan')
    report_lines.append('')
    report_lines.append('- Total files scanned: {}'.format(len(files)))
    report_lines.append('- Duplicate sets found: {}'.format(len(duplicates)))
    report_lines.append('- Tiny files (<= 4 bytes): {}'.format(len(tiny_files)))
    report_lines.append('- Files containing placeholder text: {}'.format(len(placeholders)))
    report_lines.append('')

    if duplicates:
        report_lines.append('## Potential Duplicates (same hash)')
        for digest, paths in duplicates:
            report_lines.append(f'- Hash `{digest}` ({len(paths)} files):')
            for p in paths:
                report_lines.append(f'  - {p}')
        report_lines.append('')

    if tiny_files:
        report_lines.append('## Tiny or Possibly Truncated Files (<= 4 bytes)')
        for p in tiny_files:
            report_lines.append(f'- {p} (size={p.stat().st_size} bytes)')
        report_lines.append('')

    if placeholders:
        report_lines.append('## Files Containing Placeholder Phrases')
        for p, matches in placeholders.items():
            uniq = ', '.join(sorted(set(matches)))
            report_lines.append(f'- {p}: {uniq}')
        report_lines.append('')

    dest = Path('audit_out/audit_scan_report.md')
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text('\n'.join(report_lines))
    return dest


if __name__ == '__main__':
    report_path = generate_report()
    print(f'Report written to {report_path.resolve()}')
