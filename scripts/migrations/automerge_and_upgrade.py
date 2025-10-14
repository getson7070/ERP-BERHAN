
import sys
from datetime import UTC, datetime
from alembic.config import Config
from alembic import command
from alembic.script import ScriptDirectory

def main() -> int:
    cfg = Config("alembic.ini")
    script = ScriptDirectory.from_config(cfg)

    # Detect duplicate revision IDs up-front. Fail fast so you can fix by renaming one.
    seen = {}
    dups = set()
    for rev in script.walk_revisions():
        seen[rev.revision] = seen.get(rev.revision, 0) + 1
    dups = [rid for rid, count in seen.items() if count > 1]
    if dups:
        print(f"[alembic] Duplicate revision IDs detected: {dups}. Resolve duplicates before deploy.", file=sys.stderr)
        return 2

    # Only consider true heads
    heads = list(script.get_heads())
    if len(heads) <= 1:
        # Nothing to merge; just upgrade
        command.upgrade(cfg, "head")
        return 0

    # Guard: ensure the ids we're about to merge are all heads
    valid_heads = []
    for hid in heads:
        rev = script.revision_map.get_revision(hid)
        if getattr(rev, "is_head", False):
            valid_heads.append(hid)

    # If after filtering we have 0 or 1, skip merge
    if len(valid_heads) <= 1:
        command.upgrade(cfg, "head")
        return 0

    # Generate a merge revision and then upgrade
    msg = f"automerge {datetime.now(UTC).isoformat()}"
    command.merge(cfg, valid_heads, message=msg)
    command.upgrade(cfg, "head")
    return 0

if __name__ == "__main__":
    sys.exit(main())
