import os
from alembic.config import Config
from alembic.script import ScriptDirectory

def load_cfg():
    # Try explicit locations first
    for cand in ("alembic.ini", "migrations/alembic.ini"):
        if os.path.exists(cand):
            return Config(cand)
    # Construct a config on the fly pointing to the migrations folder
    cfg = Config()
    # Respect ALEMBIC_SCRIPT_LOCATION if provided, else default to "migrations"
    script_location = os.getenv("ALEMBIC_SCRIPT_LOCATION", "migrations")
    cfg.set_main_option("script_location", script_location)
    return cfg

cfg = load_cfg()
script = ScriptDirectory.from_config(cfg)

print("Heads:", script.get_heads())
print("Bases:", script.get_bases())

# Show a simple linear view (newest->oldest)
for rev in script.walk_revisions():
    print(f"{rev.revision} <- {rev.down_revision} :: {rev.doc or ''}")
