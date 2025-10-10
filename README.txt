Apply this patch by replacing your migration file:

    migrations/versions/2b3c4d5e6f7a_add_tender_workflow.py

with the attached `2b3c4d5e6f7a_add_tender_workflow_idempotent.py`
(keep the filename or rename to the original).

Then run on Render Shell (or locally):

    alembic upgrade head

Generated: 2025-10-10T22:11:03.611844Z