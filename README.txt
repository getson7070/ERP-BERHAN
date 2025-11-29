The repository no longer ships a tender-workflow migration file; `migrations/versions` does not contain an `*_add_tender_workflow.py` revision, so the prior swap instructions are obsolete. This note replaces that guidance so operators do not hit deployment failures about a missing `2b3c4d5e6f7a_add_tender_workflow.py` file during Render rollout.

Use the in-repo migrations as-is:

    alembic upgrade head

Generated: 2025-10-10T22:11:03.611844Z
