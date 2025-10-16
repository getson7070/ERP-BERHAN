from flask import jsonify, g
from erp import db
from erp.finance.models import JournalEntry, JournalLine  # adjust import path if different
from erp.finance.services import reverse_doc             # existing helper that flips status/metadata

@bp.post("/journals/<uuid:entry_id>/reverse")
def reverse_journal(entry_id):
    """
    Reverse a posted journal by creating mirror JournalLine records that
    swap debit/credit amounts. Ensures double-entry integrity even for
    multi-line entries.
    """
    je = JournalEntry.query.get_or_404(entry_id)

    # 1) Flip status/metadata (your existing logic)
    reverse_doc(je)

    # 2) Create mirror lines: swap debit/credit for every original line
    created = 0
    for line in je.lines:
        mirror_desc = f"Reversal of {line.description or 'JE line'}"
        debit = line.credit or 0
        credit = line.debit or 0
        mirror = JournalLine(
            entry_id=je.id,
            account_id=line.account_id,
            debit=debit,
            credit=credit,
            description=mirror_desc,
            created_by=getattr(g, "user_id", None),
        )
        db.session.add(mirror)
        created += 1

    # 3) Commit everything atomically
    db.session.commit()

    return jsonify({
        "id": str(je.id),
        "status": je.status,
        "reversed_lines": created
    })
