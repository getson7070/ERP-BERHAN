SCHEMA = {
    'patients': ['id SERIAL PRIMARY KEY', 'org_id INT', 'name TEXT']
}
WORKFLOWS = {'patient_intake': ['triage','doctor']}
