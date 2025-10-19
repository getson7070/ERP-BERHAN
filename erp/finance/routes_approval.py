*** Begin Patch
*** Update File: erp/finance/routes_approval.py
+from __future__ import annotations
+
+from flask import Blueprint, jsonify, g
+
+from erp.extensions import db, limiter
+from .models import JournalEntry, JournalLine, reverse_doc
+
+# Reuse finance prefix; adjust if your app expects a different one.
+bp = Blueprint("finance_approval", __name__, url_prefix="/finance")
+
+
+@limiter.limit("10/minute")
+@bp.post("/journals/<uuid:entry_id>/reverse")
+def reverse_journal(entry_id):
+    je = JournalEntry.query.get_or_404(entry_id)
+
+    # Update journal status/metadata
+    reverse_doc(je)
+
+    # Mirror lines to swap debit/credit for proper reversal
+    for line in je.lines:
+        mirror = JournalLine(
+            entry_id=je.id,
+            account_id=line.account_id,
+            debit=(line.credit or 0),
+            credit=(line.debit or 0),
+            description=f"Reversal of {line.description or 'JE line'}",
+            created_by=getattr(g, "user_id", None),
+        )
+        db.session.add(mirror)
+
+    db.session.commit()
+    return jsonify({"id": str(je.id), "status": je.status, "reversed_lines": len(je.lines)})
*** End Patch


