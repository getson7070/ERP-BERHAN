from erp.routes.tenders import WORKFLOW_STATES


def test_workflow_states_sequence():
    assert WORKFLOW_STATES == [
        "advert_registered",
        "decided_to_register",
        "documents_secured",
        "preparing_documentation",
        "documentation_prepared",
        "document_submitted",
        "opening_minute",
        "evaluated",
        "awarded",
    ]


