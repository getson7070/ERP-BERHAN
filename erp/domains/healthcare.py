"""Module: domains/healthcare.py — audit-added docstring. Refine with precise purpose when convenient."""
SCHEMA = {"patients": ["id SERIAL PRIMARY KEY", "org_id INT", "name TEXT"]}
WORKFLOWS = {"patient_intake": ["triage", "doctor"]}



