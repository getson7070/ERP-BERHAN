
import sys
import re
import datetime
from pathlib import Path
from typing import Optional, Dict, List

from alembic.config import Config
from alembic import command
from alembic.script import ScriptDirectory
from alembic import util as alembic_util

# -------- Path resolution --------
THIS_FILE = Path(__file__).resolve()

def find_migrations_dir(start: Path) -> Optional[Path]:
    # Look up to 5 levels up for a 'migrations' dir that contains env.py and a versions dir
    for parent in [start.parent, *start.parents]:
        cand = parent.parent / "migrations" if parent.name == "migrations" else parent / "migrations"
        if cand.exists() and (cand / "env.py").exists() and (cand / "versions").exists():
            return cand
    # Also try the project root three levels up convention: <root>/migrations
    root = start.parents[3] if len(start.parents) >= 4 else start.parents[-1]
    cand = root / "migrations"
    if cand.exists() and (cand / "env.py").exists() and (cand / "versions").exists():
        return cand
    return None

MIGRATIONS_DIR = find_migrations_dir(THIS_FILE)
if not MIGRATIONS_DIR:
    print(f"[automerge] ERROR: could not locate a valid 'migrations' directory near {THIS_FILE}")
    sys.exit(2)

VERSIONS_DIR = MIGRATIONS_DIR / "versions"
REV_RE = re.compile(r"^\\s*revision\\s*[:=]\\s*['\\\"]([^'\\\"]+)['\\\"]", re.M)

# -------- Duplicate handling --------
def find_duplicates() -> Dict[str, List[Path]]:
    mapping: Dict[str, List[Path]] = {}
    for p in VERSIONS_DIR.glob("*.py"):
        try:
            txt = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        m = REV_RE.search(txt)
        if not m:
            continue
        rev = m.group(1).strip()
        mapping.setdefault(rev, []).append(p)
    return {rev: files for rev, files in mapping.items() if len(files) > 1}

def disable_extra_duplicates(dups: Dict[str, List[Path]]):
    changed = []
    for rev, files in dups.items():
        files_sorted = sorted(files, key=lambda p: p.name)
        keep = files_sorted[0]
        for extra in files_sorted[1:]:
            new_name = extra.with_suffix(".disabled.py")
            if not new_name.exists():
                extra.rename(new_name)
                changed.append((extra.name, new_name.name, rev, keep.name))
    return changed

# -------- Alembic helpers --------
def make_cfg(migrations_dir: Path) -> Config:
    ini = migrations_dir / "alembic.ini"
    if ini.exists():
        cfg = Config(str(ini))
    else:
        cfg = Config()
        cfg.set_main_option("script_location", str(migrations_dir))
    return cfg

def get_script(cfg: Config) -> ScriptDirectory:
    return ScriptDirectory.from_config(cfg)

def get_heads(cfg: Config):
    script = get_script(cfg)
    return list(script.get_heads())

def merge_only_heads(cfg: Config):
    heads = get_heads(cfg)
    print(f"[automerge] Heads before merge: {heads}")
    if len(heads) <= 1:
        print("[automerge] Single (or zero) head; merge not required.")
        return
    msg = f"automerge {datetime.datetime.now(datetime.UTC):%Y-%m-%d %H:%M:%S %Z}"
    try:
        command.merge(cfg, heads, message=msg)
        print(f"[automerge] Created merge revision for heads: {heads}")
    except alembic_util.CommandError as e:
        # If any rev in 'heads' isn't an actual head (due to inconsistent graph), filter them
        script = get_script(cfg)
        actual_heads = set(script.revision_map.heads)
        filtered = [h for h in heads if h in actual_heads]
        if len(filtered) >= 2:
            print(f"[automerge] Retrying merge with filtered heads: {filtered}")
            command.merge(cfg, filtered, message=msg)
        else:
            print(f"[automerge] WARNING: Could not create merge revision automatically: {e}")
            # Fall back to no-merge; upgrade may still succeed if linearized enough

def main():
    print(f"[automerge] Using migrations dir: {MIGRATIONS_DIR}")
    print(f"[automerge] Versions dir: {VERSIONS_DIR}")

    # Step 1: disable duplicate revisions BEFORE Alembic loads the graph
    dups = find_duplicates()
    if dups:
        changes = disable_extra_duplicates(dups)
        for old, new, rev, kept in changes:
            print(f"[automerge] Disabled duplicate '{rev}': {old} -> {new} (kept {kept})")
    else:
        print("[automerge] No duplicate revision IDs detected.")

    # Step 2: now construct config and compute heads safely
    cfg = make_cfg(MIGRATIONS_DIR)

    # Step 3: merge heads if needed (only actual heads)
    merge_only_heads(cfg)

    # Step 4: upgrade to head
    command.upgrade(cfg, "head")
    print("[automerge] Upgrade to head completed.")

if __name__ == "__main__":
    sys.exit(main())
