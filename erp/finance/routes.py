"""Module: finance/routes.py — audit-added docstring. Refine with precise purpose when convenient."""
*** Begin Patch
*** Update File: erp/finance/routes.py
@@
-from flask import Blueprint, jsonify, request
+from flask import Blueprint, jsonify, request
+from .models import Account, JournalEntry, JournalLine, Invoice, Bill
*** End Patch



