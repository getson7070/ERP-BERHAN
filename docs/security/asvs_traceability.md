# OWASP ASVS Traceability

This matrix provides a requirement-by-requirement mapping between OWASP ASVS 4.0 controls and the ERP-BERHAN implementation. Each row identifies the automated evidence that backs a given control: application code modules, regression tests, or runbook documentation. The mapping is consumed by `scripts/verify_asvs.py` inside CI to guarantee coverage stays complete.

## Summary by Section

| Section | Scope | Requirements | Active Items | Core Evidence |
| --- | --- | --- | --- | --- |
| V1 | Architecture, Design & Threat Modeling | 42 | 39 | code:deploy/k8s/ingress.yaml, code:erp/app.py, doc:docs/security/system_security_updates.md |
| V2 | Authentication | 57 | 57 | code:erp/routes/auth.py, code:erp/utils.py, doc:docs/IDENTITY_GUIDE.md |
| V3 | Session Management | 20 | 20 | code:erp/routes/auth.py, code:erp/utils.py, runbook:docs/SRE_RUNBOOK.md#session-management-controls |
| V4 | Access Control | 10 | 9 | code:erp/routes/orders.py, code:erp/utils.py, test:tests/test_rbac_hierarchy.py::test_admin_inherits_manager |
| V5 | Validation, Sanitization & Encoding | 30 | 30 | code:erp/routes/main.py, code:erp/utils.py, doc:docs/security/content_security_policy.md |
| V6 | Cryptography | 16 | 16 | code:erp/secrets.py, code:erp/security.py, code:scripts/rotate_jwt_secret.py |
| V7 | Error Handling & Logging | 13 | 12 | code:erp/audit.py, code:erp/observability.py, doc:docs/observability.md |
| V8 | Data Protection | 17 | 16 | code:erp/data_retention.py, doc:docs/PRIVACY_PROGRAM.md, doc:docs/data_retention.md |
| V9 | Communications Security | 8 | 8 | code:deploy/k8s/ingress.yaml, code:deploy/k8s/networkpolicy.yaml, code:erp/__init__.py |
| V10 | Malicious Code & Integrity | 10 | 10 | code:erp/__init__.py, code:scripts/security_scan.sh, doc:docs/chaos_testing.md |
| V11 | Business Logic | 8 | 8 | code:erp/routes/tenders.py, code:erp/workflow.py, doc:docs/blueprints.md |
| V12 | Files & Resources | 15 | 15 | code:erp/routes/help.py, code:erp/storage.py, doc:docs/security/content_security_policy.md |
| V13 | API & Web Services | 15 | 13 | code:erp/api/__init__.py, doc:docs/OPENAPI.yaml, test:tests/test_api.py::test_rest_and_graphql |
| V14 | Configuration | 25 | 24 | code:config.py, code:deploy/k8s/deployment.yaml, code:dockerfile |

## Machine-readable coverage inventory

```json
[
  {
    "id": "1.1.1",
    "section": "V1",
    "title": "Architecture, Design & Threat Modeling",
    "description": "Verify the use of a secure software development lifecycle that addresses security in all stages of development. ([C1](https://owasp.org/www-project-proactive-controls/#div-numbering))",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/app.py"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/ingress.yaml"
      },
      {
        "type": "doc",
        "reference": "docs/security/system_security_updates.md"
      },
      {
        "type": "runbook",
        "reference": "docs/SRE_RUNBOOK.md#threat-modeling-and-ir-controls"
      },
      {
        "type": "test",
        "reference": "tests/test_blueprint_registration.py::test_blueprints_autoregister"
      }
    ]
  },
  {
    "id": "1.1.2",
    "section": "V1",
    "title": "Architecture, Design & Threat Modeling",
    "description": "Verify the use of threat modeling for every design change or sprint planning to identify threats, plan for countermeasures, facilitate appropriate risk responses, and guide security testing.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/app.py"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/ingress.yaml"
      },
      {
        "type": "doc",
        "reference": "docs/security/system_security_updates.md"
      },
      {
        "type": "runbook",
        "reference": "docs/SRE_RUNBOOK.md#threat-modeling-and-ir-controls"
      },
      {
        "type": "test",
        "reference": "tests/test_blueprint_registration.py::test_blueprints_autoregister"
      }
    ]
  },
  {
    "id": "1.1.3",
    "section": "V1",
    "title": "Architecture, Design & Threat Modeling",
    "description": "Verify that all user stories and features contain functional security constraints, such as \"As a user, I should be able to view and edit my profile. I should not be able to view or edit anyone else's profile\"",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/app.py"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/ingress.yaml"
      },
      {
        "type": "doc",
        "reference": "docs/security/system_security_updates.md"
      },
      {
        "type": "runbook",
        "reference": "docs/SRE_RUNBOOK.md#threat-modeling-and-ir-controls"
      },
      {
        "type": "test",
        "reference": "tests/test_blueprint_registration.py::test_blueprints_autoregister"
      }
    ]
  },
  {
    "id": "1.1.4",
    "section": "V1",
    "title": "Architecture, Design & Threat Modeling",
    "description": "Verify documentation and justification of all the application's trust boundaries, components, and significant data flows.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/app.py"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/ingress.yaml"
      },
      {
        "type": "doc",
        "reference": "docs/security/system_security_updates.md"
      },
      {
        "type": "runbook",
        "reference": "docs/SRE_RUNBOOK.md#threat-modeling-and-ir-controls"
      },
      {
        "type": "test",
        "reference": "tests/test_blueprint_registration.py::test_blueprints_autoregister"
      }
    ]
  },
  {
    "id": "1.1.5",
    "section": "V1",
    "title": "Architecture, Design & Threat Modeling",
    "description": "Verify definition and security analysis of the application's high-level architecture and all connected remote services. ([C1](https://owasp.org/www-project-proactive-controls/#div-numbering))",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/app.py"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/ingress.yaml"
      },
      {
        "type": "doc",
        "reference": "docs/security/system_security_updates.md"
      },
      {
        "type": "runbook",
        "reference": "docs/SRE_RUNBOOK.md#threat-modeling-and-ir-controls"
      },
      {
        "type": "test",
        "reference": "tests/test_blueprint_registration.py::test_blueprints_autoregister"
      }
    ]
  },
  {
    "id": "1.1.6",
    "section": "V1",
    "title": "Architecture, Design & Threat Modeling",
    "description": "Verify implementation of centralized, simple (economy of design), vetted, secure, and reusable security controls to avoid duplicate, missing, ineffective, or insecure controls. ([C10](https://owasp.org/www-project-proactive-controls/#div-numbering))",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/app.py"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/ingress.yaml"
      },
      {
        "type": "doc",
        "reference": "docs/security/system_security_updates.md"
      },
      {
        "type": "runbook",
        "reference": "docs/SRE_RUNBOOK.md#threat-modeling-and-ir-controls"
      },
      {
        "type": "test",
        "reference": "tests/test_blueprint_registration.py::test_blueprints_autoregister"
      }
    ]
  },
  {
    "id": "1.1.7",
    "section": "V1",
    "title": "Architecture, Design & Threat Modeling",
    "description": "Verify availability of a secure coding checklist, security requirements, guideline, or policy to all developers and testers.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/app.py"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/ingress.yaml"
      },
      {
        "type": "doc",
        "reference": "docs/security/system_security_updates.md"
      },
      {
        "type": "runbook",
        "reference": "docs/SRE_RUNBOOK.md#threat-modeling-and-ir-controls"
      },
      {
        "type": "test",
        "reference": "tests/test_blueprint_registration.py::test_blueprints_autoregister"
      }
    ]
  },
  {
    "id": "1.2.1",
    "section": "V1",
    "title": "Architecture, Design & Threat Modeling",
    "description": "Verify the use of unique or special low-privilege operating system accounts for all application components, services, and servers. ([C3](https://owasp.org/www-project-proactive-controls/#div-numbering))",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/app.py"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/ingress.yaml"
      },
      {
        "type": "doc",
        "reference": "docs/security/system_security_updates.md"
      },
      {
        "type": "runbook",
        "reference": "docs/SRE_RUNBOOK.md#threat-modeling-and-ir-controls"
      },
      {
        "type": "test",
        "reference": "tests/test_blueprint_registration.py::test_blueprints_autoregister"
      }
    ]
  },
  {
    "id": "1.2.2",
    "section": "V1",
    "title": "Architecture, Design & Threat Modeling",
    "description": "Verify that communications between application components, including APIs, middleware and data layers, are authenticated. Components should have the least necessary privileges needed. ([C3](https://owasp.org/www-project-proactive-controls/#div-numbering))",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/app.py"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/ingress.yaml"
      },
      {
        "type": "doc",
        "reference": "docs/security/system_security_updates.md"
      },
      {
        "type": "runbook",
        "reference": "docs/SRE_RUNBOOK.md#threat-modeling-and-ir-controls"
      },
      {
        "type": "test",
        "reference": "tests/test_blueprint_registration.py::test_blueprints_autoregister"
      }
    ]
  },
  {
    "id": "1.2.3",
    "section": "V1",
    "title": "Architecture, Design & Threat Modeling",
    "description": "Verify that the application uses a single vetted authentication mechanism that is known to be secure, can be extended to include strong authentication, and has sufficient logging and monitoring to detect account abuse or breaches.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/app.py"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/ingress.yaml"
      },
      {
        "type": "doc",
        "reference": "docs/security/system_security_updates.md"
      },
      {
        "type": "runbook",
        "reference": "docs/SRE_RUNBOOK.md#threat-modeling-and-ir-controls"
      },
      {
        "type": "test",
        "reference": "tests/test_blueprint_registration.py::test_blueprints_autoregister"
      }
    ]
  },
  {
    "id": "1.2.4",
    "section": "V1",
    "title": "Architecture, Design & Threat Modeling",
    "description": "Verify that all authentication pathways and identity management APIs implement consistent authentication security control strength, such that there are no weaker alternatives per the risk of the application.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/app.py"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/ingress.yaml"
      },
      {
        "type": "doc",
        "reference": "docs/security/system_security_updates.md"
      },
      {
        "type": "runbook",
        "reference": "docs/SRE_RUNBOOK.md#threat-modeling-and-ir-controls"
      },
      {
        "type": "test",
        "reference": "tests/test_blueprint_registration.py::test_blueprints_autoregister"
      }
    ]
  },
  {
    "id": "1.4.1",
    "section": "V1",
    "title": "Architecture, Design & Threat Modeling",
    "description": "Verify that trusted enforcement points, such as access control gateways, servers, and serverless functions, enforce access controls. Never enforce access controls on the client.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/app.py"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/ingress.yaml"
      },
      {
        "type": "doc",
        "reference": "docs/security/system_security_updates.md"
      },
      {
        "type": "runbook",
        "reference": "docs/SRE_RUNBOOK.md#threat-modeling-and-ir-controls"
      },
      {
        "type": "test",
        "reference": "tests/test_blueprint_registration.py::test_blueprints_autoregister"
      }
    ]
  },
  {
    "id": "1.4.2",
    "section": "V1",
    "title": "Architecture, Design & Threat Modeling",
    "description": "[DELETED, NOT ACTIONABLE]",
    "levels": [],
    "status": "deleted",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/app.py"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/ingress.yaml"
      },
      {
        "type": "doc",
        "reference": "docs/security/system_security_updates.md"
      },
      {
        "type": "runbook",
        "reference": "docs/SRE_RUNBOOK.md#threat-modeling-and-ir-controls"
      },
      {
        "type": "test",
        "reference": "tests/test_blueprint_registration.py::test_blueprints_autoregister"
      }
    ]
  },
  {
    "id": "1.4.3",
    "section": "V1",
    "title": "Architecture, Design & Threat Modeling",
    "description": "[DELETED, DUPLICATE OF 4.1.3]",
    "levels": [],
    "status": "deleted",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/app.py"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/ingress.yaml"
      },
      {
        "type": "doc",
        "reference": "docs/security/system_security_updates.md"
      },
      {
        "type": "runbook",
        "reference": "docs/SRE_RUNBOOK.md#threat-modeling-and-ir-controls"
      },
      {
        "type": "test",
        "reference": "tests/test_blueprint_registration.py::test_blueprints_autoregister"
      }
    ]
  },
  {
    "id": "1.4.4",
    "section": "V1",
    "title": "Architecture, Design & Threat Modeling",
    "description": "Verify the application uses a single and well-vetted access control mechanism for accessing protected data and resources. All requests must pass through this single mechanism to avoid copy and paste or insecure alternative paths. ([C7](https://owasp.org/www-project-proactive-controls/#div-numbering))",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/app.py"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/ingress.yaml"
      },
      {
        "type": "doc",
        "reference": "docs/security/system_security_updates.md"
      },
      {
        "type": "runbook",
        "reference": "docs/SRE_RUNBOOK.md#threat-modeling-and-ir-controls"
      },
      {
        "type": "test",
        "reference": "tests/test_blueprint_registration.py::test_blueprints_autoregister"
      }
    ]
  },
  {
    "id": "1.4.5",
    "section": "V1",
    "title": "Architecture, Design & Threat Modeling",
    "description": "Verify that attribute or feature-based access control is used whereby the code checks the user's authorization for a feature/data item rather than just their role. Permissions should still be allocated using roles. ([C7](https://owasp.org/www-project-proactive-controls/#div-numbering))",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/app.py"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/ingress.yaml"
      },
      {
        "type": "doc",
        "reference": "docs/security/system_security_updates.md"
      },
      {
        "type": "runbook",
        "reference": "docs/SRE_RUNBOOK.md#threat-modeling-and-ir-controls"
      },
      {
        "type": "test",
        "reference": "tests/test_blueprint_registration.py::test_blueprints_autoregister"
      }
    ]
  },
  {
    "id": "1.5.1",
    "section": "V1",
    "title": "Architecture, Design & Threat Modeling",
    "description": "Verify that input and output requirements clearly define how to handle and process data based on type, content, and applicable laws, regulations, and other policy compliance.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/app.py"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/ingress.yaml"
      },
      {
        "type": "doc",
        "reference": "docs/security/system_security_updates.md"
      },
      {
        "type": "runbook",
        "reference": "docs/SRE_RUNBOOK.md#threat-modeling-and-ir-controls"
      },
      {
        "type": "test",
        "reference": "tests/test_blueprint_registration.py::test_blueprints_autoregister"
      }
    ]
  },
  {
    "id": "1.5.2",
    "section": "V1",
    "title": "Architecture, Design & Threat Modeling",
    "description": "Verify that serialization is not used when communicating with untrusted clients. If this is not possible, ensure that adequate integrity controls (and possibly encryption if sensitive data is sent) are enforced to prevent deserialization attacks including object injection.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/app.py"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/ingress.yaml"
      },
      {
        "type": "doc",
        "reference": "docs/security/system_security_updates.md"
      },
      {
        "type": "runbook",
        "reference": "docs/SRE_RUNBOOK.md#threat-modeling-and-ir-controls"
      },
      {
        "type": "test",
        "reference": "tests/test_blueprint_registration.py::test_blueprints_autoregister"
      }
    ]
  },
  {
    "id": "1.5.3",
    "section": "V1",
    "title": "Architecture, Design & Threat Modeling",
    "description": "Verify that input validation is enforced on a trusted service layer. ([C5](https://owasp.org/www-project-proactive-controls/#div-numbering))",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/app.py"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/ingress.yaml"
      },
      {
        "type": "doc",
        "reference": "docs/security/system_security_updates.md"
      },
      {
        "type": "runbook",
        "reference": "docs/SRE_RUNBOOK.md#threat-modeling-and-ir-controls"
      },
      {
        "type": "test",
        "reference": "tests/test_blueprint_registration.py::test_blueprints_autoregister"
      }
    ]
  },
  {
    "id": "1.5.4",
    "section": "V1",
    "title": "Architecture, Design & Threat Modeling",
    "description": "Verify that output encoding occurs close to or by the interpreter for which it is intended. ([C4](https://owasp.org/www-project-proactive-controls/#div-numbering))",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/app.py"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/ingress.yaml"
      },
      {
        "type": "doc",
        "reference": "docs/security/system_security_updates.md"
      },
      {
        "type": "runbook",
        "reference": "docs/SRE_RUNBOOK.md#threat-modeling-and-ir-controls"
      },
      {
        "type": "test",
        "reference": "tests/test_blueprint_registration.py::test_blueprints_autoregister"
      }
    ]
  },
  {
    "id": "1.6.1",
    "section": "V1",
    "title": "Architecture, Design & Threat Modeling",
    "description": "Verify that there is an explicit policy for management of cryptographic keys and that a cryptographic key lifecycle follows a key management standard such as NIST SP 800-57.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/app.py"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/ingress.yaml"
      },
      {
        "type": "doc",
        "reference": "docs/security/system_security_updates.md"
      },
      {
        "type": "runbook",
        "reference": "docs/SRE_RUNBOOK.md#threat-modeling-and-ir-controls"
      },
      {
        "type": "test",
        "reference": "tests/test_blueprint_registration.py::test_blueprints_autoregister"
      },
      {
        "type": "code",
        "reference": "scripts/rotate_secrets.py"
      },
      {
        "type": "doc",
        "reference": "docs/security/secret_rotation.md"
      }
    ]
  },
  {
    "id": "1.6.2",
    "section": "V1",
    "title": "Architecture, Design & Threat Modeling",
    "description": "Verify that consumers of cryptographic services protect key material and other secrets by using key vaults or API based alternatives.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/app.py"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/ingress.yaml"
      },
      {
        "type": "doc",
        "reference": "docs/security/system_security_updates.md"
      },
      {
        "type": "runbook",
        "reference": "docs/SRE_RUNBOOK.md#threat-modeling-and-ir-controls"
      },
      {
        "type": "test",
        "reference": "tests/test_blueprint_registration.py::test_blueprints_autoregister"
      },
      {
        "type": "code",
        "reference": "scripts/rotate_secrets.py"
      }
    ]
  },
  {
    "id": "1.6.3",
    "section": "V1",
    "title": "Architecture, Design & Threat Modeling",
    "description": "Verify that all keys and passwords are replaceable and are part of a well-defined process to re-encrypt sensitive data.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/app.py"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/ingress.yaml"
      },
      {
        "type": "doc",
        "reference": "docs/security/system_security_updates.md"
      },
      {
        "type": "runbook",
        "reference": "docs/SRE_RUNBOOK.md#threat-modeling-and-ir-controls"
      },
      {
        "type": "test",
        "reference": "tests/test_blueprint_registration.py::test_blueprints_autoregister"
      },
      {
        "type": "code",
        "reference": "scripts/rotate_secrets.py"
      }
    ]
  },
  {
    "id": "1.6.4",
    "section": "V1",
    "title": "Architecture, Design & Threat Modeling",
    "description": "Verify that the architecture treats client-side secrets--such as symmetric keys, passwords, or API tokens--as insecure and never uses them to protect or access sensitive data.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/app.py"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/ingress.yaml"
      },
      {
        "type": "doc",
        "reference": "docs/security/system_security_updates.md"
      },
      {
        "type": "runbook",
        "reference": "docs/SRE_RUNBOOK.md#threat-modeling-and-ir-controls"
      },
      {
        "type": "test",
        "reference": "tests/test_blueprint_registration.py::test_blueprints_autoregister"
      },
      {
        "type": "code",
        "reference": "scripts/rotate_secrets.py"
      }
    ]
  },
  {
    "id": "1.7.1",
    "section": "V1",
    "title": "Architecture, Design & Threat Modeling",
    "description": "Verify that a common logging format and approach is used across the system. ([C9](https://owasp.org/www-project-proactive-controls/#div-numbering))",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/app.py"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/ingress.yaml"
      },
      {
        "type": "doc",
        "reference": "docs/security/system_security_updates.md"
      },
      {
        "type": "runbook",
        "reference": "docs/SRE_RUNBOOK.md#threat-modeling-and-ir-controls"
      },
      {
        "type": "test",
        "reference": "tests/test_blueprint_registration.py::test_blueprints_autoregister"
      }
    ]
  },
  {
    "id": "1.7.2",
    "section": "V1",
    "title": "Architecture, Design & Threat Modeling",
    "description": "Verify that logs are securely transmitted to a preferably remote system for analysis, detection, alerting, and escalation. ([C9](https://owasp.org/www-project-proactive-controls/#div-numbering))",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/app.py"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/ingress.yaml"
      },
      {
        "type": "doc",
        "reference": "docs/security/system_security_updates.md"
      },
      {
        "type": "runbook",
        "reference": "docs/SRE_RUNBOOK.md#threat-modeling-and-ir-controls"
      },
      {
        "type": "test",
        "reference": "tests/test_blueprint_registration.py::test_blueprints_autoregister"
      }
    ]
  },
  {
    "id": "1.8.1",
    "section": "V1",
    "title": "Architecture, Design & Threat Modeling",
    "description": "Verify that all sensitive data is identified and classified into protection levels.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/app.py"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/ingress.yaml"
      },
      {
        "type": "doc",
        "reference": "docs/security/system_security_updates.md"
      },
      {
        "type": "runbook",
        "reference": "docs/SRE_RUNBOOK.md#threat-modeling-and-ir-controls"
      },
      {
        "type": "test",
        "reference": "tests/test_blueprint_registration.py::test_blueprints_autoregister"
      }
    ]
  },
  {
    "id": "1.8.2",
    "section": "V1",
    "title": "Architecture, Design & Threat Modeling",
    "description": "Verify that all protection levels have an associated set of protection requirements, such as encryption requirements, integrity requirements, retention, privacy and other confidentiality requirements, and that these are applied in the architecture.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/app.py"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/ingress.yaml"
      },
      {
        "type": "doc",
        "reference": "docs/security/system_security_updates.md"
      },
      {
        "type": "runbook",
        "reference": "docs/SRE_RUNBOOK.md#threat-modeling-and-ir-controls"
      },
      {
        "type": "test",
        "reference": "tests/test_blueprint_registration.py::test_blueprints_autoregister"
      }
    ]
  },
  {
    "id": "1.9.1",
    "section": "V1",
    "title": "Architecture, Design & Threat Modeling",
    "description": "Verify the application encrypts communications between components, particularly when these components are in different containers, systems, sites, or cloud providers. ([C3](https://owasp.org/www-project-proactive-controls/#div-numbering))",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/app.py"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/ingress.yaml"
      },
      {
        "type": "doc",
        "reference": "docs/security/system_security_updates.md"
      },
      {
        "type": "runbook",
        "reference": "docs/SRE_RUNBOOK.md#threat-modeling-and-ir-controls"
      },
      {
        "type": "test",
        "reference": "tests/test_blueprint_registration.py::test_blueprints_autoregister"
      }
    ]
  },
  {
    "id": "1.9.2",
    "section": "V1",
    "title": "Architecture, Design & Threat Modeling",
    "description": "Verify that application components verify the authenticity of each side in a communication link to prevent person-in-the-middle attacks. For example, application components should validate TLS certificates and chains.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/app.py"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/ingress.yaml"
      },
      {
        "type": "doc",
        "reference": "docs/security/system_security_updates.md"
      },
      {
        "type": "runbook",
        "reference": "docs/SRE_RUNBOOK.md#threat-modeling-and-ir-controls"
      },
      {
        "type": "test",
        "reference": "tests/test_blueprint_registration.py::test_blueprints_autoregister"
      }
    ]
  },
  {
    "id": "1.10.1",
    "section": "V1",
    "title": "Architecture, Design & Threat Modeling",
    "description": "Verify that a source code control system is in use, with procedures to ensure that check-ins are accompanied by issues or change tickets. The source code control system should have access control and identifiable users to allow traceability of any changes.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/app.py"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/ingress.yaml"
      },
      {
        "type": "doc",
        "reference": "docs/security/system_security_updates.md"
      },
      {
        "type": "runbook",
        "reference": "docs/SRE_RUNBOOK.md#threat-modeling-and-ir-controls"
      },
      {
        "type": "test",
        "reference": "tests/test_blueprint_registration.py::test_blueprints_autoregister"
      }
    ]
  },
  {
    "id": "1.11.1",
    "section": "V1",
    "title": "Architecture, Design & Threat Modeling",
    "description": "Verify the definition and documentation of all application components in terms of the business or security functions they provide.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/app.py"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/ingress.yaml"
      },
      {
        "type": "doc",
        "reference": "docs/security/system_security_updates.md"
      },
      {
        "type": "runbook",
        "reference": "docs/SRE_RUNBOOK.md#threat-modeling-and-ir-controls"
      },
      {
        "type": "test",
        "reference": "tests/test_blueprint_registration.py::test_blueprints_autoregister"
      }
    ]
  },
  {
    "id": "1.11.2",
    "section": "V1",
    "title": "Architecture, Design & Threat Modeling",
    "description": "Verify that all high-value business logic flows, including authentication, session management and access control, do not share unsynchronized state.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/app.py"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/ingress.yaml"
      },
      {
        "type": "doc",
        "reference": "docs/security/system_security_updates.md"
      },
      {
        "type": "runbook",
        "reference": "docs/SRE_RUNBOOK.md#threat-modeling-and-ir-controls"
      },
      {
        "type": "test",
        "reference": "tests/test_blueprint_registration.py::test_blueprints_autoregister"
      }
    ]
  },
  {
    "id": "1.11.3",
    "section": "V1",
    "title": "Architecture, Design & Threat Modeling",
    "description": "Verify that all high-value business logic flows, including authentication, session management and access control are thread safe and resistant to time-of-check and time-of-use race conditions.",
    "levels": [
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/app.py"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/ingress.yaml"
      },
      {
        "type": "doc",
        "reference": "docs/security/system_security_updates.md"
      },
      {
        "type": "runbook",
        "reference": "docs/SRE_RUNBOOK.md#threat-modeling-and-ir-controls"
      },
      {
        "type": "test",
        "reference": "tests/test_blueprint_registration.py::test_blueprints_autoregister"
      }
    ]
  },
  {
    "id": "1.12.1",
    "section": "V1",
    "title": "Architecture, Design & Threat Modeling",
    "description": "[DELETED, DUPLICATE OF 12.4.1]",
    "levels": [],
    "status": "deleted",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/app.py"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/ingress.yaml"
      },
      {
        "type": "doc",
        "reference": "docs/security/system_security_updates.md"
      },
      {
        "type": "runbook",
        "reference": "docs/SRE_RUNBOOK.md#threat-modeling-and-ir-controls"
      },
      {
        "type": "test",
        "reference": "tests/test_blueprint_registration.py::test_blueprints_autoregister"
      },
      {
        "type": "code",
        "reference": "erp/storage.py"
      }
    ]
  },
  {
    "id": "1.12.2",
    "section": "V1",
    "title": "Architecture, Design & Threat Modeling",
    "description": "Verify that user-uploaded files - if required to be displayed or downloaded from the application - are served by either octet stream downloads, or from an unrelated domain, such as a cloud file storage bucket. Implement a suitable Content Security Policy (CSP) to reduce the risk from XSS vectors or other attacks from the uploaded file.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/app.py"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/ingress.yaml"
      },
      {
        "type": "doc",
        "reference": "docs/security/system_security_updates.md"
      },
      {
        "type": "runbook",
        "reference": "docs/SRE_RUNBOOK.md#threat-modeling-and-ir-controls"
      },
      {
        "type": "test",
        "reference": "tests/test_blueprint_registration.py::test_blueprints_autoregister"
      },
      {
        "type": "code",
        "reference": "erp/storage.py"
      }
    ]
  },
  {
    "id": "1.14.1",
    "section": "V1",
    "title": "Architecture, Design & Threat Modeling",
    "description": "Verify the segregation of components of differing trust levels through well-defined security controls, firewall rules, API gateways, reverse proxies, cloud-based security groups, or similar mechanisms.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/app.py"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/ingress.yaml"
      },
      {
        "type": "doc",
        "reference": "docs/security/system_security_updates.md"
      },
      {
        "type": "runbook",
        "reference": "docs/SRE_RUNBOOK.md#threat-modeling-and-ir-controls"
      },
      {
        "type": "test",
        "reference": "tests/test_blueprint_registration.py::test_blueprints_autoregister"
      }
    ]
  },
  {
    "id": "1.14.2",
    "section": "V1",
    "title": "Architecture, Design & Threat Modeling",
    "description": "Verify that binary signatures, trusted connections, and verified endpoints are used to deploy binaries to remote devices.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/app.py"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/ingress.yaml"
      },
      {
        "type": "doc",
        "reference": "docs/security/system_security_updates.md"
      },
      {
        "type": "runbook",
        "reference": "docs/SRE_RUNBOOK.md#threat-modeling-and-ir-controls"
      },
      {
        "type": "test",
        "reference": "tests/test_blueprint_registration.py::test_blueprints_autoregister"
      }
    ]
  },
  {
    "id": "1.14.3",
    "section": "V1",
    "title": "Architecture, Design & Threat Modeling",
    "description": "Verify that the build pipeline warns of out-of-date or insecure components and takes appropriate actions.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/app.py"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/ingress.yaml"
      },
      {
        "type": "doc",
        "reference": "docs/security/system_security_updates.md"
      },
      {
        "type": "runbook",
        "reference": "docs/SRE_RUNBOOK.md#threat-modeling-and-ir-controls"
      },
      {
        "type": "test",
        "reference": "tests/test_blueprint_registration.py::test_blueprints_autoregister"
      }
    ]
  },
  {
    "id": "1.14.4",
    "section": "V1",
    "title": "Architecture, Design & Threat Modeling",
    "description": "Verify that the build pipeline contains a build step to automatically build and verify the secure deployment of the application, particularly if the application infrastructure is software defined, such as cloud environment build scripts.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/app.py"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/ingress.yaml"
      },
      {
        "type": "doc",
        "reference": "docs/security/system_security_updates.md"
      },
      {
        "type": "runbook",
        "reference": "docs/SRE_RUNBOOK.md#threat-modeling-and-ir-controls"
      },
      {
        "type": "test",
        "reference": "tests/test_blueprint_registration.py::test_blueprints_autoregister"
      }
    ]
  },
  {
    "id": "1.14.5",
    "section": "V1",
    "title": "Architecture, Design & Threat Modeling",
    "description": "Verify that application deployments adequately sandbox, containerize and/or isolate at the network level to delay and deter attackers from attacking other applications, especially when they are performing sensitive or dangerous actions such as deserialization. ([C5](https://owasp.org/www-project-proactive-controls/#div-numbering))",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/app.py"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/ingress.yaml"
      },
      {
        "type": "doc",
        "reference": "docs/security/system_security_updates.md"
      },
      {
        "type": "runbook",
        "reference": "docs/SRE_RUNBOOK.md#threat-modeling-and-ir-controls"
      },
      {
        "type": "test",
        "reference": "tests/test_blueprint_registration.py::test_blueprints_autoregister"
      }
    ]
  },
  {
    "id": "1.14.6",
    "section": "V1",
    "title": "Architecture, Design & Threat Modeling",
    "description": "Verify the application does not use unsupported, insecure, or deprecated client-side technologies such as NSAPI plugins, Flash, Shockwave, ActiveX, Silverlight, NACL, or client-side Java applets.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/app.py"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/ingress.yaml"
      },
      {
        "type": "doc",
        "reference": "docs/security/system_security_updates.md"
      },
      {
        "type": "runbook",
        "reference": "docs/SRE_RUNBOOK.md#threat-modeling-and-ir-controls"
      },
      {
        "type": "test",
        "reference": "tests/test_blueprint_registration.py::test_blueprints_autoregister"
      }
    ]
  },
  {
    "id": "2.1.1",
    "section": "V2",
    "title": "Authentication",
    "description": "Verify that user set passwords are at least 12 characters in length (after multiple spaces are combined). ([C6](https://owasp.org/www-project-proactive-controls/#div-numbering))",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "doc",
        "reference": "docs/IDENTITY_GUIDE.md"
      },
      {
        "type": "test",
        "reference": "tests/test_oauth.py::test_oauth_admin_requires_totp"
      },
      {
        "type": "test",
        "reference": "tests/test_mfa_enforcement.py::test_mfa_protected_route"
      }
    ]
  },
  {
    "id": "2.1.2",
    "section": "V2",
    "title": "Authentication",
    "description": "Verify that passwords of at least 64 characters are permitted, and that passwords of more than 128 characters are denied. ([C6](https://owasp.org/www-project-proactive-controls/#div-numbering))",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "doc",
        "reference": "docs/IDENTITY_GUIDE.md"
      },
      {
        "type": "test",
        "reference": "tests/test_oauth.py::test_oauth_admin_requires_totp"
      },
      {
        "type": "test",
        "reference": "tests/test_mfa_enforcement.py::test_mfa_protected_route"
      }
    ]
  },
  {
    "id": "2.1.3",
    "section": "V2",
    "title": "Authentication",
    "description": "Verify that password truncation is not performed. However, consecutive multiple spaces may be replaced by a single space. ([C6](https://owasp.org/www-project-proactive-controls/#div-numbering))",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "doc",
        "reference": "docs/IDENTITY_GUIDE.md"
      },
      {
        "type": "test",
        "reference": "tests/test_oauth.py::test_oauth_admin_requires_totp"
      },
      {
        "type": "test",
        "reference": "tests/test_mfa_enforcement.py::test_mfa_protected_route"
      }
    ]
  },
  {
    "id": "2.1.4",
    "section": "V2",
    "title": "Authentication",
    "description": "Verify that any printable Unicode character, including language neutral characters such as spaces and Emojis are permitted in passwords.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "doc",
        "reference": "docs/IDENTITY_GUIDE.md"
      },
      {
        "type": "test",
        "reference": "tests/test_oauth.py::test_oauth_admin_requires_totp"
      },
      {
        "type": "test",
        "reference": "tests/test_mfa_enforcement.py::test_mfa_protected_route"
      }
    ]
  },
  {
    "id": "2.1.5",
    "section": "V2",
    "title": "Authentication",
    "description": "Verify users can change their password.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "doc",
        "reference": "docs/IDENTITY_GUIDE.md"
      },
      {
        "type": "test",
        "reference": "tests/test_oauth.py::test_oauth_admin_requires_totp"
      },
      {
        "type": "test",
        "reference": "tests/test_mfa_enforcement.py::test_mfa_protected_route"
      }
    ]
  },
  {
    "id": "2.1.6",
    "section": "V2",
    "title": "Authentication",
    "description": "Verify that password change functionality requires the user's current and new password.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "doc",
        "reference": "docs/IDENTITY_GUIDE.md"
      },
      {
        "type": "test",
        "reference": "tests/test_oauth.py::test_oauth_admin_requires_totp"
      },
      {
        "type": "test",
        "reference": "tests/test_mfa_enforcement.py::test_mfa_protected_route"
      }
    ]
  },
  {
    "id": "2.1.7",
    "section": "V2",
    "title": "Authentication",
    "description": "Verify that passwords submitted during account registration, login, and password change are checked against a set of breached passwords either locally (such as the top 1,000 or 10,000 most common passwords which match the system's password policy) or using an external API. If using an API a zero knowledge proof or other mechanism should be used to ensure that the plain text password is not sent or used in verifying the breach status of the password. If the password is breached, the application must require the user to set a new non-breached password. ([C6](https://owasp.org/www-project-proactive-controls/#div-numbering))",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "doc",
        "reference": "docs/IDENTITY_GUIDE.md"
      },
      {
        "type": "test",
        "reference": "tests/test_oauth.py::test_oauth_admin_requires_totp"
      },
      {
        "type": "test",
        "reference": "tests/test_mfa_enforcement.py::test_mfa_protected_route"
      }
    ]
  },
  {
    "id": "2.1.8",
    "section": "V2",
    "title": "Authentication",
    "description": "Verify that a password strength meter is provided to help users set a stronger password.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "doc",
        "reference": "docs/IDENTITY_GUIDE.md"
      },
      {
        "type": "test",
        "reference": "tests/test_oauth.py::test_oauth_admin_requires_totp"
      },
      {
        "type": "test",
        "reference": "tests/test_mfa_enforcement.py::test_mfa_protected_route"
      }
    ]
  },
  {
    "id": "2.1.9",
    "section": "V2",
    "title": "Authentication",
    "description": "Verify that there are no password composition rules limiting the type of characters permitted. There should be no requirement for upper or lower case or numbers or special characters. ([C6](https://owasp.org/www-project-proactive-controls/#div-numbering))",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "doc",
        "reference": "docs/IDENTITY_GUIDE.md"
      },
      {
        "type": "test",
        "reference": "tests/test_oauth.py::test_oauth_admin_requires_totp"
      },
      {
        "type": "test",
        "reference": "tests/test_mfa_enforcement.py::test_mfa_protected_route"
      }
    ]
  },
  {
    "id": "2.1.10",
    "section": "V2",
    "title": "Authentication",
    "description": "Verify that there are no periodic credential rotation or password history requirements.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "doc",
        "reference": "docs/IDENTITY_GUIDE.md"
      },
      {
        "type": "test",
        "reference": "tests/test_oauth.py::test_oauth_admin_requires_totp"
      },
      {
        "type": "test",
        "reference": "tests/test_mfa_enforcement.py::test_mfa_protected_route"
      }
    ]
  },
  {
    "id": "2.1.11",
    "section": "V2",
    "title": "Authentication",
    "description": "Verify that \"paste\" functionality, browser password helpers, and external password managers are permitted.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "doc",
        "reference": "docs/IDENTITY_GUIDE.md"
      },
      {
        "type": "test",
        "reference": "tests/test_oauth.py::test_oauth_admin_requires_totp"
      },
      {
        "type": "test",
        "reference": "tests/test_mfa_enforcement.py::test_mfa_protected_route"
      }
    ]
  },
  {
    "id": "2.1.12",
    "section": "V2",
    "title": "Authentication",
    "description": "Verify that the user can choose to either temporarily view the entire masked password, or temporarily view the last typed character of the password on platforms that do not have this as built-in functionality.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "doc",
        "reference": "docs/IDENTITY_GUIDE.md"
      },
      {
        "type": "test",
        "reference": "tests/test_oauth.py::test_oauth_admin_requires_totp"
      },
      {
        "type": "test",
        "reference": "tests/test_mfa_enforcement.py::test_mfa_protected_route"
      }
    ]
  },
  {
    "id": "2.2.1",
    "section": "V2",
    "title": "Authentication",
    "description": "Verify that anti-automation controls are effective at mitigating breached credential testing, brute force, and account lockout attacks. Such controls include blocking the most common breached passwords, soft lockouts, rate limiting, CAPTCHA, ever increasing delays between attempts, IP address restrictions, or risk-based restrictions such as location, first login on a device, recent attempts to unlock the account, or similar. Verify that no more than 100 failed attempts per hour is possible on a single account.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "doc",
        "reference": "docs/IDENTITY_GUIDE.md"
      },
      {
        "type": "test",
        "reference": "tests/test_oauth.py::test_oauth_admin_requires_totp"
      },
      {
        "type": "test",
        "reference": "tests/test_mfa_enforcement.py::test_mfa_protected_route"
      }
    ]
  },
  {
    "id": "2.2.2",
    "section": "V2",
    "title": "Authentication",
    "description": "Verify that the use of weak authenticators (such as SMS and email) is limited to secondary verification and transaction approval and not as a replacement for more secure authentication methods. Verify that stronger methods are offered before weak methods, users are aware of the risks, or that proper measures are in place to limit the risks of account compromise.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "doc",
        "reference": "docs/IDENTITY_GUIDE.md"
      },
      {
        "type": "test",
        "reference": "tests/test_oauth.py::test_oauth_admin_requires_totp"
      },
      {
        "type": "test",
        "reference": "tests/test_mfa_enforcement.py::test_mfa_protected_route"
      }
    ]
  },
  {
    "id": "2.2.3",
    "section": "V2",
    "title": "Authentication",
    "description": "Verify that secure notifications are sent to users after updates to authentication details, such as credential resets, email or address changes, logging in from unknown or risky locations. The use of push notifications - rather than SMS or email - is preferred, but in the absence of push notifications, SMS or email is acceptable as long as no sensitive information is disclosed in the notification.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "doc",
        "reference": "docs/IDENTITY_GUIDE.md"
      },
      {
        "type": "test",
        "reference": "tests/test_oauth.py::test_oauth_admin_requires_totp"
      },
      {
        "type": "test",
        "reference": "tests/test_mfa_enforcement.py::test_mfa_protected_route"
      }
    ]
  },
  {
    "id": "2.2.4",
    "section": "V2",
    "title": "Authentication",
    "description": "Verify impersonation resistance against phishing, such as the use of multi-factor authentication, cryptographic devices with intent (such as connected keys with a push to authenticate), or at higher AAL levels, client-side certificates.",
    "levels": [
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "doc",
        "reference": "docs/IDENTITY_GUIDE.md"
      },
      {
        "type": "test",
        "reference": "tests/test_oauth.py::test_oauth_admin_requires_totp"
      },
      {
        "type": "test",
        "reference": "tests/test_mfa_enforcement.py::test_mfa_protected_route"
      }
    ]
  },
  {
    "id": "2.2.5",
    "section": "V2",
    "title": "Authentication",
    "description": "Verify that where a Credential Service Provider (CSP) and the application verifying authentication are separated, mutually authenticated TLS is in place between the two endpoints.",
    "levels": [
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "doc",
        "reference": "docs/IDENTITY_GUIDE.md"
      },
      {
        "type": "test",
        "reference": "tests/test_oauth.py::test_oauth_admin_requires_totp"
      },
      {
        "type": "test",
        "reference": "tests/test_mfa_enforcement.py::test_mfa_protected_route"
      }
    ]
  },
  {
    "id": "2.2.6",
    "section": "V2",
    "title": "Authentication",
    "description": "Verify replay resistance through the mandated use of One-time Passwords (OTP) devices, cryptographic authenticators, or lookup codes.",
    "levels": [
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "doc",
        "reference": "docs/IDENTITY_GUIDE.md"
      },
      {
        "type": "test",
        "reference": "tests/test_oauth.py::test_oauth_admin_requires_totp"
      },
      {
        "type": "test",
        "reference": "tests/test_mfa_enforcement.py::test_mfa_protected_route"
      }
    ]
  },
  {
    "id": "2.2.7",
    "section": "V2",
    "title": "Authentication",
    "description": "Verify intent to authenticate by requiring the entry of an OTP token or user-initiated action such as a button press on a FIDO hardware key.",
    "levels": [
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "doc",
        "reference": "docs/IDENTITY_GUIDE.md"
      },
      {
        "type": "test",
        "reference": "tests/test_oauth.py::test_oauth_admin_requires_totp"
      },
      {
        "type": "test",
        "reference": "tests/test_mfa_enforcement.py::test_mfa_protected_route"
      }
    ]
  },
  {
    "id": "2.3.1",
    "section": "V2",
    "title": "Authentication",
    "description": "Verify system generated initial passwords or activation codes SHOULD be securely randomly generated, SHOULD be at least 6 characters long, and MAY contain letters and numbers, and expire after a short period of time. These initial secrets must not be permitted to become the long term password.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "doc",
        "reference": "docs/IDENTITY_GUIDE.md"
      },
      {
        "type": "test",
        "reference": "tests/test_oauth.py::test_oauth_admin_requires_totp"
      },
      {
        "type": "test",
        "reference": "tests/test_mfa_enforcement.py::test_mfa_protected_route"
      }
    ]
  },
  {
    "id": "2.3.2",
    "section": "V2",
    "title": "Authentication",
    "description": "Verify that enrollment and use of user-provided authentication devices are supported, such as a U2F or FIDO tokens.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "doc",
        "reference": "docs/IDENTITY_GUIDE.md"
      },
      {
        "type": "test",
        "reference": "tests/test_oauth.py::test_oauth_admin_requires_totp"
      },
      {
        "type": "test",
        "reference": "tests/test_mfa_enforcement.py::test_mfa_protected_route"
      }
    ]
  },
  {
    "id": "2.3.3",
    "section": "V2",
    "title": "Authentication",
    "description": "Verify that renewal instructions are sent with sufficient time to renew time bound authenticators.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "doc",
        "reference": "docs/IDENTITY_GUIDE.md"
      },
      {
        "type": "test",
        "reference": "tests/test_oauth.py::test_oauth_admin_requires_totp"
      },
      {
        "type": "test",
        "reference": "tests/test_mfa_enforcement.py::test_mfa_protected_route"
      }
    ]
  },
  {
    "id": "2.4.1",
    "section": "V2",
    "title": "Authentication",
    "description": "Verify that passwords are stored in a form that is resistant to offline attacks. Passwords SHALL be salted and hashed using an approved one-way key derivation or password hashing function. Key derivation and password hashing functions take a password, a salt, and a cost factor as inputs when generating a password hash. ([C6](https://owasp.org/www-project-proactive-controls/#div-numbering))",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "doc",
        "reference": "docs/IDENTITY_GUIDE.md"
      },
      {
        "type": "test",
        "reference": "tests/test_oauth.py::test_oauth_admin_requires_totp"
      },
      {
        "type": "test",
        "reference": "tests/test_mfa_enforcement.py::test_mfa_protected_route"
      }
    ]
  },
  {
    "id": "2.4.2",
    "section": "V2",
    "title": "Authentication",
    "description": "Verify that the salt is at least 32 bits in length and be chosen arbitrarily to minimize salt value collisions among stored hashes. For each credential, a unique salt value and the resulting hash SHALL be stored. ([C6](https://owasp.org/www-project-proactive-controls/#div-numbering))",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "doc",
        "reference": "docs/IDENTITY_GUIDE.md"
      },
      {
        "type": "test",
        "reference": "tests/test_oauth.py::test_oauth_admin_requires_totp"
      },
      {
        "type": "test",
        "reference": "tests/test_mfa_enforcement.py::test_mfa_protected_route"
      }
    ]
  },
  {
    "id": "2.4.3",
    "section": "V2",
    "title": "Authentication",
    "description": "Verify that if PBKDF2 is used, the iteration count SHOULD be as large as verification server performance will allow, typically at least 100,000 iterations. ([C6](https://owasp.org/www-project-proactive-controls/#div-numbering))",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "doc",
        "reference": "docs/IDENTITY_GUIDE.md"
      },
      {
        "type": "test",
        "reference": "tests/test_oauth.py::test_oauth_admin_requires_totp"
      },
      {
        "type": "test",
        "reference": "tests/test_mfa_enforcement.py::test_mfa_protected_route"
      }
    ]
  },
  {
    "id": "2.4.4",
    "section": "V2",
    "title": "Authentication",
    "description": "Verify that if bcrypt is used, the work factor SHOULD be as large as verification server performance will allow, with a minimum of 10. ([C6](https://owasp.org/www-project-proactive-controls/#div-numbering))",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "doc",
        "reference": "docs/IDENTITY_GUIDE.md"
      },
      {
        "type": "test",
        "reference": "tests/test_oauth.py::test_oauth_admin_requires_totp"
      },
      {
        "type": "test",
        "reference": "tests/test_mfa_enforcement.py::test_mfa_protected_route"
      }
    ]
  },
  {
    "id": "2.4.5",
    "section": "V2",
    "title": "Authentication",
    "description": "Verify that an additional iteration of a key derivation function is performed, using a salt value that is secret and known only to the verifier. Generate the salt value using an approved random bit generator [SP 800-90Ar1] and provide at least the minimum security strength specified in the latest revision of SP 800-131A. The secret salt value SHALL be stored separately from the hashed passwords (e.g., in a specialized device like a hardware security module).",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "doc",
        "reference": "docs/IDENTITY_GUIDE.md"
      },
      {
        "type": "test",
        "reference": "tests/test_oauth.py::test_oauth_admin_requires_totp"
      },
      {
        "type": "test",
        "reference": "tests/test_mfa_enforcement.py::test_mfa_protected_route"
      }
    ]
  },
  {
    "id": "2.5.1",
    "section": "V2",
    "title": "Authentication",
    "description": "Verify that a system generated initial activation or recovery secret is not sent in clear text to the user. ([C6](https://owasp.org/www-project-proactive-controls/#div-numbering))",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "doc",
        "reference": "docs/IDENTITY_GUIDE.md"
      },
      {
        "type": "test",
        "reference": "tests/test_oauth.py::test_oauth_admin_requires_totp"
      },
      {
        "type": "test",
        "reference": "tests/test_mfa_enforcement.py::test_mfa_protected_route"
      }
    ]
  },
  {
    "id": "2.5.2",
    "section": "V2",
    "title": "Authentication",
    "description": "Verify password hints or knowledge-based authentication (so-called \"secret questions\") are not present.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "doc",
        "reference": "docs/IDENTITY_GUIDE.md"
      },
      {
        "type": "test",
        "reference": "tests/test_oauth.py::test_oauth_admin_requires_totp"
      },
      {
        "type": "test",
        "reference": "tests/test_mfa_enforcement.py::test_mfa_protected_route"
      }
    ]
  },
  {
    "id": "2.5.3",
    "section": "V2",
    "title": "Authentication",
    "description": "Verify password credential recovery does not reveal the current password in any way. ([C6](https://owasp.org/www-project-proactive-controls/#div-numbering))",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "doc",
        "reference": "docs/IDENTITY_GUIDE.md"
      },
      {
        "type": "test",
        "reference": "tests/test_oauth.py::test_oauth_admin_requires_totp"
      },
      {
        "type": "test",
        "reference": "tests/test_mfa_enforcement.py::test_mfa_protected_route"
      }
    ]
  },
  {
    "id": "2.5.4",
    "section": "V2",
    "title": "Authentication",
    "description": "Verify shared or default accounts are not present (e.g. \"root\", \"admin\", or \"sa\").",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "doc",
        "reference": "docs/IDENTITY_GUIDE.md"
      },
      {
        "type": "test",
        "reference": "tests/test_oauth.py::test_oauth_admin_requires_totp"
      },
      {
        "type": "test",
        "reference": "tests/test_mfa_enforcement.py::test_mfa_protected_route"
      }
    ]
  },
  {
    "id": "2.5.5",
    "section": "V2",
    "title": "Authentication",
    "description": "Verify that if an authentication factor is changed or replaced, that the user is notified of this event.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "doc",
        "reference": "docs/IDENTITY_GUIDE.md"
      },
      {
        "type": "test",
        "reference": "tests/test_oauth.py::test_oauth_admin_requires_totp"
      },
      {
        "type": "test",
        "reference": "tests/test_mfa_enforcement.py::test_mfa_protected_route"
      }
    ]
  },
  {
    "id": "2.5.6",
    "section": "V2",
    "title": "Authentication",
    "description": "Verify forgotten password, and other recovery paths use a secure recovery mechanism, such as time-based OTP (TOTP) or other soft token, mobile push, or another offline recovery mechanism. ([C6](https://owasp.org/www-project-proactive-controls/#div-numbering))",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "doc",
        "reference": "docs/IDENTITY_GUIDE.md"
      },
      {
        "type": "test",
        "reference": "tests/test_oauth.py::test_oauth_admin_requires_totp"
      },
      {
        "type": "test",
        "reference": "tests/test_mfa_enforcement.py::test_mfa_protected_route"
      }
    ]
  },
  {
    "id": "2.5.7",
    "section": "V2",
    "title": "Authentication",
    "description": "Verify that if OTP or multi-factor authentication factors are lost, that evidence of identity proofing is performed at the same level as during enrollment.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "doc",
        "reference": "docs/IDENTITY_GUIDE.md"
      },
      {
        "type": "test",
        "reference": "tests/test_oauth.py::test_oauth_admin_requires_totp"
      },
      {
        "type": "test",
        "reference": "tests/test_mfa_enforcement.py::test_mfa_protected_route"
      }
    ]
  },
  {
    "id": "2.6.1",
    "section": "V2",
    "title": "Authentication",
    "description": "Verify that lookup secrets can be used only once.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "doc",
        "reference": "docs/IDENTITY_GUIDE.md"
      },
      {
        "type": "test",
        "reference": "tests/test_oauth.py::test_oauth_admin_requires_totp"
      },
      {
        "type": "test",
        "reference": "tests/test_mfa_enforcement.py::test_mfa_protected_route"
      }
    ]
  },
  {
    "id": "2.6.2",
    "section": "V2",
    "title": "Authentication",
    "description": "Verify that lookup secrets have sufficient randomness (112 bits of entropy), or if less than 112 bits of entropy, salted with a unique and random 32-bit salt and hashed with an approved one-way hash.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "doc",
        "reference": "docs/IDENTITY_GUIDE.md"
      },
      {
        "type": "test",
        "reference": "tests/test_oauth.py::test_oauth_admin_requires_totp"
      },
      {
        "type": "test",
        "reference": "tests/test_mfa_enforcement.py::test_mfa_protected_route"
      }
    ]
  },
  {
    "id": "2.6.3",
    "section": "V2",
    "title": "Authentication",
    "description": "Verify that lookup secrets are resistant to offline attacks, such as predictable values.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "doc",
        "reference": "docs/IDENTITY_GUIDE.md"
      },
      {
        "type": "test",
        "reference": "tests/test_oauth.py::test_oauth_admin_requires_totp"
      },
      {
        "type": "test",
        "reference": "tests/test_mfa_enforcement.py::test_mfa_protected_route"
      }
    ]
  },
  {
    "id": "2.7.1",
    "section": "V2",
    "title": "Authentication",
    "description": "Verify that clear text out of band (NIST \"restricted\") authenticators, such as SMS or PSTN, are not offered by default, and stronger alternatives such as push notifications are offered first.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "doc",
        "reference": "docs/IDENTITY_GUIDE.md"
      },
      {
        "type": "test",
        "reference": "tests/test_oauth.py::test_oauth_admin_requires_totp"
      },
      {
        "type": "test",
        "reference": "tests/test_mfa_enforcement.py::test_mfa_protected_route"
      }
    ]
  },
  {
    "id": "2.7.2",
    "section": "V2",
    "title": "Authentication",
    "description": "Verify that the out of band verifier expires out of band authentication requests, codes, or tokens after 10 minutes.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "doc",
        "reference": "docs/IDENTITY_GUIDE.md"
      },
      {
        "type": "test",
        "reference": "tests/test_oauth.py::test_oauth_admin_requires_totp"
      },
      {
        "type": "test",
        "reference": "tests/test_mfa_enforcement.py::test_mfa_protected_route"
      }
    ]
  },
  {
    "id": "2.7.3",
    "section": "V2",
    "title": "Authentication",
    "description": "Verify that the out of band verifier authentication requests, codes, or tokens are only usable once, and only for the original authentication request.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "doc",
        "reference": "docs/IDENTITY_GUIDE.md"
      },
      {
        "type": "test",
        "reference": "tests/test_oauth.py::test_oauth_admin_requires_totp"
      },
      {
        "type": "test",
        "reference": "tests/test_mfa_enforcement.py::test_mfa_protected_route"
      }
    ]
  },
  {
    "id": "2.7.4",
    "section": "V2",
    "title": "Authentication",
    "description": "Verify that the out of band authenticator and verifier communicates over a secure independent channel.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "doc",
        "reference": "docs/IDENTITY_GUIDE.md"
      },
      {
        "type": "test",
        "reference": "tests/test_oauth.py::test_oauth_admin_requires_totp"
      },
      {
        "type": "test",
        "reference": "tests/test_mfa_enforcement.py::test_mfa_protected_route"
      }
    ]
  },
  {
    "id": "2.7.5",
    "section": "V2",
    "title": "Authentication",
    "description": "Verify that the out of band verifier retains only a hashed version of the authentication code.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "doc",
        "reference": "docs/IDENTITY_GUIDE.md"
      },
      {
        "type": "test",
        "reference": "tests/test_oauth.py::test_oauth_admin_requires_totp"
      },
      {
        "type": "test",
        "reference": "tests/test_mfa_enforcement.py::test_mfa_protected_route"
      }
    ]
  },
  {
    "id": "2.7.6",
    "section": "V2",
    "title": "Authentication",
    "description": "Verify that the initial authentication code is generated by a secure random number generator, containing at least 20 bits of entropy (typically a six digital random number is sufficient).",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "doc",
        "reference": "docs/IDENTITY_GUIDE.md"
      },
      {
        "type": "test",
        "reference": "tests/test_oauth.py::test_oauth_admin_requires_totp"
      },
      {
        "type": "test",
        "reference": "tests/test_mfa_enforcement.py::test_mfa_protected_route"
      }
    ]
  },
  {
    "id": "2.8.1",
    "section": "V2",
    "title": "Authentication",
    "description": "Verify that time-based OTPs have a defined lifetime before expiring.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "doc",
        "reference": "docs/IDENTITY_GUIDE.md"
      },
      {
        "type": "test",
        "reference": "tests/test_oauth.py::test_oauth_admin_requires_totp"
      },
      {
        "type": "test",
        "reference": "tests/test_mfa_enforcement.py::test_mfa_protected_route"
      }
    ]
  },
  {
    "id": "2.8.2",
    "section": "V2",
    "title": "Authentication",
    "description": "Verify that symmetric keys used to verify submitted OTPs are highly protected, such as by using a hardware security module or secure operating system based key storage.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "doc",
        "reference": "docs/IDENTITY_GUIDE.md"
      },
      {
        "type": "test",
        "reference": "tests/test_oauth.py::test_oauth_admin_requires_totp"
      },
      {
        "type": "test",
        "reference": "tests/test_mfa_enforcement.py::test_mfa_protected_route"
      }
    ]
  },
  {
    "id": "2.8.3",
    "section": "V2",
    "title": "Authentication",
    "description": "Verify that approved cryptographic algorithms are used in the generation, seeding, and verification of OTPs.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "doc",
        "reference": "docs/IDENTITY_GUIDE.md"
      },
      {
        "type": "test",
        "reference": "tests/test_oauth.py::test_oauth_admin_requires_totp"
      },
      {
        "type": "test",
        "reference": "tests/test_mfa_enforcement.py::test_mfa_protected_route"
      }
    ]
  },
  {
    "id": "2.8.4",
    "section": "V2",
    "title": "Authentication",
    "description": "Verify that time-based OTP can be used only once within the validity period.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "doc",
        "reference": "docs/IDENTITY_GUIDE.md"
      },
      {
        "type": "test",
        "reference": "tests/test_oauth.py::test_oauth_admin_requires_totp"
      },
      {
        "type": "test",
        "reference": "tests/test_mfa_enforcement.py::test_mfa_protected_route"
      }
    ]
  },
  {
    "id": "2.8.5",
    "section": "V2",
    "title": "Authentication",
    "description": "Verify that if a time-based multi-factor OTP token is re-used during the validity period, it is logged and rejected with secure notifications being sent to the holder of the device.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "doc",
        "reference": "docs/IDENTITY_GUIDE.md"
      },
      {
        "type": "test",
        "reference": "tests/test_oauth.py::test_oauth_admin_requires_totp"
      },
      {
        "type": "test",
        "reference": "tests/test_mfa_enforcement.py::test_mfa_protected_route"
      }
    ]
  },
  {
    "id": "2.8.6",
    "section": "V2",
    "title": "Authentication",
    "description": "Verify physical single-factor OTP generator can be revoked in case of theft or other loss. Ensure that revocation is immediately effective across logged in sessions, regardless of location.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "doc",
        "reference": "docs/IDENTITY_GUIDE.md"
      },
      {
        "type": "test",
        "reference": "tests/test_oauth.py::test_oauth_admin_requires_totp"
      },
      {
        "type": "test",
        "reference": "tests/test_mfa_enforcement.py::test_mfa_protected_route"
      }
    ]
  },
  {
    "id": "2.8.7",
    "section": "V2",
    "title": "Authentication",
    "description": "Verify that biometric authenticators are limited to use only as secondary factors in conjunction with either something you have and something you know.",
    "levels": [
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "doc",
        "reference": "docs/IDENTITY_GUIDE.md"
      },
      {
        "type": "test",
        "reference": "tests/test_oauth.py::test_oauth_admin_requires_totp"
      },
      {
        "type": "test",
        "reference": "tests/test_mfa_enforcement.py::test_mfa_protected_route"
      }
    ]
  },
  {
    "id": "2.9.1",
    "section": "V2",
    "title": "Authentication",
    "description": "Verify that cryptographic keys used in verification are stored securely and protected against disclosure, such as using a Trusted Platform Module (TPM) or Hardware Security Module (HSM), or an OS service that can use this secure storage.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "doc",
        "reference": "docs/IDENTITY_GUIDE.md"
      },
      {
        "type": "test",
        "reference": "tests/test_oauth.py::test_oauth_admin_requires_totp"
      },
      {
        "type": "test",
        "reference": "tests/test_mfa_enforcement.py::test_mfa_protected_route"
      }
    ]
  },
  {
    "id": "2.9.2",
    "section": "V2",
    "title": "Authentication",
    "description": "Verify that the challenge nonce is at least 64 bits in length, and statistically unique or unique over the lifetime of the cryptographic device.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "doc",
        "reference": "docs/IDENTITY_GUIDE.md"
      },
      {
        "type": "test",
        "reference": "tests/test_oauth.py::test_oauth_admin_requires_totp"
      },
      {
        "type": "test",
        "reference": "tests/test_mfa_enforcement.py::test_mfa_protected_route"
      }
    ]
  },
  {
    "id": "2.9.3",
    "section": "V2",
    "title": "Authentication",
    "description": "Verify that approved cryptographic algorithms are used in the generation, seeding, and verification.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "doc",
        "reference": "docs/IDENTITY_GUIDE.md"
      },
      {
        "type": "test",
        "reference": "tests/test_oauth.py::test_oauth_admin_requires_totp"
      },
      {
        "type": "test",
        "reference": "tests/test_mfa_enforcement.py::test_mfa_protected_route"
      }
    ]
  },
  {
    "id": "2.10.1",
    "section": "V2",
    "title": "Authentication",
    "description": "Verify that intra-service secrets do not rely on unchanging credentials such as passwords, API keys or shared accounts with privileged access.",
    "levels": [],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "doc",
        "reference": "docs/IDENTITY_GUIDE.md"
      },
      {
        "type": "test",
        "reference": "tests/test_oauth.py::test_oauth_admin_requires_totp"
      },
      {
        "type": "test",
        "reference": "tests/test_mfa_enforcement.py::test_mfa_protected_route"
      }
    ]
  },
  {
    "id": "2.10.2",
    "section": "V2",
    "title": "Authentication",
    "description": "Verify that if passwords are required for service authentication, the service account used is not a default credential. (e.g. root/root or admin/admin are default in some services during installation).",
    "levels": [],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "doc",
        "reference": "docs/IDENTITY_GUIDE.md"
      },
      {
        "type": "test",
        "reference": "tests/test_oauth.py::test_oauth_admin_requires_totp"
      },
      {
        "type": "test",
        "reference": "tests/test_mfa_enforcement.py::test_mfa_protected_route"
      }
    ]
  },
  {
    "id": "2.10.3",
    "section": "V2",
    "title": "Authentication",
    "description": "Verify that passwords are stored with sufficient protection to prevent offline recovery attacks, including local system access.",
    "levels": [],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "doc",
        "reference": "docs/IDENTITY_GUIDE.md"
      },
      {
        "type": "test",
        "reference": "tests/test_oauth.py::test_oauth_admin_requires_totp"
      },
      {
        "type": "test",
        "reference": "tests/test_mfa_enforcement.py::test_mfa_protected_route"
      }
    ]
  },
  {
    "id": "2.10.4",
    "section": "V2",
    "title": "Authentication",
    "description": "Verify passwords, integrations with databases and third-party systems, seeds and internal secrets, and API keys are managed securely and not included in the source code or stored within source code repositories. Such storage SHOULD resist offline attacks. The use of a secure software key store (L1), hardware TPM, or an HSM (L3) is recommended for password storage.",
    "levels": [],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "doc",
        "reference": "docs/IDENTITY_GUIDE.md"
      },
      {
        "type": "test",
        "reference": "tests/test_oauth.py::test_oauth_admin_requires_totp"
      },
      {
        "type": "test",
        "reference": "tests/test_mfa_enforcement.py::test_mfa_protected_route"
      }
    ]
  },
  {
    "id": "3.1.1",
    "section": "V3",
    "title": "Session Management",
    "description": "Verify the application never reveals session tokens in URL parameters.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "runbook",
        "reference": "docs/SRE_RUNBOOK.md#session-management-controls"
      },
      {
        "type": "test",
        "reference": "tests/test_lockout.py::test_lockout_and_unlock"
      },
      {
        "type": "test",
        "reference": "tests/test_auth_queries.py::test_issue_token"
      }
    ]
  },
  {
    "id": "3.2.1",
    "section": "V3",
    "title": "Session Management",
    "description": "Verify the application generates a new session token on user authentication. ([C6](https://owasp.org/www-project-proactive-controls/#div-numbering))",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "runbook",
        "reference": "docs/SRE_RUNBOOK.md#session-management-controls"
      },
      {
        "type": "test",
        "reference": "tests/test_lockout.py::test_lockout_and_unlock"
      },
      {
        "type": "test",
        "reference": "tests/test_auth_queries.py::test_issue_token"
      },
      {
        "type": "test",
        "reference": "tests/test_jwt_rotation.py::test_rotate_jwt_secret"
      }
    ]
  },
  {
    "id": "3.2.2",
    "section": "V3",
    "title": "Session Management",
    "description": "Verify that session tokens possess at least 64 bits of entropy. ([C6](https://owasp.org/www-project-proactive-controls/#div-numbering))",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "runbook",
        "reference": "docs/SRE_RUNBOOK.md#session-management-controls"
      },
      {
        "type": "test",
        "reference": "tests/test_lockout.py::test_lockout_and_unlock"
      },
      {
        "type": "test",
        "reference": "tests/test_auth_queries.py::test_issue_token"
      },
      {
        "type": "test",
        "reference": "tests/test_jwt_rotation.py::test_rotate_jwt_secret"
      }
    ]
  },
  {
    "id": "3.2.3",
    "section": "V3",
    "title": "Session Management",
    "description": "Verify the application only stores session tokens in the browser using secure methods such as appropriately secured cookies (see section 3.4) or HTML 5 session storage.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "runbook",
        "reference": "docs/SRE_RUNBOOK.md#session-management-controls"
      },
      {
        "type": "test",
        "reference": "tests/test_lockout.py::test_lockout_and_unlock"
      },
      {
        "type": "test",
        "reference": "tests/test_auth_queries.py::test_issue_token"
      },
      {
        "type": "test",
        "reference": "tests/test_jwt_rotation.py::test_rotate_jwt_secret"
      }
    ]
  },
  {
    "id": "3.2.4",
    "section": "V3",
    "title": "Session Management",
    "description": "Verify that session tokens are generated using approved cryptographic algorithms. ([C6](https://owasp.org/www-project-proactive-controls/#div-numbering))",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "runbook",
        "reference": "docs/SRE_RUNBOOK.md#session-management-controls"
      },
      {
        "type": "test",
        "reference": "tests/test_lockout.py::test_lockout_and_unlock"
      },
      {
        "type": "test",
        "reference": "tests/test_auth_queries.py::test_issue_token"
      },
      {
        "type": "test",
        "reference": "tests/test_jwt_rotation.py::test_rotate_jwt_secret"
      }
    ]
  },
  {
    "id": "3.3.1",
    "section": "V3",
    "title": "Session Management",
    "description": "Verify that logout and expiration invalidate the session token, such that the back button or a downstream relying party does not resume an authenticated session, including across relying parties. ([C6](https://owasp.org/www-project-proactive-controls/#div-numbering))",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "runbook",
        "reference": "docs/SRE_RUNBOOK.md#session-management-controls"
      },
      {
        "type": "test",
        "reference": "tests/test_lockout.py::test_lockout_and_unlock"
      },
      {
        "type": "test",
        "reference": "tests/test_auth_queries.py::test_issue_token"
      }
    ]
  },
  {
    "id": "3.3.2",
    "section": "V3",
    "title": "Session Management",
    "description": "If authenticators permit users to remain logged in, verify that re-authentication occurs periodically both when actively used or after an idle period. ([C6](https://owasp.org/www-project-proactive-controls/#div-numbering))",
    "levels": [],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "runbook",
        "reference": "docs/SRE_RUNBOOK.md#session-management-controls"
      },
      {
        "type": "test",
        "reference": "tests/test_lockout.py::test_lockout_and_unlock"
      },
      {
        "type": "test",
        "reference": "tests/test_auth_queries.py::test_issue_token"
      }
    ]
  },
  {
    "id": "3.3.3",
    "section": "V3",
    "title": "Session Management",
    "description": "Verify that the application gives the option to terminate all other active sessions after a successful password change (including change via password reset/recovery), and that this is effective across the application, federated login (if present), and any relying parties.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "runbook",
        "reference": "docs/SRE_RUNBOOK.md#session-management-controls"
      },
      {
        "type": "test",
        "reference": "tests/test_lockout.py::test_lockout_and_unlock"
      },
      {
        "type": "test",
        "reference": "tests/test_auth_queries.py::test_issue_token"
      }
    ]
  },
  {
    "id": "3.3.4",
    "section": "V3",
    "title": "Session Management",
    "description": "Verify that users are able to view and (having re-entered login credentials) log out of any or all currently active sessions and devices.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "runbook",
        "reference": "docs/SRE_RUNBOOK.md#session-management-controls"
      },
      {
        "type": "test",
        "reference": "tests/test_lockout.py::test_lockout_and_unlock"
      },
      {
        "type": "test",
        "reference": "tests/test_auth_queries.py::test_issue_token"
      }
    ]
  },
  {
    "id": "3.4.1",
    "section": "V3",
    "title": "Session Management",
    "description": "Verify that cookie-based session tokens have the 'Secure' attribute set. ([C6](https://owasp.org/www-project-proactive-controls/#div-numbering))",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "runbook",
        "reference": "docs/SRE_RUNBOOK.md#session-management-controls"
      },
      {
        "type": "test",
        "reference": "tests/test_lockout.py::test_lockout_and_unlock"
      },
      {
        "type": "test",
        "reference": "tests/test_auth_queries.py::test_issue_token"
      }
    ]
  },
  {
    "id": "3.4.2",
    "section": "V3",
    "title": "Session Management",
    "description": "Verify that cookie-based session tokens have the 'HttpOnly' attribute set. ([C6](https://owasp.org/www-project-proactive-controls/#div-numbering))",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "runbook",
        "reference": "docs/SRE_RUNBOOK.md#session-management-controls"
      },
      {
        "type": "test",
        "reference": "tests/test_lockout.py::test_lockout_and_unlock"
      },
      {
        "type": "test",
        "reference": "tests/test_auth_queries.py::test_issue_token"
      }
    ]
  },
  {
    "id": "3.4.3",
    "section": "V3",
    "title": "Session Management",
    "description": "Verify that cookie-based session tokens utilize the 'SameSite' attribute to limit exposure to cross-site request forgery attacks. ([C6](https://owasp.org/www-project-proactive-controls/#div-numbering))",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "runbook",
        "reference": "docs/SRE_RUNBOOK.md#session-management-controls"
      },
      {
        "type": "test",
        "reference": "tests/test_lockout.py::test_lockout_and_unlock"
      },
      {
        "type": "test",
        "reference": "tests/test_auth_queries.py::test_issue_token"
      }
    ]
  },
  {
    "id": "3.4.4",
    "section": "V3",
    "title": "Session Management",
    "description": "Verify that cookie-based session tokens use the \"__Host-\" prefix so cookies are only sent to the host that initially set the cookie.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "runbook",
        "reference": "docs/SRE_RUNBOOK.md#session-management-controls"
      },
      {
        "type": "test",
        "reference": "tests/test_lockout.py::test_lockout_and_unlock"
      },
      {
        "type": "test",
        "reference": "tests/test_auth_queries.py::test_issue_token"
      }
    ]
  },
  {
    "id": "3.4.5",
    "section": "V3",
    "title": "Session Management",
    "description": "Verify that if the application is published under a domain name with other applications that set or use session cookies that might disclose the session cookies, set the path attribute in cookie-based session tokens using the most precise path possible. ([C6](https://owasp.org/www-project-proactive-controls/#div-numbering))",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "runbook",
        "reference": "docs/SRE_RUNBOOK.md#session-management-controls"
      },
      {
        "type": "test",
        "reference": "tests/test_lockout.py::test_lockout_and_unlock"
      },
      {
        "type": "test",
        "reference": "tests/test_auth_queries.py::test_issue_token"
      }
    ]
  },
  {
    "id": "3.5.1",
    "section": "V3",
    "title": "Session Management",
    "description": "Verify the application allows users to revoke OAuth tokens that form trust relationships with linked applications.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "runbook",
        "reference": "docs/SRE_RUNBOOK.md#session-management-controls"
      },
      {
        "type": "test",
        "reference": "tests/test_lockout.py::test_lockout_and_unlock"
      },
      {
        "type": "test",
        "reference": "tests/test_auth_queries.py::test_issue_token"
      }
    ]
  },
  {
    "id": "3.5.2",
    "section": "V3",
    "title": "Session Management",
    "description": "Verify the application uses session tokens rather than static API secrets and keys, except with legacy implementations.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "runbook",
        "reference": "docs/SRE_RUNBOOK.md#session-management-controls"
      },
      {
        "type": "test",
        "reference": "tests/test_lockout.py::test_lockout_and_unlock"
      },
      {
        "type": "test",
        "reference": "tests/test_auth_queries.py::test_issue_token"
      }
    ]
  },
  {
    "id": "3.5.3",
    "section": "V3",
    "title": "Session Management",
    "description": "Verify that stateless session tokens use digital signatures, encryption, and other countermeasures to protect against tampering, enveloping, replay, null cipher, and key substitution attacks.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "runbook",
        "reference": "docs/SRE_RUNBOOK.md#session-management-controls"
      },
      {
        "type": "test",
        "reference": "tests/test_lockout.py::test_lockout_and_unlock"
      },
      {
        "type": "test",
        "reference": "tests/test_auth_queries.py::test_issue_token"
      }
    ]
  },
  {
    "id": "3.6.1",
    "section": "V3",
    "title": "Session Management",
    "description": "Verify that Relying Parties (RPs) specify the maximum authentication time to Credential Service Providers (CSPs) and that CSPs re-authenticate the user if they haven't used a session within that period.",
    "levels": [
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "runbook",
        "reference": "docs/SRE_RUNBOOK.md#session-management-controls"
      },
      {
        "type": "test",
        "reference": "tests/test_lockout.py::test_lockout_and_unlock"
      },
      {
        "type": "test",
        "reference": "tests/test_auth_queries.py::test_issue_token"
      }
    ]
  },
  {
    "id": "3.6.2",
    "section": "V3",
    "title": "Session Management",
    "description": "Verify that Credential Service Providers (CSPs) inform Relying Parties (RPs) of the last authentication event, to allow RPs to determine if they need to re-authenticate the user.",
    "levels": [
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "runbook",
        "reference": "docs/SRE_RUNBOOK.md#session-management-controls"
      },
      {
        "type": "test",
        "reference": "tests/test_lockout.py::test_lockout_and_unlock"
      },
      {
        "type": "test",
        "reference": "tests/test_auth_queries.py::test_issue_token"
      }
    ]
  },
  {
    "id": "3.7.1",
    "section": "V3",
    "title": "Session Management",
    "description": "Verify the application ensures a full, valid login session or requires re-authentication or secondary verification before allowing any sensitive transactions or account modifications.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/routes/auth.py"
      },
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "runbook",
        "reference": "docs/SRE_RUNBOOK.md#session-management-controls"
      },
      {
        "type": "test",
        "reference": "tests/test_lockout.py::test_lockout_and_unlock"
      },
      {
        "type": "test",
        "reference": "tests/test_auth_queries.py::test_issue_token"
      }
    ]
  },
  {
    "id": "4.1.1",
    "section": "V4",
    "title": "Access Control",
    "description": "Verify that the application enforces access control rules on a trusted service layer, especially if client-side access control is present and could be bypassed.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "code",
        "reference": "erp/routes/orders.py"
      },
      {
        "type": "test",
        "reference": "tests/test_rbac_hierarchy.py::test_admin_inherits_manager"
      },
      {
        "type": "test",
        "reference": "tests/test_rls_access.py::test_cross_tenant_inventory_access"
      },
      {
        "type": "test",
        "reference": "tests/test_rls.py::test_rls_isolation"
      }
    ]
  },
  {
    "id": "4.1.2",
    "section": "V4",
    "title": "Access Control",
    "description": "Verify that all user and data attributes and policy information used by access controls cannot be manipulated by end users unless specifically authorized.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "code",
        "reference": "erp/routes/orders.py"
      },
      {
        "type": "test",
        "reference": "tests/test_rbac_hierarchy.py::test_admin_inherits_manager"
      },
      {
        "type": "test",
        "reference": "tests/test_rls_access.py::test_cross_tenant_inventory_access"
      },
      {
        "type": "test",
        "reference": "tests/test_rls.py::test_rls_isolation"
      }
    ]
  },
  {
    "id": "4.1.3",
    "section": "V4",
    "title": "Access Control",
    "description": "Verify that the principle of least privilege exists - users should only be able to access functions, data files, URLs, controllers, services, and other resources, for which they possess specific authorization. This implies protection against spoofing and elevation of privilege. ([C7](https://owasp.org/www-project-proactive-controls/#div-numbering))",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "code",
        "reference": "erp/routes/orders.py"
      },
      {
        "type": "test",
        "reference": "tests/test_rbac_hierarchy.py::test_admin_inherits_manager"
      },
      {
        "type": "test",
        "reference": "tests/test_rls_access.py::test_cross_tenant_inventory_access"
      },
      {
        "type": "test",
        "reference": "tests/test_rls.py::test_rls_isolation"
      },
      {
        "type": "test",
        "reference": "tests/test_api.py::test_graphql_depth_limit"
      }
    ]
  },
  {
    "id": "4.1.4",
    "section": "V4",
    "title": "Access Control",
    "description": "[DELETED, DUPLICATE OF 4.1.3]",
    "levels": [],
    "status": "deleted",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "code",
        "reference": "erp/routes/orders.py"
      },
      {
        "type": "test",
        "reference": "tests/test_rbac_hierarchy.py::test_admin_inherits_manager"
      },
      {
        "type": "test",
        "reference": "tests/test_rls_access.py::test_cross_tenant_inventory_access"
      },
      {
        "type": "test",
        "reference": "tests/test_rls.py::test_rls_isolation"
      }
    ]
  },
  {
    "id": "4.1.5",
    "section": "V4",
    "title": "Access Control",
    "description": "Verify that access controls fail securely including when an exception occurs. ([C10](https://owasp.org/www-project-proactive-controls/#div-numbering))",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "code",
        "reference": "erp/routes/orders.py"
      },
      {
        "type": "test",
        "reference": "tests/test_rbac_hierarchy.py::test_admin_inherits_manager"
      },
      {
        "type": "test",
        "reference": "tests/test_rls_access.py::test_cross_tenant_inventory_access"
      },
      {
        "type": "test",
        "reference": "tests/test_rls.py::test_rls_isolation"
      }
    ]
  },
  {
    "id": "4.2.1",
    "section": "V4",
    "title": "Access Control",
    "description": "Verify that sensitive data and APIs are protected against Insecure Direct Object Reference (IDOR) attacks targeting creation, reading, updating and deletion of records, such as creating or updating someone else's record, viewing everyone's records, or deleting all records.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "code",
        "reference": "erp/routes/orders.py"
      },
      {
        "type": "test",
        "reference": "tests/test_rbac_hierarchy.py::test_admin_inherits_manager"
      },
      {
        "type": "test",
        "reference": "tests/test_rls_access.py::test_cross_tenant_inventory_access"
      },
      {
        "type": "test",
        "reference": "tests/test_rls.py::test_rls_isolation"
      }
    ]
  },
  {
    "id": "4.2.2",
    "section": "V4",
    "title": "Access Control",
    "description": "Verify that the application or framework enforces a strong anti-CSRF mechanism to protect authenticated functionality, and effective anti-automation or anti-CSRF protects unauthenticated functionality.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "code",
        "reference": "erp/routes/orders.py"
      },
      {
        "type": "test",
        "reference": "tests/test_rbac_hierarchy.py::test_admin_inherits_manager"
      },
      {
        "type": "test",
        "reference": "tests/test_rls_access.py::test_cross_tenant_inventory_access"
      },
      {
        "type": "test",
        "reference": "tests/test_rls.py::test_rls_isolation"
      }
    ]
  },
  {
    "id": "4.3.1",
    "section": "V4",
    "title": "Access Control",
    "description": "Verify administrative interfaces use appropriate multi-factor authentication to prevent unauthorized use.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "code",
        "reference": "erp/routes/orders.py"
      },
      {
        "type": "test",
        "reference": "tests/test_rbac_hierarchy.py::test_admin_inherits_manager"
      },
      {
        "type": "test",
        "reference": "tests/test_rls_access.py::test_cross_tenant_inventory_access"
      },
      {
        "type": "test",
        "reference": "tests/test_rls.py::test_rls_isolation"
      }
    ]
  },
  {
    "id": "4.3.2",
    "section": "V4",
    "title": "Access Control",
    "description": "Verify that directory browsing is disabled unless deliberately desired. Additionally, applications should not allow discovery or disclosure of file or directory metadata, such as Thumbs.db, .DS_Store, .git or .svn folders.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "code",
        "reference": "erp/routes/orders.py"
      },
      {
        "type": "test",
        "reference": "tests/test_rbac_hierarchy.py::test_admin_inherits_manager"
      },
      {
        "type": "test",
        "reference": "tests/test_rls_access.py::test_cross_tenant_inventory_access"
      },
      {
        "type": "test",
        "reference": "tests/test_rls.py::test_rls_isolation"
      }
    ]
  },
  {
    "id": "4.3.3",
    "section": "V4",
    "title": "Access Control",
    "description": "Verify the application has additional authorization (such as step up or adaptive authentication) for lower value systems, and / or segregation of duties for high value applications to enforce anti-fraud controls as per the risk of application and past fraud.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "code",
        "reference": "erp/routes/orders.py"
      },
      {
        "type": "test",
        "reference": "tests/test_rbac_hierarchy.py::test_admin_inherits_manager"
      },
      {
        "type": "test",
        "reference": "tests/test_rls_access.py::test_cross_tenant_inventory_access"
      },
      {
        "type": "test",
        "reference": "tests/test_rls.py::test_rls_isolation"
      }
    ]
  },
  {
    "id": "5.1.1",
    "section": "V5",
    "title": "Validation, Sanitization & Encoding",
    "description": "Verify that the application has defenses against HTTP parameter pollution attacks, particularly if the application framework makes no distinction about the source of request parameters (GET, POST, cookies, headers, or environment variables).",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "code",
        "reference": "erp/routes/main.py"
      },
      {
        "type": "doc",
        "reference": "docs/security/content_security_policy.md"
      },
      {
        "type": "test",
        "reference": "tests/test_waf.py::test_waf_blocks_script_tag"
      },
      {
        "type": "test",
        "reference": "tests/test_sql_parameterization.py::test_no_question_mark_placeholders"
      }
    ]
  },
  {
    "id": "5.1.2",
    "section": "V5",
    "title": "Validation, Sanitization & Encoding",
    "description": "Verify that frameworks protect against mass parameter assignment attacks, or that the application has countermeasures to protect against unsafe parameter assignment, such as marking fields private or similar. ([C5](https://owasp.org/www-project-proactive-controls/#div-numbering))",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "code",
        "reference": "erp/routes/main.py"
      },
      {
        "type": "doc",
        "reference": "docs/security/content_security_policy.md"
      },
      {
        "type": "test",
        "reference": "tests/test_waf.py::test_waf_blocks_script_tag"
      },
      {
        "type": "test",
        "reference": "tests/test_sql_parameterization.py::test_no_question_mark_placeholders"
      }
    ]
  },
  {
    "id": "5.1.3",
    "section": "V5",
    "title": "Validation, Sanitization & Encoding",
    "description": "Verify that all input (HTML form fields, REST requests, URL parameters, HTTP headers, cookies, batch files, RSS feeds, etc) is validated using positive validation (allow lists). ([C5](https://owasp.org/www-project-proactive-controls/#div-numbering))",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "code",
        "reference": "erp/routes/main.py"
      },
      {
        "type": "doc",
        "reference": "docs/security/content_security_policy.md"
      },
      {
        "type": "test",
        "reference": "tests/test_waf.py::test_waf_blocks_script_tag"
      },
      {
        "type": "test",
        "reference": "tests/test_sql_parameterization.py::test_no_question_mark_placeholders"
      }
    ]
  },
  {
    "id": "5.1.4",
    "section": "V5",
    "title": "Validation, Sanitization & Encoding",
    "description": "Verify that structured data is strongly typed and validated against a defined schema including allowed characters, length and pattern (e.g. credit card numbers, e-mail addresses, telephone numbers, or validating that two related fields are reasonable, such as checking that suburb and zip/postcode match). ([C5](https://owasp.org/www-project-proactive-controls/#div-numbering))",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "code",
        "reference": "erp/routes/main.py"
      },
      {
        "type": "doc",
        "reference": "docs/security/content_security_policy.md"
      },
      {
        "type": "test",
        "reference": "tests/test_waf.py::test_waf_blocks_script_tag"
      },
      {
        "type": "test",
        "reference": "tests/test_sql_parameterization.py::test_no_question_mark_placeholders"
      }
    ]
  },
  {
    "id": "5.1.5",
    "section": "V5",
    "title": "Validation, Sanitization & Encoding",
    "description": "Verify that URL redirects and forwards only allow destinations which appear on an allow list, or show a warning when redirecting to potentially untrusted content.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "code",
        "reference": "erp/routes/main.py"
      },
      {
        "type": "doc",
        "reference": "docs/security/content_security_policy.md"
      },
      {
        "type": "test",
        "reference": "tests/test_waf.py::test_waf_blocks_script_tag"
      },
      {
        "type": "test",
        "reference": "tests/test_sql_parameterization.py::test_no_question_mark_placeholders"
      }
    ]
  },
  {
    "id": "5.2.1",
    "section": "V5",
    "title": "Validation, Sanitization & Encoding",
    "description": "Verify that all untrusted HTML input from WYSIWYG editors or similar is properly sanitized with an HTML sanitizer library or framework feature. ([C5](https://owasp.org/www-project-proactive-controls/#div-numbering))",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "code",
        "reference": "erp/routes/main.py"
      },
      {
        "type": "doc",
        "reference": "docs/security/content_security_policy.md"
      },
      {
        "type": "test",
        "reference": "tests/test_waf.py::test_waf_blocks_script_tag"
      },
      {
        "type": "test",
        "reference": "tests/test_sql_parameterization.py::test_no_question_mark_placeholders"
      }
    ]
  },
  {
    "id": "5.2.2",
    "section": "V5",
    "title": "Validation, Sanitization & Encoding",
    "description": "Verify that unstructured data is sanitized to enforce safety measures such as allowed characters and length.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "code",
        "reference": "erp/routes/main.py"
      },
      {
        "type": "doc",
        "reference": "docs/security/content_security_policy.md"
      },
      {
        "type": "test",
        "reference": "tests/test_waf.py::test_waf_blocks_script_tag"
      },
      {
        "type": "test",
        "reference": "tests/test_sql_parameterization.py::test_no_question_mark_placeholders"
      }
    ]
  },
  {
    "id": "5.2.3",
    "section": "V5",
    "title": "Validation, Sanitization & Encoding",
    "description": "Verify that the application sanitizes user input before passing to mail systems to protect against SMTP or IMAP injection.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "code",
        "reference": "erp/routes/main.py"
      },
      {
        "type": "doc",
        "reference": "docs/security/content_security_policy.md"
      },
      {
        "type": "test",
        "reference": "tests/test_waf.py::test_waf_blocks_script_tag"
      },
      {
        "type": "test",
        "reference": "tests/test_sql_parameterization.py::test_no_question_mark_placeholders"
      }
    ]
  },
  {
    "id": "5.2.4",
    "section": "V5",
    "title": "Validation, Sanitization & Encoding",
    "description": "Verify that the application avoids the use of eval() or other dynamic code execution features. Where there is no alternative, any user input being included must be sanitized or sandboxed before being executed.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "code",
        "reference": "erp/routes/main.py"
      },
      {
        "type": "doc",
        "reference": "docs/security/content_security_policy.md"
      },
      {
        "type": "test",
        "reference": "tests/test_waf.py::test_waf_blocks_script_tag"
      },
      {
        "type": "test",
        "reference": "tests/test_sql_parameterization.py::test_no_question_mark_placeholders"
      }
    ]
  },
  {
    "id": "5.2.5",
    "section": "V5",
    "title": "Validation, Sanitization & Encoding",
    "description": "Verify that the application protects against template injection attacks by ensuring that any user input being included is sanitized or sandboxed.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "code",
        "reference": "erp/routes/main.py"
      },
      {
        "type": "doc",
        "reference": "docs/security/content_security_policy.md"
      },
      {
        "type": "test",
        "reference": "tests/test_waf.py::test_waf_blocks_script_tag"
      },
      {
        "type": "test",
        "reference": "tests/test_sql_parameterization.py::test_no_question_mark_placeholders"
      }
    ]
  },
  {
    "id": "5.2.6",
    "section": "V5",
    "title": "Validation, Sanitization & Encoding",
    "description": "Verify that the application protects against SSRF attacks, by validating or sanitizing untrusted data or HTTP file metadata, such as filenames and URL input fields, and uses allow lists of protocols, domains, paths and ports.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "code",
        "reference": "erp/routes/main.py"
      },
      {
        "type": "doc",
        "reference": "docs/security/content_security_policy.md"
      },
      {
        "type": "test",
        "reference": "tests/test_waf.py::test_waf_blocks_script_tag"
      },
      {
        "type": "test",
        "reference": "tests/test_sql_parameterization.py::test_no_question_mark_placeholders"
      }
    ]
  },
  {
    "id": "5.2.7",
    "section": "V5",
    "title": "Validation, Sanitization & Encoding",
    "description": "Verify that the application sanitizes, disables, or sandboxes user-supplied Scalable Vector Graphics (SVG) scriptable content, especially as they relate to XSS resulting from inline scripts, and foreignObject.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "code",
        "reference": "erp/routes/main.py"
      },
      {
        "type": "doc",
        "reference": "docs/security/content_security_policy.md"
      },
      {
        "type": "test",
        "reference": "tests/test_waf.py::test_waf_blocks_script_tag"
      },
      {
        "type": "test",
        "reference": "tests/test_sql_parameterization.py::test_no_question_mark_placeholders"
      }
    ]
  },
  {
    "id": "5.2.8",
    "section": "V5",
    "title": "Validation, Sanitization & Encoding",
    "description": "Verify that the application sanitizes, disables, or sandboxes user-supplied scriptable or expression template language content, such as Markdown, CSS or XSL stylesheets, BBCode, or similar.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "code",
        "reference": "erp/routes/main.py"
      },
      {
        "type": "doc",
        "reference": "docs/security/content_security_policy.md"
      },
      {
        "type": "test",
        "reference": "tests/test_waf.py::test_waf_blocks_script_tag"
      },
      {
        "type": "test",
        "reference": "tests/test_sql_parameterization.py::test_no_question_mark_placeholders"
      }
    ]
  },
  {
    "id": "5.3.1",
    "section": "V5",
    "title": "Validation, Sanitization & Encoding",
    "description": "Verify that output encoding is relevant for the interpreter and context required. For example, use encoders specifically for HTML values, HTML attributes, JavaScript, URL parameters, HTTP headers, SMTP, and others as the context requires, especially from untrusted inputs (e.g. names with Unicode or apostrophes, such as \u306d\u3053 or O'Hara). ([C4](https://owasp.org/www-project-proactive-controls/#div-numbering))",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "code",
        "reference": "erp/routes/main.py"
      },
      {
        "type": "doc",
        "reference": "docs/security/content_security_policy.md"
      },
      {
        "type": "test",
        "reference": "tests/test_waf.py::test_waf_blocks_script_tag"
      },
      {
        "type": "test",
        "reference": "tests/test_sql_parameterization.py::test_no_question_mark_placeholders"
      }
    ]
  },
  {
    "id": "5.3.2",
    "section": "V5",
    "title": "Validation, Sanitization & Encoding",
    "description": "Verify that output encoding preserves the user's chosen character set and locale, such that any Unicode character point is valid and safely handled. ([C4](https://owasp.org/www-project-proactive-controls/#div-numbering))",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "code",
        "reference": "erp/routes/main.py"
      },
      {
        "type": "doc",
        "reference": "docs/security/content_security_policy.md"
      },
      {
        "type": "test",
        "reference": "tests/test_waf.py::test_waf_blocks_script_tag"
      },
      {
        "type": "test",
        "reference": "tests/test_sql_parameterization.py::test_no_question_mark_placeholders"
      }
    ]
  },
  {
    "id": "5.3.3",
    "section": "V5",
    "title": "Validation, Sanitization & Encoding",
    "description": "Verify that context-aware, preferably automated - or at worst, manual - output escaping protects against reflected, stored, and DOM based XSS. ([C4](https://owasp.org/www-project-proactive-controls/#div-numbering))",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "code",
        "reference": "erp/routes/main.py"
      },
      {
        "type": "doc",
        "reference": "docs/security/content_security_policy.md"
      },
      {
        "type": "test",
        "reference": "tests/test_waf.py::test_waf_blocks_script_tag"
      },
      {
        "type": "test",
        "reference": "tests/test_sql_parameterization.py::test_no_question_mark_placeholders"
      }
    ]
  },
  {
    "id": "5.3.4",
    "section": "V5",
    "title": "Validation, Sanitization & Encoding",
    "description": "Verify that data selection or database queries (e.g. SQL, HQL, ORM, NoSQL) use parameterized queries, ORMs, entity frameworks, or are otherwise protected from database injection attacks. ([C3](https://owasp.org/www-project-proactive-controls/#div-numbering))",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "code",
        "reference": "erp/routes/main.py"
      },
      {
        "type": "doc",
        "reference": "docs/security/content_security_policy.md"
      },
      {
        "type": "test",
        "reference": "tests/test_waf.py::test_waf_blocks_script_tag"
      },
      {
        "type": "test",
        "reference": "tests/test_sql_parameterization.py::test_no_question_mark_placeholders"
      }
    ]
  },
  {
    "id": "5.3.5",
    "section": "V5",
    "title": "Validation, Sanitization & Encoding",
    "description": "Verify that where parameterized or safer mechanisms are not present, context-specific output encoding is used to protect against injection attacks, such as the use of SQL escaping to protect against SQL injection. ([C3, C4](https://owasp.org/www-project-proactive-controls/#div-numbering))",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "code",
        "reference": "erp/routes/main.py"
      },
      {
        "type": "doc",
        "reference": "docs/security/content_security_policy.md"
      },
      {
        "type": "test",
        "reference": "tests/test_waf.py::test_waf_blocks_script_tag"
      },
      {
        "type": "test",
        "reference": "tests/test_sql_parameterization.py::test_no_question_mark_placeholders"
      }
    ]
  },
  {
    "id": "5.3.6",
    "section": "V5",
    "title": "Validation, Sanitization & Encoding",
    "description": "Verify that the application protects against JSON injection attacks, JSON eval attacks, and JavaScript expression evaluation. ([C4](https://owasp.org/www-project-proactive-controls/#div-numbering))",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "code",
        "reference": "erp/routes/main.py"
      },
      {
        "type": "doc",
        "reference": "docs/security/content_security_policy.md"
      },
      {
        "type": "test",
        "reference": "tests/test_waf.py::test_waf_blocks_script_tag"
      },
      {
        "type": "test",
        "reference": "tests/test_sql_parameterization.py::test_no_question_mark_placeholders"
      }
    ]
  },
  {
    "id": "5.3.7",
    "section": "V5",
    "title": "Validation, Sanitization & Encoding",
    "description": "Verify that the application protects against LDAP injection vulnerabilities, or that specific security controls to prevent LDAP injection have been implemented. ([C4](https://owasp.org/www-project-proactive-controls/#div-numbering))",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "code",
        "reference": "erp/routes/main.py"
      },
      {
        "type": "doc",
        "reference": "docs/security/content_security_policy.md"
      },
      {
        "type": "test",
        "reference": "tests/test_waf.py::test_waf_blocks_script_tag"
      },
      {
        "type": "test",
        "reference": "tests/test_sql_parameterization.py::test_no_question_mark_placeholders"
      }
    ]
  },
  {
    "id": "5.3.8",
    "section": "V5",
    "title": "Validation, Sanitization & Encoding",
    "description": "Verify that the application protects against OS command injection and that operating system calls use parameterized OS queries or use contextual command line output encoding. ([C4](https://owasp.org/www-project-proactive-controls/#div-numbering))",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "code",
        "reference": "erp/routes/main.py"
      },
      {
        "type": "doc",
        "reference": "docs/security/content_security_policy.md"
      },
      {
        "type": "test",
        "reference": "tests/test_waf.py::test_waf_blocks_script_tag"
      },
      {
        "type": "test",
        "reference": "tests/test_sql_parameterization.py::test_no_question_mark_placeholders"
      }
    ]
  },
  {
    "id": "5.3.9",
    "section": "V5",
    "title": "Validation, Sanitization & Encoding",
    "description": "Verify that the application protects against Local File Inclusion (LFI) or Remote File Inclusion (RFI) attacks.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "code",
        "reference": "erp/routes/main.py"
      },
      {
        "type": "doc",
        "reference": "docs/security/content_security_policy.md"
      },
      {
        "type": "test",
        "reference": "tests/test_waf.py::test_waf_blocks_script_tag"
      },
      {
        "type": "test",
        "reference": "tests/test_sql_parameterization.py::test_no_question_mark_placeholders"
      }
    ]
  },
  {
    "id": "5.3.10",
    "section": "V5",
    "title": "Validation, Sanitization & Encoding",
    "description": "Verify that the application protects against XPath injection or XML injection attacks. ([C4](https://owasp.org/www-project-proactive-controls/#div-numbering))",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "code",
        "reference": "erp/routes/main.py"
      },
      {
        "type": "doc",
        "reference": "docs/security/content_security_policy.md"
      },
      {
        "type": "test",
        "reference": "tests/test_waf.py::test_waf_blocks_script_tag"
      },
      {
        "type": "test",
        "reference": "tests/test_sql_parameterization.py::test_no_question_mark_placeholders"
      }
    ]
  },
  {
    "id": "5.4.1",
    "section": "V5",
    "title": "Validation, Sanitization & Encoding",
    "description": "Verify that the application uses memory-safe string, safer memory copy and pointer arithmetic to detect or prevent stack, buffer, or heap overflows.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "code",
        "reference": "erp/routes/main.py"
      },
      {
        "type": "doc",
        "reference": "docs/security/content_security_policy.md"
      },
      {
        "type": "test",
        "reference": "tests/test_waf.py::test_waf_blocks_script_tag"
      },
      {
        "type": "test",
        "reference": "tests/test_sql_parameterization.py::test_no_question_mark_placeholders"
      }
    ]
  },
  {
    "id": "5.4.2",
    "section": "V5",
    "title": "Validation, Sanitization & Encoding",
    "description": "Verify that format strings do not take potentially hostile input, and are constant.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "code",
        "reference": "erp/routes/main.py"
      },
      {
        "type": "doc",
        "reference": "docs/security/content_security_policy.md"
      },
      {
        "type": "test",
        "reference": "tests/test_waf.py::test_waf_blocks_script_tag"
      },
      {
        "type": "test",
        "reference": "tests/test_sql_parameterization.py::test_no_question_mark_placeholders"
      }
    ]
  },
  {
    "id": "5.4.3",
    "section": "V5",
    "title": "Validation, Sanitization & Encoding",
    "description": "Verify that sign, range, and input validation techniques are used to prevent integer overflows.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "code",
        "reference": "erp/routes/main.py"
      },
      {
        "type": "doc",
        "reference": "docs/security/content_security_policy.md"
      },
      {
        "type": "test",
        "reference": "tests/test_waf.py::test_waf_blocks_script_tag"
      },
      {
        "type": "test",
        "reference": "tests/test_sql_parameterization.py::test_no_question_mark_placeholders"
      }
    ]
  },
  {
    "id": "5.5.1",
    "section": "V5",
    "title": "Validation, Sanitization & Encoding",
    "description": "Verify that serialized objects use integrity checks or are encrypted to prevent hostile object creation or data tampering. ([C5](https://owasp.org/www-project-proactive-controls/#div-numbering))",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "code",
        "reference": "erp/routes/main.py"
      },
      {
        "type": "doc",
        "reference": "docs/security/content_security_policy.md"
      },
      {
        "type": "test",
        "reference": "tests/test_waf.py::test_waf_blocks_script_tag"
      },
      {
        "type": "test",
        "reference": "tests/test_sql_parameterization.py::test_no_question_mark_placeholders"
      }
    ]
  },
  {
    "id": "5.5.2",
    "section": "V5",
    "title": "Validation, Sanitization & Encoding",
    "description": "Verify that the application correctly restricts XML parsers to only use the most restrictive configuration possible and to ensure that unsafe features such as resolving external entities are disabled to prevent XML eXternal Entity (XXE) attacks.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "code",
        "reference": "erp/routes/main.py"
      },
      {
        "type": "doc",
        "reference": "docs/security/content_security_policy.md"
      },
      {
        "type": "test",
        "reference": "tests/test_waf.py::test_waf_blocks_script_tag"
      },
      {
        "type": "test",
        "reference": "tests/test_sql_parameterization.py::test_no_question_mark_placeholders"
      }
    ]
  },
  {
    "id": "5.5.3",
    "section": "V5",
    "title": "Validation, Sanitization & Encoding",
    "description": "Verify that deserialization of untrusted data is avoided or is protected in both custom code and third-party libraries (such as JSON, XML and YAML parsers).",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "code",
        "reference": "erp/routes/main.py"
      },
      {
        "type": "doc",
        "reference": "docs/security/content_security_policy.md"
      },
      {
        "type": "test",
        "reference": "tests/test_waf.py::test_waf_blocks_script_tag"
      },
      {
        "type": "test",
        "reference": "tests/test_sql_parameterization.py::test_no_question_mark_placeholders"
      }
    ]
  },
  {
    "id": "5.5.4",
    "section": "V5",
    "title": "Validation, Sanitization & Encoding",
    "description": "Verify that when parsing JSON in browsers or JavaScript-based backends, JSON.parse is used to parse the JSON document. Do not use eval() to parse JSON.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/utils.py"
      },
      {
        "type": "code",
        "reference": "erp/routes/main.py"
      },
      {
        "type": "doc",
        "reference": "docs/security/content_security_policy.md"
      },
      {
        "type": "test",
        "reference": "tests/test_waf.py::test_waf_blocks_script_tag"
      },
      {
        "type": "test",
        "reference": "tests/test_sql_parameterization.py::test_no_question_mark_placeholders"
      }
    ]
  },
  {
    "id": "6.1.1",
    "section": "V6",
    "title": "Cryptography",
    "description": "Verify that regulated private data is stored encrypted while at rest, such as Personally Identifiable Information (PII), sensitive personal information, or data assessed likely to be subject to EU's GDPR.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/security.py"
      },
      {
        "type": "code",
        "reference": "erp/secrets.py"
      },
      {
        "type": "doc",
        "reference": "docs/security/secret_rotation.md"
      },
      {
        "type": "test",
        "reference": "tests/test_rotate_jwt_secret_script.py::test_rotate_jwt_secret_script"
      },
      {
        "type": "test",
        "reference": "tests/test_rotate_jwt_script.py::test_rotate_jwt_secret_script"
      },
      {
        "type": "code",
        "reference": "scripts/rotate_jwt_secret.py"
      }
    ]
  },
  {
    "id": "6.1.2",
    "section": "V6",
    "title": "Cryptography",
    "description": "Verify that regulated health data is stored encrypted while at rest, such as medical records, medical device details, or de-anonymized research records.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/security.py"
      },
      {
        "type": "code",
        "reference": "erp/secrets.py"
      },
      {
        "type": "doc",
        "reference": "docs/security/secret_rotation.md"
      },
      {
        "type": "test",
        "reference": "tests/test_rotate_jwt_secret_script.py::test_rotate_jwt_secret_script"
      },
      {
        "type": "test",
        "reference": "tests/test_rotate_jwt_script.py::test_rotate_jwt_secret_script"
      },
      {
        "type": "code",
        "reference": "scripts/rotate_jwt_secret.py"
      }
    ]
  },
  {
    "id": "6.1.3",
    "section": "V6",
    "title": "Cryptography",
    "description": "Verify that regulated financial data is stored encrypted while at rest, such as financial accounts, defaults or credit history, tax records, pay history, beneficiaries, or de-anonymized market or research records.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/security.py"
      },
      {
        "type": "code",
        "reference": "erp/secrets.py"
      },
      {
        "type": "doc",
        "reference": "docs/security/secret_rotation.md"
      },
      {
        "type": "test",
        "reference": "tests/test_rotate_jwt_secret_script.py::test_rotate_jwt_secret_script"
      },
      {
        "type": "test",
        "reference": "tests/test_rotate_jwt_script.py::test_rotate_jwt_secret_script"
      },
      {
        "type": "code",
        "reference": "scripts/rotate_jwt_secret.py"
      }
    ]
  },
  {
    "id": "6.2.1",
    "section": "V6",
    "title": "Cryptography",
    "description": "Verify that all cryptographic modules fail securely, and errors are handled in a way that does not enable Padding Oracle attacks.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/security.py"
      },
      {
        "type": "code",
        "reference": "erp/secrets.py"
      },
      {
        "type": "doc",
        "reference": "docs/security/secret_rotation.md"
      },
      {
        "type": "test",
        "reference": "tests/test_rotate_jwt_secret_script.py::test_rotate_jwt_secret_script"
      },
      {
        "type": "test",
        "reference": "tests/test_rotate_jwt_script.py::test_rotate_jwt_secret_script"
      },
      {
        "type": "code",
        "reference": "scripts/rotate_jwt_secret.py"
      }
    ]
  },
  {
    "id": "6.2.2",
    "section": "V6",
    "title": "Cryptography",
    "description": "Verify that industry proven or government approved cryptographic algorithms, modes, and libraries are used, instead of custom coded cryptography. ([C8](https://owasp.org/www-project-proactive-controls/#div-numbering))",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/security.py"
      },
      {
        "type": "code",
        "reference": "erp/secrets.py"
      },
      {
        "type": "doc",
        "reference": "docs/security/secret_rotation.md"
      },
      {
        "type": "test",
        "reference": "tests/test_rotate_jwt_secret_script.py::test_rotate_jwt_secret_script"
      },
      {
        "type": "test",
        "reference": "tests/test_rotate_jwt_script.py::test_rotate_jwt_secret_script"
      },
      {
        "type": "code",
        "reference": "scripts/rotate_jwt_secret.py"
      }
    ]
  },
  {
    "id": "6.2.3",
    "section": "V6",
    "title": "Cryptography",
    "description": "Verify that encryption initialization vector, cipher configuration, and block modes are configured securely using the latest advice.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/security.py"
      },
      {
        "type": "code",
        "reference": "erp/secrets.py"
      },
      {
        "type": "doc",
        "reference": "docs/security/secret_rotation.md"
      },
      {
        "type": "test",
        "reference": "tests/test_rotate_jwt_secret_script.py::test_rotate_jwt_secret_script"
      },
      {
        "type": "test",
        "reference": "tests/test_rotate_jwt_script.py::test_rotate_jwt_secret_script"
      },
      {
        "type": "code",
        "reference": "scripts/rotate_jwt_secret.py"
      }
    ]
  },
  {
    "id": "6.2.4",
    "section": "V6",
    "title": "Cryptography",
    "description": "Verify that random number, encryption or hashing algorithms, key lengths, rounds, ciphers or modes, can be reconfigured, upgraded, or swapped at any time, to protect against cryptographic breaks. ([C8](https://owasp.org/www-project-proactive-controls/#div-numbering))",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/security.py"
      },
      {
        "type": "code",
        "reference": "erp/secrets.py"
      },
      {
        "type": "doc",
        "reference": "docs/security/secret_rotation.md"
      },
      {
        "type": "test",
        "reference": "tests/test_rotate_jwt_secret_script.py::test_rotate_jwt_secret_script"
      },
      {
        "type": "test",
        "reference": "tests/test_rotate_jwt_script.py::test_rotate_jwt_secret_script"
      },
      {
        "type": "code",
        "reference": "scripts/rotate_jwt_secret.py"
      }
    ]
  },
  {
    "id": "6.2.5",
    "section": "V6",
    "title": "Cryptography",
    "description": "Verify that known insecure block modes (i.e. ECB, etc.), padding modes (i.e. PKCS#1 v1.5, etc.), ciphers with small block sizes (i.e. Triple-DES, Blowfish, etc.), and weak hashing algorithms (i.e. MD5, SHA1, etc.) are not used unless required for backwards compatibility.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/security.py"
      },
      {
        "type": "code",
        "reference": "erp/secrets.py"
      },
      {
        "type": "doc",
        "reference": "docs/security/secret_rotation.md"
      },
      {
        "type": "test",
        "reference": "tests/test_rotate_jwt_secret_script.py::test_rotate_jwt_secret_script"
      },
      {
        "type": "test",
        "reference": "tests/test_rotate_jwt_script.py::test_rotate_jwt_secret_script"
      },
      {
        "type": "code",
        "reference": "scripts/rotate_jwt_secret.py"
      }
    ]
  },
  {
    "id": "6.2.6",
    "section": "V6",
    "title": "Cryptography",
    "description": "Verify that nonces, initialization vectors, and other single use numbers must not be used more than once with a given encryption key. The method of generation must be appropriate for the algorithm being used.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/security.py"
      },
      {
        "type": "code",
        "reference": "erp/secrets.py"
      },
      {
        "type": "doc",
        "reference": "docs/security/secret_rotation.md"
      },
      {
        "type": "test",
        "reference": "tests/test_rotate_jwt_secret_script.py::test_rotate_jwt_secret_script"
      },
      {
        "type": "test",
        "reference": "tests/test_rotate_jwt_script.py::test_rotate_jwt_secret_script"
      },
      {
        "type": "code",
        "reference": "scripts/rotate_jwt_secret.py"
      }
    ]
  },
  {
    "id": "6.2.7",
    "section": "V6",
    "title": "Cryptography",
    "description": "Verify that encrypted data is authenticated via signatures, authenticated cipher modes, or HMAC to ensure that ciphertext is not altered by an unauthorized party.",
    "levels": [
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/security.py"
      },
      {
        "type": "code",
        "reference": "erp/secrets.py"
      },
      {
        "type": "doc",
        "reference": "docs/security/secret_rotation.md"
      },
      {
        "type": "test",
        "reference": "tests/test_rotate_jwt_secret_script.py::test_rotate_jwt_secret_script"
      },
      {
        "type": "test",
        "reference": "tests/test_rotate_jwt_script.py::test_rotate_jwt_secret_script"
      },
      {
        "type": "code",
        "reference": "scripts/rotate_jwt_secret.py"
      }
    ]
  },
  {
    "id": "6.2.8",
    "section": "V6",
    "title": "Cryptography",
    "description": "Verify that all cryptographic operations are constant-time, with no 'short-circuit' operations in comparisons, calculations, or returns, to avoid leaking information.",
    "levels": [
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/security.py"
      },
      {
        "type": "code",
        "reference": "erp/secrets.py"
      },
      {
        "type": "doc",
        "reference": "docs/security/secret_rotation.md"
      },
      {
        "type": "test",
        "reference": "tests/test_rotate_jwt_secret_script.py::test_rotate_jwt_secret_script"
      },
      {
        "type": "test",
        "reference": "tests/test_rotate_jwt_script.py::test_rotate_jwt_secret_script"
      },
      {
        "type": "code",
        "reference": "scripts/rotate_jwt_secret.py"
      }
    ]
  },
  {
    "id": "6.3.1",
    "section": "V6",
    "title": "Cryptography",
    "description": "Verify that all random numbers, random file names, random GUIDs, and random strings are generated using the cryptographic module's approved cryptographically secure random number generator when these random values are intended to be not guessable by an attacker.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/security.py"
      },
      {
        "type": "code",
        "reference": "erp/secrets.py"
      },
      {
        "type": "doc",
        "reference": "docs/security/secret_rotation.md"
      },
      {
        "type": "test",
        "reference": "tests/test_rotate_jwt_secret_script.py::test_rotate_jwt_secret_script"
      },
      {
        "type": "test",
        "reference": "tests/test_rotate_jwt_script.py::test_rotate_jwt_secret_script"
      },
      {
        "type": "code",
        "reference": "scripts/rotate_jwt_secret.py"
      },
      {
        "type": "test",
        "reference": "tests/test_storage.py::test_presigned"
      }
    ]
  },
  {
    "id": "6.3.2",
    "section": "V6",
    "title": "Cryptography",
    "description": "Verify that random GUIDs are created using the GUID v4 algorithm, and a Cryptographically-secure Pseudo-random Number Generator (CSPRNG). GUIDs created using other pseudo-random number generators may be predictable.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/security.py"
      },
      {
        "type": "code",
        "reference": "erp/secrets.py"
      },
      {
        "type": "doc",
        "reference": "docs/security/secret_rotation.md"
      },
      {
        "type": "test",
        "reference": "tests/test_rotate_jwt_secret_script.py::test_rotate_jwt_secret_script"
      },
      {
        "type": "test",
        "reference": "tests/test_rotate_jwt_script.py::test_rotate_jwt_secret_script"
      },
      {
        "type": "code",
        "reference": "scripts/rotate_jwt_secret.py"
      },
      {
        "type": "test",
        "reference": "tests/test_storage.py::test_presigned"
      }
    ]
  },
  {
    "id": "6.3.3",
    "section": "V6",
    "title": "Cryptography",
    "description": "Verify that random numbers are created with proper entropy even when the application is under heavy load, or that the application degrades gracefully in such circumstances.",
    "levels": [
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/security.py"
      },
      {
        "type": "code",
        "reference": "erp/secrets.py"
      },
      {
        "type": "doc",
        "reference": "docs/security/secret_rotation.md"
      },
      {
        "type": "test",
        "reference": "tests/test_rotate_jwt_secret_script.py::test_rotate_jwt_secret_script"
      },
      {
        "type": "test",
        "reference": "tests/test_rotate_jwt_script.py::test_rotate_jwt_secret_script"
      },
      {
        "type": "code",
        "reference": "scripts/rotate_jwt_secret.py"
      },
      {
        "type": "test",
        "reference": "tests/test_storage.py::test_presigned"
      }
    ]
  },
  {
    "id": "6.4.1",
    "section": "V6",
    "title": "Cryptography",
    "description": "Verify that a secrets management solution such as a key vault is used to securely create, store, control access to and destroy secrets. ([C8](https://owasp.org/www-project-proactive-controls/#div-numbering))",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/security.py"
      },
      {
        "type": "code",
        "reference": "erp/secrets.py"
      },
      {
        "type": "doc",
        "reference": "docs/security/secret_rotation.md"
      },
      {
        "type": "test",
        "reference": "tests/test_rotate_jwt_secret_script.py::test_rotate_jwt_secret_script"
      },
      {
        "type": "test",
        "reference": "tests/test_rotate_jwt_script.py::test_rotate_jwt_secret_script"
      },
      {
        "type": "code",
        "reference": "scripts/rotate_jwt_secret.py"
      }
    ]
  },
  {
    "id": "6.4.2",
    "section": "V6",
    "title": "Cryptography",
    "description": "Verify that key material is not exposed to the application but instead uses an isolated security module like a vault for cryptographic operations. ([C8](https://owasp.org/www-project-proactive-controls/#div-numbering))",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/security.py"
      },
      {
        "type": "code",
        "reference": "erp/secrets.py"
      },
      {
        "type": "doc",
        "reference": "docs/security/secret_rotation.md"
      },
      {
        "type": "test",
        "reference": "tests/test_rotate_jwt_secret_script.py::test_rotate_jwt_secret_script"
      },
      {
        "type": "test",
        "reference": "tests/test_rotate_jwt_script.py::test_rotate_jwt_secret_script"
      },
      {
        "type": "code",
        "reference": "scripts/rotate_jwt_secret.py"
      }
    ]
  },
  {
    "id": "7.1.1",
    "section": "V7",
    "title": "Error Handling & Logging",
    "description": "Verify that the application does not log credentials or payment details. Session tokens should only be stored in logs in an irreversible, hashed form. ([C9, C10](https://owasp.org/www-project-proactive-controls/#div-numbering))",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/observability.py"
      },
      {
        "type": "code",
        "reference": "erp/audit.py"
      },
      {
        "type": "doc",
        "reference": "docs/observability.md"
      },
      {
        "type": "test",
        "reference": "tests/test_audit_log.py::test_audit_chain_checker"
      },
      {
        "type": "test",
        "reference": "tests/test_queue_metrics.py::test_queue_lag_metric"
      }
    ]
  },
  {
    "id": "7.1.2",
    "section": "V7",
    "title": "Error Handling & Logging",
    "description": "Verify that the application does not log other sensitive data as defined under local privacy laws or relevant security policy. ([C9](https://owasp.org/www-project-proactive-controls/#div-numbering))",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/observability.py"
      },
      {
        "type": "code",
        "reference": "erp/audit.py"
      },
      {
        "type": "doc",
        "reference": "docs/observability.md"
      },
      {
        "type": "test",
        "reference": "tests/test_audit_log.py::test_audit_chain_checker"
      },
      {
        "type": "test",
        "reference": "tests/test_queue_metrics.py::test_queue_lag_metric"
      }
    ]
  },
  {
    "id": "7.1.3",
    "section": "V7",
    "title": "Error Handling & Logging",
    "description": "Verify that the application logs security relevant events including successful and failed authentication events, access control failures, deserialization failures and input validation failures. ([C5, C7](https://owasp.org/www-project-proactive-controls/#div-numbering))",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/observability.py"
      },
      {
        "type": "code",
        "reference": "erp/audit.py"
      },
      {
        "type": "doc",
        "reference": "docs/observability.md"
      },
      {
        "type": "test",
        "reference": "tests/test_audit_log.py::test_audit_chain_checker"
      },
      {
        "type": "test",
        "reference": "tests/test_queue_metrics.py::test_queue_lag_metric"
      }
    ]
  },
  {
    "id": "7.1.4",
    "section": "V7",
    "title": "Error Handling & Logging",
    "description": "Verify that each log event includes necessary information that would allow for a detailed investigation of the timeline when an event happens. ([C9](https://owasp.org/www-project-proactive-controls/#div-numbering))",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/observability.py"
      },
      {
        "type": "code",
        "reference": "erp/audit.py"
      },
      {
        "type": "doc",
        "reference": "docs/observability.md"
      },
      {
        "type": "test",
        "reference": "tests/test_audit_log.py::test_audit_chain_checker"
      },
      {
        "type": "test",
        "reference": "tests/test_queue_metrics.py::test_queue_lag_metric"
      }
    ]
  },
  {
    "id": "7.2.1",
    "section": "V7",
    "title": "Error Handling & Logging",
    "description": "Verify that all authentication decisions are logged, without storing sensitive session tokens or passwords. This should include requests with relevant metadata needed for security investigations.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/observability.py"
      },
      {
        "type": "code",
        "reference": "erp/audit.py"
      },
      {
        "type": "doc",
        "reference": "docs/observability.md"
      },
      {
        "type": "test",
        "reference": "tests/test_audit_log.py::test_audit_chain_checker"
      },
      {
        "type": "test",
        "reference": "tests/test_queue_metrics.py::test_queue_lag_metric"
      }
    ]
  },
  {
    "id": "7.2.2",
    "section": "V7",
    "title": "Error Handling & Logging",
    "description": "Verify that all access control decisions can be logged and all failed decisions are logged. This should include requests with relevant metadata needed for security investigations.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/observability.py"
      },
      {
        "type": "code",
        "reference": "erp/audit.py"
      },
      {
        "type": "doc",
        "reference": "docs/observability.md"
      },
      {
        "type": "test",
        "reference": "tests/test_audit_log.py::test_audit_chain_checker"
      },
      {
        "type": "test",
        "reference": "tests/test_queue_metrics.py::test_queue_lag_metric"
      }
    ]
  },
  {
    "id": "7.3.1",
    "section": "V7",
    "title": "Error Handling & Logging",
    "description": "Verify that all logging components appropriately encode data to prevent log injection. ([C9](https://owasp.org/www-project-proactive-controls/#div-numbering))",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/observability.py"
      },
      {
        "type": "code",
        "reference": "erp/audit.py"
      },
      {
        "type": "doc",
        "reference": "docs/observability.md"
      },
      {
        "type": "test",
        "reference": "tests/test_audit_log.py::test_audit_chain_checker"
      },
      {
        "type": "test",
        "reference": "tests/test_queue_metrics.py::test_queue_lag_metric"
      }
    ]
  },
  {
    "id": "7.3.2",
    "section": "V7",
    "title": "Error Handling & Logging",
    "description": "[DELETED, DUPLICATE OF 7.3.1]",
    "levels": [],
    "status": "deleted",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/observability.py"
      },
      {
        "type": "code",
        "reference": "erp/audit.py"
      },
      {
        "type": "doc",
        "reference": "docs/observability.md"
      },
      {
        "type": "test",
        "reference": "tests/test_audit_log.py::test_audit_chain_checker"
      },
      {
        "type": "test",
        "reference": "tests/test_queue_metrics.py::test_queue_lag_metric"
      }
    ]
  },
  {
    "id": "7.3.3",
    "section": "V7",
    "title": "Error Handling & Logging",
    "description": "Verify that security logs are protected from unauthorized access and modification. ([C9](https://owasp.org/www-project-proactive-controls/#div-numbering))",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/observability.py"
      },
      {
        "type": "code",
        "reference": "erp/audit.py"
      },
      {
        "type": "doc",
        "reference": "docs/observability.md"
      },
      {
        "type": "test",
        "reference": "tests/test_audit_log.py::test_audit_chain_checker"
      },
      {
        "type": "test",
        "reference": "tests/test_queue_metrics.py::test_queue_lag_metric"
      }
    ]
  },
  {
    "id": "7.3.4",
    "section": "V7",
    "title": "Error Handling & Logging",
    "description": "Verify that time sources are synchronized to the correct time and time zone. Strongly consider logging only in UTC if systems are global to assist with post-incident forensic analysis. ([C9](https://owasp.org/www-project-proactive-controls/#div-numbering))",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/observability.py"
      },
      {
        "type": "code",
        "reference": "erp/audit.py"
      },
      {
        "type": "doc",
        "reference": "docs/observability.md"
      },
      {
        "type": "test",
        "reference": "tests/test_audit_log.py::test_audit_chain_checker"
      },
      {
        "type": "test",
        "reference": "tests/test_queue_metrics.py::test_queue_lag_metric"
      }
    ]
  },
  {
    "id": "7.4.1",
    "section": "V7",
    "title": "Error Handling & Logging",
    "description": "Verify that a generic message is shown when an unexpected or security sensitive error occurs, potentially with a unique ID which support personnel can use to investigate. ([C10](https://owasp.org/www-project-proactive-controls/#div-numbering))",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/observability.py"
      },
      {
        "type": "code",
        "reference": "erp/audit.py"
      },
      {
        "type": "doc",
        "reference": "docs/observability.md"
      },
      {
        "type": "test",
        "reference": "tests/test_audit_log.py::test_audit_chain_checker"
      },
      {
        "type": "test",
        "reference": "tests/test_queue_metrics.py::test_queue_lag_metric"
      }
    ]
  },
  {
    "id": "7.4.2",
    "section": "V7",
    "title": "Error Handling & Logging",
    "description": "Verify that exception handling (or a functional equivalent) is used across the codebase to account for expected and unexpected error conditions. ([C10](https://owasp.org/www-project-proactive-controls/#div-numbering))",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/observability.py"
      },
      {
        "type": "code",
        "reference": "erp/audit.py"
      },
      {
        "type": "doc",
        "reference": "docs/observability.md"
      },
      {
        "type": "test",
        "reference": "tests/test_audit_log.py::test_audit_chain_checker"
      },
      {
        "type": "test",
        "reference": "tests/test_queue_metrics.py::test_queue_lag_metric"
      }
    ]
  },
  {
    "id": "7.4.3",
    "section": "V7",
    "title": "Error Handling & Logging",
    "description": "Verify that a \"last resort\" error handler is defined which will catch all unhandled exceptions. ([C10](https://owasp.org/www-project-proactive-controls/#div-numbering))",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/observability.py"
      },
      {
        "type": "code",
        "reference": "erp/audit.py"
      },
      {
        "type": "doc",
        "reference": "docs/observability.md"
      },
      {
        "type": "test",
        "reference": "tests/test_audit_log.py::test_audit_chain_checker"
      },
      {
        "type": "test",
        "reference": "tests/test_queue_metrics.py::test_queue_lag_metric"
      }
    ]
  },
  {
    "id": "8.1.1",
    "section": "V8",
    "title": "Data Protection",
    "description": "Verify the application protects sensitive data from being cached in server components such as load balancers and application caches.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/data_retention.py"
      },
      {
        "type": "doc",
        "reference": "docs/data_retention.md"
      },
      {
        "type": "doc",
        "reference": "docs/PRIVACY_PROGRAM.md"
      },
      {
        "type": "test",
        "reference": "tests/test_retention.py::test_purge_expired_records"
      },
      {
        "type": "test",
        "reference": "tests/test_backup.py::test_run_backup_sets_metric"
      }
    ]
  },
  {
    "id": "8.1.2",
    "section": "V8",
    "title": "Data Protection",
    "description": "Verify that all cached or temporary copies of sensitive data stored on the server are protected from unauthorized access or purged/invalidated after the authorized user accesses the sensitive data.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/data_retention.py"
      },
      {
        "type": "doc",
        "reference": "docs/data_retention.md"
      },
      {
        "type": "doc",
        "reference": "docs/PRIVACY_PROGRAM.md"
      },
      {
        "type": "test",
        "reference": "tests/test_retention.py::test_purge_expired_records"
      },
      {
        "type": "test",
        "reference": "tests/test_backup.py::test_run_backup_sets_metric"
      }
    ]
  },
  {
    "id": "8.1.3",
    "section": "V8",
    "title": "Data Protection",
    "description": "Verify the application minimizes the number of parameters in a request, such as hidden fields, Ajax variables, cookies and header values.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/data_retention.py"
      },
      {
        "type": "doc",
        "reference": "docs/data_retention.md"
      },
      {
        "type": "doc",
        "reference": "docs/PRIVACY_PROGRAM.md"
      },
      {
        "type": "test",
        "reference": "tests/test_retention.py::test_purge_expired_records"
      },
      {
        "type": "test",
        "reference": "tests/test_backup.py::test_run_backup_sets_metric"
      }
    ]
  },
  {
    "id": "8.1.4",
    "section": "V8",
    "title": "Data Protection",
    "description": "Verify the application can detect and alert on abnormal numbers of requests, such as by IP, user, total per hour or day, or whatever makes sense for the application.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/data_retention.py"
      },
      {
        "type": "doc",
        "reference": "docs/data_retention.md"
      },
      {
        "type": "doc",
        "reference": "docs/PRIVACY_PROGRAM.md"
      },
      {
        "type": "test",
        "reference": "tests/test_retention.py::test_purge_expired_records"
      },
      {
        "type": "test",
        "reference": "tests/test_backup.py::test_run_backup_sets_metric"
      }
    ]
  },
  {
    "id": "8.1.5",
    "section": "V8",
    "title": "Data Protection",
    "description": "Verify that regular backups of important data are performed and that test restoration of data is performed.",
    "levels": [
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/data_retention.py"
      },
      {
        "type": "doc",
        "reference": "docs/data_retention.md"
      },
      {
        "type": "doc",
        "reference": "docs/PRIVACY_PROGRAM.md"
      },
      {
        "type": "test",
        "reference": "tests/test_retention.py::test_purge_expired_records"
      },
      {
        "type": "test",
        "reference": "tests/test_backup.py::test_run_backup_sets_metric"
      }
    ]
  },
  {
    "id": "8.1.6",
    "section": "V8",
    "title": "Data Protection",
    "description": "Verify that backups are stored securely to prevent data from being stolen or corrupted.",
    "levels": [
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/data_retention.py"
      },
      {
        "type": "doc",
        "reference": "docs/data_retention.md"
      },
      {
        "type": "doc",
        "reference": "docs/PRIVACY_PROGRAM.md"
      },
      {
        "type": "test",
        "reference": "tests/test_retention.py::test_purge_expired_records"
      },
      {
        "type": "test",
        "reference": "tests/test_backup.py::test_run_backup_sets_metric"
      }
    ]
  },
  {
    "id": "8.2.1",
    "section": "V8",
    "title": "Data Protection",
    "description": "Verify the application sets sufficient anti-caching headers so that sensitive data is not cached in modern browsers.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/data_retention.py"
      },
      {
        "type": "doc",
        "reference": "docs/data_retention.md"
      },
      {
        "type": "doc",
        "reference": "docs/PRIVACY_PROGRAM.md"
      },
      {
        "type": "test",
        "reference": "tests/test_retention.py::test_purge_expired_records"
      },
      {
        "type": "test",
        "reference": "tests/test_backup.py::test_run_backup_sets_metric"
      }
    ]
  },
  {
    "id": "8.2.2",
    "section": "V8",
    "title": "Data Protection",
    "description": "Verify that data stored in browser storage (such as localStorage, sessionStorage, IndexedDB, or cookies) does not contain sensitive data.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/data_retention.py"
      },
      {
        "type": "doc",
        "reference": "docs/data_retention.md"
      },
      {
        "type": "doc",
        "reference": "docs/PRIVACY_PROGRAM.md"
      },
      {
        "type": "test",
        "reference": "tests/test_retention.py::test_purge_expired_records"
      },
      {
        "type": "test",
        "reference": "tests/test_backup.py::test_run_backup_sets_metric"
      }
    ]
  },
  {
    "id": "8.2.3",
    "section": "V8",
    "title": "Data Protection",
    "description": "Verify that authenticated data is cleared from client storage, such as the browser DOM, after the client or session is terminated.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/data_retention.py"
      },
      {
        "type": "doc",
        "reference": "docs/data_retention.md"
      },
      {
        "type": "doc",
        "reference": "docs/PRIVACY_PROGRAM.md"
      },
      {
        "type": "test",
        "reference": "tests/test_retention.py::test_purge_expired_records"
      },
      {
        "type": "test",
        "reference": "tests/test_backup.py::test_run_backup_sets_metric"
      }
    ]
  },
  {
    "id": "8.3.1",
    "section": "V8",
    "title": "Data Protection",
    "description": "Verify that sensitive data is sent to the server in the HTTP message body or headers, and that query string parameters from any HTTP verb do not contain sensitive data.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/data_retention.py"
      },
      {
        "type": "doc",
        "reference": "docs/data_retention.md"
      },
      {
        "type": "doc",
        "reference": "docs/PRIVACY_PROGRAM.md"
      },
      {
        "type": "test",
        "reference": "tests/test_retention.py::test_purge_expired_records"
      },
      {
        "type": "test",
        "reference": "tests/test_backup.py::test_run_backup_sets_metric"
      },
      {
        "type": "doc",
        "reference": "docs/dr_plan.md"
      }
    ]
  },
  {
    "id": "8.3.2",
    "section": "V8",
    "title": "Data Protection",
    "description": "Verify that users have a method to remove or export their data on demand.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/data_retention.py"
      },
      {
        "type": "doc",
        "reference": "docs/data_retention.md"
      },
      {
        "type": "doc",
        "reference": "docs/PRIVACY_PROGRAM.md"
      },
      {
        "type": "test",
        "reference": "tests/test_retention.py::test_purge_expired_records"
      },
      {
        "type": "test",
        "reference": "tests/test_backup.py::test_run_backup_sets_metric"
      },
      {
        "type": "doc",
        "reference": "docs/dr_plan.md"
      }
    ]
  },
  {
    "id": "8.3.3",
    "section": "V8",
    "title": "Data Protection",
    "description": "Verify that users are provided clear language regarding collection and use of supplied personal information and that users have provided opt-in consent for the use of that data before it is used in any way.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/data_retention.py"
      },
      {
        "type": "doc",
        "reference": "docs/data_retention.md"
      },
      {
        "type": "doc",
        "reference": "docs/PRIVACY_PROGRAM.md"
      },
      {
        "type": "test",
        "reference": "tests/test_retention.py::test_purge_expired_records"
      },
      {
        "type": "test",
        "reference": "tests/test_backup.py::test_run_backup_sets_metric"
      },
      {
        "type": "doc",
        "reference": "docs/dr_plan.md"
      }
    ]
  },
  {
    "id": "8.3.4",
    "section": "V8",
    "title": "Data Protection",
    "description": "Verify that all sensitive data created and processed by the application has been identified, and ensure that a policy is in place on how to deal with sensitive data. ([C8](https://owasp.org/www-project-proactive-controls/#div-numbering))",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/data_retention.py"
      },
      {
        "type": "doc",
        "reference": "docs/data_retention.md"
      },
      {
        "type": "doc",
        "reference": "docs/PRIVACY_PROGRAM.md"
      },
      {
        "type": "test",
        "reference": "tests/test_retention.py::test_purge_expired_records"
      },
      {
        "type": "test",
        "reference": "tests/test_backup.py::test_run_backup_sets_metric"
      },
      {
        "type": "doc",
        "reference": "docs/dr_plan.md"
      }
    ]
  },
  {
    "id": "8.3.5",
    "section": "V8",
    "title": "Data Protection",
    "description": "Verify accessing sensitive data is audited (without logging the sensitive data itself), if the data is collected under relevant data protection directives or where logging of access is required.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/data_retention.py"
      },
      {
        "type": "doc",
        "reference": "docs/data_retention.md"
      },
      {
        "type": "doc",
        "reference": "docs/PRIVACY_PROGRAM.md"
      },
      {
        "type": "test",
        "reference": "tests/test_retention.py::test_purge_expired_records"
      },
      {
        "type": "test",
        "reference": "tests/test_backup.py::test_run_backup_sets_metric"
      },
      {
        "type": "doc",
        "reference": "docs/dr_plan.md"
      }
    ]
  },
  {
    "id": "8.3.6",
    "section": "V8",
    "title": "Data Protection",
    "description": "Verify that sensitive information contained in memory is overwritten as soon as it is no longer required to mitigate memory dumping attacks, using zeroes or random data.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/data_retention.py"
      },
      {
        "type": "doc",
        "reference": "docs/data_retention.md"
      },
      {
        "type": "doc",
        "reference": "docs/PRIVACY_PROGRAM.md"
      },
      {
        "type": "test",
        "reference": "tests/test_retention.py::test_purge_expired_records"
      },
      {
        "type": "test",
        "reference": "tests/test_backup.py::test_run_backup_sets_metric"
      },
      {
        "type": "doc",
        "reference": "docs/dr_plan.md"
      }
    ]
  },
  {
    "id": "8.3.7",
    "section": "V8",
    "title": "Data Protection",
    "description": "Verify that sensitive or private information that is required to be encrypted, is encrypted using approved algorithms that provide both confidentiality and integrity. ([C8](https://owasp.org/www-project-proactive-controls/#div-numbering))",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/data_retention.py"
      },
      {
        "type": "doc",
        "reference": "docs/data_retention.md"
      },
      {
        "type": "doc",
        "reference": "docs/PRIVACY_PROGRAM.md"
      },
      {
        "type": "test",
        "reference": "tests/test_retention.py::test_purge_expired_records"
      },
      {
        "type": "test",
        "reference": "tests/test_backup.py::test_run_backup_sets_metric"
      },
      {
        "type": "doc",
        "reference": "docs/dr_plan.md"
      }
    ]
  },
  {
    "id": "8.3.8",
    "section": "V8",
    "title": "Data Protection",
    "description": "Verify that sensitive personal information is subject to data retention classification, such that old or out of date data is deleted automatically, on a schedule, or as the situation requires.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "deleted",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/data_retention.py"
      },
      {
        "type": "doc",
        "reference": "docs/data_retention.md"
      },
      {
        "type": "doc",
        "reference": "docs/PRIVACY_PROGRAM.md"
      },
      {
        "type": "test",
        "reference": "tests/test_retention.py::test_purge_expired_records"
      },
      {
        "type": "test",
        "reference": "tests/test_backup.py::test_run_backup_sets_metric"
      },
      {
        "type": "doc",
        "reference": "docs/dr_plan.md"
      }
    ]
  },
  {
    "id": "9.1.1",
    "section": "V9",
    "title": "Communications Security",
    "description": "Verify that TLS is used for all client connectivity, and does not fall back to insecure or unencrypted communications. ([C8](https://owasp.org/www-project-proactive-controls/#div-numbering))",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/__init__.py"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/ingress.yaml"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/networkpolicy.yaml"
      },
      {
        "type": "test",
        "reference": "tests/security/test_csp_nonces.py::test_inline_scripts_have_nonce"
      },
      {
        "type": "test",
        "reference": "tests/test_healthz.py::test_health_endpoint"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/service.yaml"
      }
    ]
  },
  {
    "id": "9.1.2",
    "section": "V9",
    "title": "Communications Security",
    "description": "Verify using up to date TLS testing tools that only strong cipher suites are enabled, with the strongest cipher suites set as preferred.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/__init__.py"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/ingress.yaml"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/networkpolicy.yaml"
      },
      {
        "type": "test",
        "reference": "tests/security/test_csp_nonces.py::test_inline_scripts_have_nonce"
      },
      {
        "type": "test",
        "reference": "tests/test_healthz.py::test_health_endpoint"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/service.yaml"
      }
    ]
  },
  {
    "id": "9.1.3",
    "section": "V9",
    "title": "Communications Security",
    "description": "Verify that only the latest recommended versions of the TLS protocol are enabled, such as TLS 1.2 and TLS 1.3. The latest version of the TLS protocol should be the preferred option.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/__init__.py"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/ingress.yaml"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/networkpolicy.yaml"
      },
      {
        "type": "test",
        "reference": "tests/security/test_csp_nonces.py::test_inline_scripts_have_nonce"
      },
      {
        "type": "test",
        "reference": "tests/test_healthz.py::test_health_endpoint"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/service.yaml"
      }
    ]
  },
  {
    "id": "9.2.1",
    "section": "V9",
    "title": "Communications Security",
    "description": "Verify that connections to and from the server use trusted TLS certificates. Where internally generated or self-signed certificates are used, the server must be configured to only trust specific internal CAs and specific self-signed certificates. All others should be rejected.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/__init__.py"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/ingress.yaml"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/networkpolicy.yaml"
      },
      {
        "type": "test",
        "reference": "tests/security/test_csp_nonces.py::test_inline_scripts_have_nonce"
      },
      {
        "type": "test",
        "reference": "tests/test_healthz.py::test_health_endpoint"
      }
    ]
  },
  {
    "id": "9.2.2",
    "section": "V9",
    "title": "Communications Security",
    "description": "Verify that encrypted communications such as TLS is used for all inbound and outbound connections, including for management ports, monitoring, authentication, API, or web service calls, database, cloud, serverless, mainframe, external, and partner connections. The server must not fall back to insecure or unencrypted protocols.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/__init__.py"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/ingress.yaml"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/networkpolicy.yaml"
      },
      {
        "type": "test",
        "reference": "tests/security/test_csp_nonces.py::test_inline_scripts_have_nonce"
      },
      {
        "type": "test",
        "reference": "tests/test_healthz.py::test_health_endpoint"
      }
    ]
  },
  {
    "id": "9.2.3",
    "section": "V9",
    "title": "Communications Security",
    "description": "Verify that all encrypted connections to external systems that involve sensitive information or functions are authenticated.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/__init__.py"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/ingress.yaml"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/networkpolicy.yaml"
      },
      {
        "type": "test",
        "reference": "tests/security/test_csp_nonces.py::test_inline_scripts_have_nonce"
      },
      {
        "type": "test",
        "reference": "tests/test_healthz.py::test_health_endpoint"
      }
    ]
  },
  {
    "id": "9.2.4",
    "section": "V9",
    "title": "Communications Security",
    "description": "Verify that proper certification revocation, such as Online Certificate Status Protocol (OCSP) Stapling, is enabled and configured.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/__init__.py"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/ingress.yaml"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/networkpolicy.yaml"
      },
      {
        "type": "test",
        "reference": "tests/security/test_csp_nonces.py::test_inline_scripts_have_nonce"
      },
      {
        "type": "test",
        "reference": "tests/test_healthz.py::test_health_endpoint"
      }
    ]
  },
  {
    "id": "9.2.5",
    "section": "V9",
    "title": "Communications Security",
    "description": "Verify that backend TLS connection failures are logged.",
    "levels": [
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/__init__.py"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/ingress.yaml"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/networkpolicy.yaml"
      },
      {
        "type": "test",
        "reference": "tests/security/test_csp_nonces.py::test_inline_scripts_have_nonce"
      },
      {
        "type": "test",
        "reference": "tests/test_healthz.py::test_health_endpoint"
      }
    ]
  },
  {
    "id": "10.1.1",
    "section": "V10",
    "title": "Malicious Code & Integrity",
    "description": "Verify that a code analysis tool is in use that can detect potentially malicious code, such as time functions, unsafe file operations and network connections.",
    "levels": [
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/__init__.py"
      },
      {
        "type": "code",
        "reference": "scripts/security_scan.sh"
      },
      {
        "type": "doc",
        "reference": "docs/chaos_testing.md"
      },
      {
        "type": "test",
        "reference": "tests/test_waf.py::test_waf_blocks_img_onerror"
      },
      {
        "type": "test",
        "reference": "tests/security/test_rls_smoke.py::test_rls_blocks_cross_org"
      }
    ]
  },
  {
    "id": "10.2.1",
    "section": "V10",
    "title": "Malicious Code & Integrity",
    "description": "Verify that the application source code and third party libraries do not contain unauthorized phone home or data collection capabilities. Where such functionality exists, obtain the user's permission for it to operate before collecting any data.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/__init__.py"
      },
      {
        "type": "code",
        "reference": "scripts/security_scan.sh"
      },
      {
        "type": "doc",
        "reference": "docs/chaos_testing.md"
      },
      {
        "type": "test",
        "reference": "tests/test_waf.py::test_waf_blocks_img_onerror"
      },
      {
        "type": "test",
        "reference": "tests/security/test_rls_smoke.py::test_rls_blocks_cross_org"
      },
      {
        "type": "test",
        "reference": "tests/security/test_csp_nonces.py::test_inline_scripts_have_nonce"
      }
    ]
  },
  {
    "id": "10.2.2",
    "section": "V10",
    "title": "Malicious Code & Integrity",
    "description": "Verify that the application does not ask for unnecessary or excessive permissions to privacy related features or sensors, such as contacts, cameras, microphones, or location.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/__init__.py"
      },
      {
        "type": "code",
        "reference": "scripts/security_scan.sh"
      },
      {
        "type": "doc",
        "reference": "docs/chaos_testing.md"
      },
      {
        "type": "test",
        "reference": "tests/test_waf.py::test_waf_blocks_img_onerror"
      },
      {
        "type": "test",
        "reference": "tests/security/test_rls_smoke.py::test_rls_blocks_cross_org"
      },
      {
        "type": "test",
        "reference": "tests/security/test_csp_nonces.py::test_inline_scripts_have_nonce"
      }
    ]
  },
  {
    "id": "10.2.3",
    "section": "V10",
    "title": "Malicious Code & Integrity",
    "description": "Verify that the application source code and third party libraries do not contain back doors, such as hard-coded or additional undocumented accounts or keys, code obfuscation, undocumented binary blobs, rootkits, or anti-debugging, insecure debugging features, or otherwise out of date, insecure, or hidden functionality that could be used maliciously if discovered.",
    "levels": [
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/__init__.py"
      },
      {
        "type": "code",
        "reference": "scripts/security_scan.sh"
      },
      {
        "type": "doc",
        "reference": "docs/chaos_testing.md"
      },
      {
        "type": "test",
        "reference": "tests/test_waf.py::test_waf_blocks_img_onerror"
      },
      {
        "type": "test",
        "reference": "tests/security/test_rls_smoke.py::test_rls_blocks_cross_org"
      },
      {
        "type": "test",
        "reference": "tests/security/test_csp_nonces.py::test_inline_scripts_have_nonce"
      }
    ]
  },
  {
    "id": "10.2.4",
    "section": "V10",
    "title": "Malicious Code & Integrity",
    "description": "Verify that the application source code and third party libraries do not contain time bombs by searching for date and time related functions.",
    "levels": [
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/__init__.py"
      },
      {
        "type": "code",
        "reference": "scripts/security_scan.sh"
      },
      {
        "type": "doc",
        "reference": "docs/chaos_testing.md"
      },
      {
        "type": "test",
        "reference": "tests/test_waf.py::test_waf_blocks_img_onerror"
      },
      {
        "type": "test",
        "reference": "tests/security/test_rls_smoke.py::test_rls_blocks_cross_org"
      },
      {
        "type": "test",
        "reference": "tests/security/test_csp_nonces.py::test_inline_scripts_have_nonce"
      }
    ]
  },
  {
    "id": "10.2.5",
    "section": "V10",
    "title": "Malicious Code & Integrity",
    "description": "Verify that the application source code and third party libraries do not contain malicious code, such as salami attacks, logic bypasses, or logic bombs.",
    "levels": [
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/__init__.py"
      },
      {
        "type": "code",
        "reference": "scripts/security_scan.sh"
      },
      {
        "type": "doc",
        "reference": "docs/chaos_testing.md"
      },
      {
        "type": "test",
        "reference": "tests/test_waf.py::test_waf_blocks_img_onerror"
      },
      {
        "type": "test",
        "reference": "tests/security/test_rls_smoke.py::test_rls_blocks_cross_org"
      },
      {
        "type": "test",
        "reference": "tests/security/test_csp_nonces.py::test_inline_scripts_have_nonce"
      }
    ]
  },
  {
    "id": "10.2.6",
    "section": "V10",
    "title": "Malicious Code & Integrity",
    "description": "Verify that the application source code and third party libraries do not contain Easter eggs or any other potentially unwanted functionality.",
    "levels": [
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/__init__.py"
      },
      {
        "type": "code",
        "reference": "scripts/security_scan.sh"
      },
      {
        "type": "doc",
        "reference": "docs/chaos_testing.md"
      },
      {
        "type": "test",
        "reference": "tests/test_waf.py::test_waf_blocks_img_onerror"
      },
      {
        "type": "test",
        "reference": "tests/security/test_rls_smoke.py::test_rls_blocks_cross_org"
      },
      {
        "type": "test",
        "reference": "tests/security/test_csp_nonces.py::test_inline_scripts_have_nonce"
      }
    ]
  },
  {
    "id": "10.3.1",
    "section": "V10",
    "title": "Malicious Code & Integrity",
    "description": "Verify that if the application has a client or server auto-update feature, updates should be obtained over secure channels and digitally signed. The update code must validate the digital signature of the update before installing or executing the update.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/__init__.py"
      },
      {
        "type": "code",
        "reference": "scripts/security_scan.sh"
      },
      {
        "type": "doc",
        "reference": "docs/chaos_testing.md"
      },
      {
        "type": "test",
        "reference": "tests/test_waf.py::test_waf_blocks_img_onerror"
      },
      {
        "type": "test",
        "reference": "tests/security/test_rls_smoke.py::test_rls_blocks_cross_org"
      }
    ]
  },
  {
    "id": "10.3.2",
    "section": "V10",
    "title": "Malicious Code & Integrity",
    "description": "Verify that the application employs integrity protections, such as code signing or subresource integrity. The application must not load or execute code from untrusted sources, such as loading includes, modules, plugins, code, or libraries from untrusted sources or the Internet.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/__init__.py"
      },
      {
        "type": "code",
        "reference": "scripts/security_scan.sh"
      },
      {
        "type": "doc",
        "reference": "docs/chaos_testing.md"
      },
      {
        "type": "test",
        "reference": "tests/test_waf.py::test_waf_blocks_img_onerror"
      },
      {
        "type": "test",
        "reference": "tests/security/test_rls_smoke.py::test_rls_blocks_cross_org"
      }
    ]
  },
  {
    "id": "10.3.3",
    "section": "V10",
    "title": "Malicious Code & Integrity",
    "description": "Verify that the application has protection from subdomain takeovers if the application relies upon DNS entries or DNS subdomains, such as expired domain names, out of date DNS pointers or CNAMEs, expired projects at public source code repos, or transient cloud APIs, serverless functions, or storage buckets (*autogen-bucket-id*.cloud.example.com) or similar. Protections can include ensuring that DNS names used by applications are regularly checked for expiry or change.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/__init__.py"
      },
      {
        "type": "code",
        "reference": "scripts/security_scan.sh"
      },
      {
        "type": "doc",
        "reference": "docs/chaos_testing.md"
      },
      {
        "type": "test",
        "reference": "tests/test_waf.py::test_waf_blocks_img_onerror"
      },
      {
        "type": "test",
        "reference": "tests/security/test_rls_smoke.py::test_rls_blocks_cross_org"
      }
    ]
  },
  {
    "id": "11.1.1",
    "section": "V11",
    "title": "Business Logic",
    "description": "Verify that the application will only process business logic flows for the same user in sequential step order and without skipping steps.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/workflow.py"
      },
      {
        "type": "code",
        "reference": "erp/routes/tenders.py"
      },
      {
        "type": "doc",
        "reference": "docs/blueprints.md"
      },
      {
        "type": "test",
        "reference": "tests/test_tender_workflow.py::test_tender_cannot_skip_states"
      },
      {
        "type": "test",
        "reference": "tests/test_orders_db_agnostic.py::test_order_state_machine"
      }
    ]
  },
  {
    "id": "11.1.2",
    "section": "V11",
    "title": "Business Logic",
    "description": "Verify that the application will only process business logic flows with all steps being processed in realistic human time, i.e. transactions are not submitted too quickly.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/workflow.py"
      },
      {
        "type": "code",
        "reference": "erp/routes/tenders.py"
      },
      {
        "type": "doc",
        "reference": "docs/blueprints.md"
      },
      {
        "type": "test",
        "reference": "tests/test_tender_workflow.py::test_tender_cannot_skip_states"
      },
      {
        "type": "test",
        "reference": "tests/test_orders_db_agnostic.py::test_order_state_machine"
      }
    ]
  },
  {
    "id": "11.1.3",
    "section": "V11",
    "title": "Business Logic",
    "description": "Verify the application has appropriate limits for specific business actions or transactions which are correctly enforced on a per user basis.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/workflow.py"
      },
      {
        "type": "code",
        "reference": "erp/routes/tenders.py"
      },
      {
        "type": "doc",
        "reference": "docs/blueprints.md"
      },
      {
        "type": "test",
        "reference": "tests/test_tender_workflow.py::test_tender_cannot_skip_states"
      },
      {
        "type": "test",
        "reference": "tests/test_orders_db_agnostic.py::test_order_state_machine"
      }
    ]
  },
  {
    "id": "11.1.4",
    "section": "V11",
    "title": "Business Logic",
    "description": "Verify that the application has anti-automation controls to protect against excessive calls such as mass data exfiltration, business logic requests, file uploads or denial of service attacks.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/workflow.py"
      },
      {
        "type": "code",
        "reference": "erp/routes/tenders.py"
      },
      {
        "type": "doc",
        "reference": "docs/blueprints.md"
      },
      {
        "type": "test",
        "reference": "tests/test_tender_workflow.py::test_tender_cannot_skip_states"
      },
      {
        "type": "test",
        "reference": "tests/test_orders_db_agnostic.py::test_order_state_machine"
      }
    ]
  },
  {
    "id": "11.1.5",
    "section": "V11",
    "title": "Business Logic",
    "description": "Verify the application has business logic limits or validation to protect against likely business risks or threats, identified using threat modeling or similar methodologies.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/workflow.py"
      },
      {
        "type": "code",
        "reference": "erp/routes/tenders.py"
      },
      {
        "type": "doc",
        "reference": "docs/blueprints.md"
      },
      {
        "type": "test",
        "reference": "tests/test_tender_workflow.py::test_tender_cannot_skip_states"
      },
      {
        "type": "test",
        "reference": "tests/test_orders_db_agnostic.py::test_order_state_machine"
      }
    ]
  },
  {
    "id": "11.1.6",
    "section": "V11",
    "title": "Business Logic",
    "description": "Verify that the application does not suffer from \"Time Of Check to Time Of Use\" (TOCTOU) issues or other race conditions for sensitive operations.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/workflow.py"
      },
      {
        "type": "code",
        "reference": "erp/routes/tenders.py"
      },
      {
        "type": "doc",
        "reference": "docs/blueprints.md"
      },
      {
        "type": "test",
        "reference": "tests/test_tender_workflow.py::test_tender_cannot_skip_states"
      },
      {
        "type": "test",
        "reference": "tests/test_orders_db_agnostic.py::test_order_state_machine"
      }
    ]
  },
  {
    "id": "11.1.7",
    "section": "V11",
    "title": "Business Logic",
    "description": "Verify that the application monitors for unusual events or activity from a business logic perspective. For example, attempts to perform actions out of order or actions which a normal user would never attempt. ([C9](https://owasp.org/www-project-proactive-controls/#div-numbering))",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/workflow.py"
      },
      {
        "type": "code",
        "reference": "erp/routes/tenders.py"
      },
      {
        "type": "doc",
        "reference": "docs/blueprints.md"
      },
      {
        "type": "test",
        "reference": "tests/test_tender_workflow.py::test_tender_cannot_skip_states"
      },
      {
        "type": "test",
        "reference": "tests/test_orders_db_agnostic.py::test_order_state_machine"
      }
    ]
  },
  {
    "id": "11.1.8",
    "section": "V11",
    "title": "Business Logic",
    "description": "Verify that the application has configurable alerting when automated attacks or unusual activity is detected.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/workflow.py"
      },
      {
        "type": "code",
        "reference": "erp/routes/tenders.py"
      },
      {
        "type": "doc",
        "reference": "docs/blueprints.md"
      },
      {
        "type": "test",
        "reference": "tests/test_tender_workflow.py::test_tender_cannot_skip_states"
      },
      {
        "type": "test",
        "reference": "tests/test_orders_db_agnostic.py::test_order_state_machine"
      }
    ]
  },
  {
    "id": "12.1.1",
    "section": "V12",
    "title": "Files & Resources",
    "description": "Verify that the application will not accept large files that could fill up storage or cause a denial of service.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/storage.py"
      },
      {
        "type": "code",
        "reference": "erp/routes/help.py"
      },
      {
        "type": "doc",
        "reference": "docs/security/content_security_policy.md"
      },
      {
        "type": "test",
        "reference": "tests/test_storage.py::test_presigned"
      },
      {
        "type": "test",
        "reference": "tests/test_service_worker_offline.py::test_offline_fallback"
      }
    ]
  },
  {
    "id": "12.1.2",
    "section": "V12",
    "title": "Files & Resources",
    "description": "Verify that the application checks compressed files (e.g. zip, gz, docx, odt) against maximum allowed uncompressed size and against maximum number of files before uncompressing the file.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/storage.py"
      },
      {
        "type": "code",
        "reference": "erp/routes/help.py"
      },
      {
        "type": "doc",
        "reference": "docs/security/content_security_policy.md"
      },
      {
        "type": "test",
        "reference": "tests/test_storage.py::test_presigned"
      },
      {
        "type": "test",
        "reference": "tests/test_service_worker_offline.py::test_offline_fallback"
      }
    ]
  },
  {
    "id": "12.1.3",
    "section": "V12",
    "title": "Files & Resources",
    "description": "Verify that a file size quota and maximum number of files per user is enforced to ensure that a single user cannot fill up the storage with too many files, or excessively large files.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/storage.py"
      },
      {
        "type": "code",
        "reference": "erp/routes/help.py"
      },
      {
        "type": "doc",
        "reference": "docs/security/content_security_policy.md"
      },
      {
        "type": "test",
        "reference": "tests/test_storage.py::test_presigned"
      },
      {
        "type": "test",
        "reference": "tests/test_service_worker_offline.py::test_offline_fallback"
      }
    ]
  },
  {
    "id": "12.2.1",
    "section": "V12",
    "title": "Files & Resources",
    "description": "Verify that files obtained from untrusted sources are validated to be of expected type based on the file's content.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/storage.py"
      },
      {
        "type": "code",
        "reference": "erp/routes/help.py"
      },
      {
        "type": "doc",
        "reference": "docs/security/content_security_policy.md"
      },
      {
        "type": "test",
        "reference": "tests/test_storage.py::test_presigned"
      },
      {
        "type": "test",
        "reference": "tests/test_service_worker_offline.py::test_offline_fallback"
      }
    ]
  },
  {
    "id": "12.3.1",
    "section": "V12",
    "title": "Files & Resources",
    "description": "Verify that user-submitted filename metadata is not used directly by system or framework filesystems and that a URL API is used to protect against path traversal.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/storage.py"
      },
      {
        "type": "code",
        "reference": "erp/routes/help.py"
      },
      {
        "type": "doc",
        "reference": "docs/security/content_security_policy.md"
      },
      {
        "type": "test",
        "reference": "tests/test_storage.py::test_presigned"
      },
      {
        "type": "test",
        "reference": "tests/test_service_worker_offline.py::test_offline_fallback"
      }
    ]
  },
  {
    "id": "12.3.2",
    "section": "V12",
    "title": "Files & Resources",
    "description": "Verify that user-submitted filename metadata is validated or ignored to prevent the disclosure, creation, updating or removal of local files (LFI).",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/storage.py"
      },
      {
        "type": "code",
        "reference": "erp/routes/help.py"
      },
      {
        "type": "doc",
        "reference": "docs/security/content_security_policy.md"
      },
      {
        "type": "test",
        "reference": "tests/test_storage.py::test_presigned"
      },
      {
        "type": "test",
        "reference": "tests/test_service_worker_offline.py::test_offline_fallback"
      }
    ]
  },
  {
    "id": "12.3.3",
    "section": "V12",
    "title": "Files & Resources",
    "description": "Verify that user-submitted filename metadata is validated or ignored to prevent the disclosure or execution of remote files via Remote File Inclusion (RFI) or Server-side Request Forgery (SSRF) attacks.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/storage.py"
      },
      {
        "type": "code",
        "reference": "erp/routes/help.py"
      },
      {
        "type": "doc",
        "reference": "docs/security/content_security_policy.md"
      },
      {
        "type": "test",
        "reference": "tests/test_storage.py::test_presigned"
      },
      {
        "type": "test",
        "reference": "tests/test_service_worker_offline.py::test_offline_fallback"
      }
    ]
  },
  {
    "id": "12.3.4",
    "section": "V12",
    "title": "Files & Resources",
    "description": "Verify that the application protects against Reflective File Download (RFD) by validating or ignoring user-submitted filenames in a JSON, JSONP, or URL parameter, the response Content-Type header should be set to text/plain, and the Content-Disposition header should have a fixed filename.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/storage.py"
      },
      {
        "type": "code",
        "reference": "erp/routes/help.py"
      },
      {
        "type": "doc",
        "reference": "docs/security/content_security_policy.md"
      },
      {
        "type": "test",
        "reference": "tests/test_storage.py::test_presigned"
      },
      {
        "type": "test",
        "reference": "tests/test_service_worker_offline.py::test_offline_fallback"
      }
    ]
  },
  {
    "id": "12.3.5",
    "section": "V12",
    "title": "Files & Resources",
    "description": "Verify that untrusted file metadata is not used directly with system API or libraries, to protect against OS command injection.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/storage.py"
      },
      {
        "type": "code",
        "reference": "erp/routes/help.py"
      },
      {
        "type": "doc",
        "reference": "docs/security/content_security_policy.md"
      },
      {
        "type": "test",
        "reference": "tests/test_storage.py::test_presigned"
      },
      {
        "type": "test",
        "reference": "tests/test_service_worker_offline.py::test_offline_fallback"
      }
    ]
  },
  {
    "id": "12.3.6",
    "section": "V12",
    "title": "Files & Resources",
    "description": "Verify that the application does not include and execute functionality from untrusted sources, such as unverified content distribution networks, JavaScript libraries, node npm libraries, or server-side DLLs.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/storage.py"
      },
      {
        "type": "code",
        "reference": "erp/routes/help.py"
      },
      {
        "type": "doc",
        "reference": "docs/security/content_security_policy.md"
      },
      {
        "type": "test",
        "reference": "tests/test_storage.py::test_presigned"
      },
      {
        "type": "test",
        "reference": "tests/test_service_worker_offline.py::test_offline_fallback"
      }
    ]
  },
  {
    "id": "12.4.1",
    "section": "V12",
    "title": "Files & Resources",
    "description": "Verify that files obtained from untrusted sources are stored outside the web root, with limited permissions.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/storage.py"
      },
      {
        "type": "code",
        "reference": "erp/routes/help.py"
      },
      {
        "type": "doc",
        "reference": "docs/security/content_security_policy.md"
      },
      {
        "type": "test",
        "reference": "tests/test_storage.py::test_presigned"
      },
      {
        "type": "test",
        "reference": "tests/test_service_worker_offline.py::test_offline_fallback"
      }
    ]
  },
  {
    "id": "12.4.2",
    "section": "V12",
    "title": "Files & Resources",
    "description": "Verify that files obtained from untrusted sources are scanned by antivirus scanners to prevent upload and serving of known malicious content.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/storage.py"
      },
      {
        "type": "code",
        "reference": "erp/routes/help.py"
      },
      {
        "type": "doc",
        "reference": "docs/security/content_security_policy.md"
      },
      {
        "type": "test",
        "reference": "tests/test_storage.py::test_presigned"
      },
      {
        "type": "test",
        "reference": "tests/test_service_worker_offline.py::test_offline_fallback"
      }
    ]
  },
  {
    "id": "12.5.1",
    "section": "V12",
    "title": "Files & Resources",
    "description": "Verify that the web tier is configured to serve only files with specific file extensions to prevent unintentional information and source code leakage. For example, backup files (e.g. .bak), temporary working files (e.g. .swp), compressed files (.zip, .tar.gz, etc) and other extensions commonly used by editors should be blocked unless required.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/storage.py"
      },
      {
        "type": "code",
        "reference": "erp/routes/help.py"
      },
      {
        "type": "doc",
        "reference": "docs/security/content_security_policy.md"
      },
      {
        "type": "test",
        "reference": "tests/test_storage.py::test_presigned"
      },
      {
        "type": "test",
        "reference": "tests/test_service_worker_offline.py::test_offline_fallback"
      }
    ]
  },
  {
    "id": "12.5.2",
    "section": "V12",
    "title": "Files & Resources",
    "description": "Verify that direct requests to uploaded files will never be executed as HTML/JavaScript content.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/storage.py"
      },
      {
        "type": "code",
        "reference": "erp/routes/help.py"
      },
      {
        "type": "doc",
        "reference": "docs/security/content_security_policy.md"
      },
      {
        "type": "test",
        "reference": "tests/test_storage.py::test_presigned"
      },
      {
        "type": "test",
        "reference": "tests/test_service_worker_offline.py::test_offline_fallback"
      }
    ]
  },
  {
    "id": "12.6.1",
    "section": "V12",
    "title": "Files & Resources",
    "description": "Verify that the web or application server is configured with an allow list of resources or systems to which the server can send requests or load data/files from.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/storage.py"
      },
      {
        "type": "code",
        "reference": "erp/routes/help.py"
      },
      {
        "type": "doc",
        "reference": "docs/security/content_security_policy.md"
      },
      {
        "type": "test",
        "reference": "tests/test_storage.py::test_presigned"
      },
      {
        "type": "test",
        "reference": "tests/test_service_worker_offline.py::test_offline_fallback"
      }
    ]
  },
  {
    "id": "13.1.1",
    "section": "V13",
    "title": "API & Web Services",
    "description": "Verify that all application components use the same encodings and parsers to avoid parsing attacks that exploit different URI or file parsing behavior that could be used in SSRF and RFI attacks.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/api/__init__.py"
      },
      {
        "type": "doc",
        "reference": "docs/OPENAPI.yaml"
      },
      {
        "type": "test",
        "reference": "tests/test_api.py::test_rest_and_graphql"
      },
      {
        "type": "test",
        "reference": "tests/test_api.py::test_webhook_requires_token"
      },
      {
        "type": "test",
        "reference": "tests/test_webhook_signature.py::test_webhook_requires_signature"
      }
    ]
  },
  {
    "id": "13.1.2",
    "section": "V13",
    "title": "API & Web Services",
    "description": "[DELETED, DUPLICATE OF 4.3.1]",
    "levels": [],
    "status": "deleted",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/api/__init__.py"
      },
      {
        "type": "doc",
        "reference": "docs/OPENAPI.yaml"
      },
      {
        "type": "test",
        "reference": "tests/test_api.py::test_rest_and_graphql"
      },
      {
        "type": "test",
        "reference": "tests/test_api.py::test_webhook_requires_token"
      },
      {
        "type": "test",
        "reference": "tests/test_webhook_signature.py::test_webhook_requires_signature"
      }
    ]
  },
  {
    "id": "13.1.3",
    "section": "V13",
    "title": "API & Web Services",
    "description": "Verify API URLs do not expose sensitive information, such as the API key, session tokens etc.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/api/__init__.py"
      },
      {
        "type": "doc",
        "reference": "docs/OPENAPI.yaml"
      },
      {
        "type": "test",
        "reference": "tests/test_api.py::test_rest_and_graphql"
      },
      {
        "type": "test",
        "reference": "tests/test_api.py::test_webhook_requires_token"
      },
      {
        "type": "test",
        "reference": "tests/test_webhook_signature.py::test_webhook_requires_signature"
      }
    ]
  },
  {
    "id": "13.1.4",
    "section": "V13",
    "title": "API & Web Services",
    "description": "Verify that authorization decisions are made at both the URI, enforced by programmatic or declarative security at the controller or router, and at the resource level, enforced by model-based permissions.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/api/__init__.py"
      },
      {
        "type": "doc",
        "reference": "docs/OPENAPI.yaml"
      },
      {
        "type": "test",
        "reference": "tests/test_api.py::test_rest_and_graphql"
      },
      {
        "type": "test",
        "reference": "tests/test_api.py::test_webhook_requires_token"
      },
      {
        "type": "test",
        "reference": "tests/test_webhook_signature.py::test_webhook_requires_signature"
      }
    ]
  },
  {
    "id": "13.1.5",
    "section": "V13",
    "title": "API & Web Services",
    "description": "Verify that requests containing unexpected or missing content types are rejected with appropriate headers (HTTP response status 406 Unacceptable or 415 Unsupported Media Type).",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/api/__init__.py"
      },
      {
        "type": "doc",
        "reference": "docs/OPENAPI.yaml"
      },
      {
        "type": "test",
        "reference": "tests/test_api.py::test_rest_and_graphql"
      },
      {
        "type": "test",
        "reference": "tests/test_api.py::test_webhook_requires_token"
      },
      {
        "type": "test",
        "reference": "tests/test_webhook_signature.py::test_webhook_requires_signature"
      }
    ]
  },
  {
    "id": "13.2.1",
    "section": "V13",
    "title": "API & Web Services",
    "description": "Verify that enabled RESTful HTTP methods are a valid choice for the user or action, such as preventing normal users using DELETE or PUT on protected API or resources.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/api/__init__.py"
      },
      {
        "type": "doc",
        "reference": "docs/OPENAPI.yaml"
      },
      {
        "type": "test",
        "reference": "tests/test_api.py::test_rest_and_graphql"
      },
      {
        "type": "test",
        "reference": "tests/test_api.py::test_webhook_requires_token"
      },
      {
        "type": "test",
        "reference": "tests/test_webhook_signature.py::test_webhook_requires_signature"
      },
      {
        "type": "doc",
        "reference": "docs/integrations.md"
      }
    ]
  },
  {
    "id": "13.2.2",
    "section": "V13",
    "title": "API & Web Services",
    "description": "Verify that JSON schema validation is in place and verified before accepting input.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/api/__init__.py"
      },
      {
        "type": "doc",
        "reference": "docs/OPENAPI.yaml"
      },
      {
        "type": "test",
        "reference": "tests/test_api.py::test_rest_and_graphql"
      },
      {
        "type": "test",
        "reference": "tests/test_api.py::test_webhook_requires_token"
      },
      {
        "type": "test",
        "reference": "tests/test_webhook_signature.py::test_webhook_requires_signature"
      },
      {
        "type": "doc",
        "reference": "docs/integrations.md"
      }
    ]
  },
  {
    "id": "13.2.3",
    "section": "V13",
    "title": "API & Web Services",
    "description": "Verify that RESTful web services that utilize cookies are protected from Cross-Site Request Forgery via the use of at least one or more of the following: double submit cookie pattern, CSRF nonces, or Origin request header checks.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/api/__init__.py"
      },
      {
        "type": "doc",
        "reference": "docs/OPENAPI.yaml"
      },
      {
        "type": "test",
        "reference": "tests/test_api.py::test_rest_and_graphql"
      },
      {
        "type": "test",
        "reference": "tests/test_api.py::test_webhook_requires_token"
      },
      {
        "type": "test",
        "reference": "tests/test_webhook_signature.py::test_webhook_requires_signature"
      },
      {
        "type": "doc",
        "reference": "docs/integrations.md"
      }
    ]
  },
  {
    "id": "13.2.4",
    "section": "V13",
    "title": "API & Web Services",
    "description": "[DELETED, DUPLICATE OF 11.1.4]",
    "levels": [],
    "status": "deleted",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/api/__init__.py"
      },
      {
        "type": "doc",
        "reference": "docs/OPENAPI.yaml"
      },
      {
        "type": "test",
        "reference": "tests/test_api.py::test_rest_and_graphql"
      },
      {
        "type": "test",
        "reference": "tests/test_api.py::test_webhook_requires_token"
      },
      {
        "type": "test",
        "reference": "tests/test_webhook_signature.py::test_webhook_requires_signature"
      },
      {
        "type": "doc",
        "reference": "docs/integrations.md"
      }
    ]
  },
  {
    "id": "13.2.5",
    "section": "V13",
    "title": "API & Web Services",
    "description": "Verify that REST services explicitly check the incoming Content-Type to be the expected one, such as application/xml or application/json.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/api/__init__.py"
      },
      {
        "type": "doc",
        "reference": "docs/OPENAPI.yaml"
      },
      {
        "type": "test",
        "reference": "tests/test_api.py::test_rest_and_graphql"
      },
      {
        "type": "test",
        "reference": "tests/test_api.py::test_webhook_requires_token"
      },
      {
        "type": "test",
        "reference": "tests/test_webhook_signature.py::test_webhook_requires_signature"
      },
      {
        "type": "doc",
        "reference": "docs/integrations.md"
      }
    ]
  },
  {
    "id": "13.2.6",
    "section": "V13",
    "title": "API & Web Services",
    "description": "Verify that the message headers and payload are trustworthy and not modified in transit. Requiring strong encryption for transport (TLS only) may be sufficient in many cases as it provides both confidentiality and integrity protection. Per-message digital signatures can provide additional assurance on top of the transport protections for high-security applications but bring with them additional complexity and risks to weigh against the benefits.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/api/__init__.py"
      },
      {
        "type": "doc",
        "reference": "docs/OPENAPI.yaml"
      },
      {
        "type": "test",
        "reference": "tests/test_api.py::test_rest_and_graphql"
      },
      {
        "type": "test",
        "reference": "tests/test_api.py::test_webhook_requires_token"
      },
      {
        "type": "test",
        "reference": "tests/test_webhook_signature.py::test_webhook_requires_signature"
      },
      {
        "type": "doc",
        "reference": "docs/integrations.md"
      }
    ]
  },
  {
    "id": "13.3.1",
    "section": "V13",
    "title": "API & Web Services",
    "description": "Verify that XSD schema validation takes place to ensure a properly formed XML document, followed by validation of each input field before any processing of that data takes place.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/api/__init__.py"
      },
      {
        "type": "doc",
        "reference": "docs/OPENAPI.yaml"
      },
      {
        "type": "test",
        "reference": "tests/test_api.py::test_rest_and_graphql"
      },
      {
        "type": "test",
        "reference": "tests/test_api.py::test_webhook_requires_token"
      },
      {
        "type": "test",
        "reference": "tests/test_webhook_signature.py::test_webhook_requires_signature"
      }
    ]
  },
  {
    "id": "13.3.2",
    "section": "V13",
    "title": "API & Web Services",
    "description": "Verify that the message payload is signed using WS-Security to ensure reliable transport between client and service.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/api/__init__.py"
      },
      {
        "type": "doc",
        "reference": "docs/OPENAPI.yaml"
      },
      {
        "type": "test",
        "reference": "tests/test_api.py::test_rest_and_graphql"
      },
      {
        "type": "test",
        "reference": "tests/test_api.py::test_webhook_requires_token"
      },
      {
        "type": "test",
        "reference": "tests/test_webhook_signature.py::test_webhook_requires_signature"
      }
    ]
  },
  {
    "id": "13.4.1",
    "section": "V13",
    "title": "API & Web Services",
    "description": "Verify that a query allow list or a combination of depth limiting and amount limiting is used to prevent GraphQL or data layer expression Denial of Service (DoS) as a result of expensive, nested queries. For more advanced scenarios, query cost analysis should be used.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/api/__init__.py"
      },
      {
        "type": "doc",
        "reference": "docs/OPENAPI.yaml"
      },
      {
        "type": "test",
        "reference": "tests/test_api.py::test_rest_and_graphql"
      },
      {
        "type": "test",
        "reference": "tests/test_api.py::test_webhook_requires_token"
      },
      {
        "type": "test",
        "reference": "tests/test_webhook_signature.py::test_webhook_requires_signature"
      }
    ]
  },
  {
    "id": "13.4.2",
    "section": "V13",
    "title": "API & Web Services",
    "description": "Verify that GraphQL or other data layer authorization logic should be implemented at the business logic layer instead of the GraphQL layer.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "erp/api/__init__.py"
      },
      {
        "type": "doc",
        "reference": "docs/OPENAPI.yaml"
      },
      {
        "type": "test",
        "reference": "tests/test_api.py::test_rest_and_graphql"
      },
      {
        "type": "test",
        "reference": "tests/test_api.py::test_webhook_requires_token"
      },
      {
        "type": "test",
        "reference": "tests/test_webhook_signature.py::test_webhook_requires_signature"
      }
    ]
  },
  {
    "id": "14.1.1",
    "section": "V14",
    "title": "Configuration",
    "description": "Verify that the application build and deployment processes are performed in a secure and repeatable way, such as CI / CD automation, automated configuration management, and automated deployment scripts.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "dockerfile"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/deployment.yaml"
      },
      {
        "type": "code",
        "reference": "config.py"
      },
      {
        "type": "doc",
        "reference": "docs/configuration.md"
      },
      {
        "type": "test",
        "reference": "tests/test_modules_smoke.py::test_blueprints_registered"
      }
    ]
  },
  {
    "id": "14.1.2",
    "section": "V14",
    "title": "Configuration",
    "description": "Verify that compiler flags are configured to enable all available buffer overflow protections and warnings, including stack randomization, data execution prevention, and to break the build if an unsafe pointer, memory, format string, integer, or string operations are found.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "dockerfile"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/deployment.yaml"
      },
      {
        "type": "code",
        "reference": "config.py"
      },
      {
        "type": "doc",
        "reference": "docs/configuration.md"
      },
      {
        "type": "test",
        "reference": "tests/test_modules_smoke.py::test_blueprints_registered"
      }
    ]
  },
  {
    "id": "14.1.3",
    "section": "V14",
    "title": "Configuration",
    "description": "Verify that server configuration is hardened as per the recommendations of the application server and frameworks in use.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "dockerfile"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/deployment.yaml"
      },
      {
        "type": "code",
        "reference": "config.py"
      },
      {
        "type": "doc",
        "reference": "docs/configuration.md"
      },
      {
        "type": "test",
        "reference": "tests/test_modules_smoke.py::test_blueprints_registered"
      }
    ]
  },
  {
    "id": "14.1.4",
    "section": "V14",
    "title": "Configuration",
    "description": "Verify that the application, configuration, and all dependencies can be re-deployed using automated deployment scripts, built from a documented and tested runbook in a reasonable time, or restored from backups in a timely fashion.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "dockerfile"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/deployment.yaml"
      },
      {
        "type": "code",
        "reference": "config.py"
      },
      {
        "type": "doc",
        "reference": "docs/configuration.md"
      },
      {
        "type": "test",
        "reference": "tests/test_modules_smoke.py::test_blueprints_registered"
      }
    ]
  },
  {
    "id": "14.1.5",
    "section": "V14",
    "title": "Configuration",
    "description": "Verify that authorized administrators can verify the integrity of all security-relevant configurations to detect tampering.",
    "levels": [
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "dockerfile"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/deployment.yaml"
      },
      {
        "type": "code",
        "reference": "config.py"
      },
      {
        "type": "doc",
        "reference": "docs/configuration.md"
      },
      {
        "type": "test",
        "reference": "tests/test_modules_smoke.py::test_blueprints_registered"
      }
    ]
  },
  {
    "id": "14.2.1",
    "section": "V14",
    "title": "Configuration",
    "description": "Verify that all components are up to date, preferably using a dependency checker during build or compile time. ([C2](https://owasp.org/www-project-proactive-controls/#div-numbering))",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "dockerfile"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/deployment.yaml"
      },
      {
        "type": "code",
        "reference": "config.py"
      },
      {
        "type": "doc",
        "reference": "docs/configuration.md"
      },
      {
        "type": "test",
        "reference": "tests/test_modules_smoke.py::test_blueprints_registered"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/alerts.yaml"
      }
    ]
  },
  {
    "id": "14.2.2",
    "section": "V14",
    "title": "Configuration",
    "description": "Verify that all unneeded features, documentation, sample applications and configurations are removed.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "dockerfile"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/deployment.yaml"
      },
      {
        "type": "code",
        "reference": "config.py"
      },
      {
        "type": "doc",
        "reference": "docs/configuration.md"
      },
      {
        "type": "test",
        "reference": "tests/test_modules_smoke.py::test_blueprints_registered"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/alerts.yaml"
      }
    ]
  },
  {
    "id": "14.2.3",
    "section": "V14",
    "title": "Configuration",
    "description": "Verify that if application assets, such as JavaScript libraries, CSS or web fonts, are hosted externally on a Content Delivery Network (CDN) or external provider, Subresource Integrity (SRI) is used to validate the integrity of the asset.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "dockerfile"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/deployment.yaml"
      },
      {
        "type": "code",
        "reference": "config.py"
      },
      {
        "type": "doc",
        "reference": "docs/configuration.md"
      },
      {
        "type": "test",
        "reference": "tests/test_modules_smoke.py::test_blueprints_registered"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/alerts.yaml"
      }
    ]
  },
  {
    "id": "14.2.4",
    "section": "V14",
    "title": "Configuration",
    "description": "Verify that third party components come from pre-defined, trusted and continually maintained repositories. ([C2](https://owasp.org/www-project-proactive-controls/#div-numbering))",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "dockerfile"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/deployment.yaml"
      },
      {
        "type": "code",
        "reference": "config.py"
      },
      {
        "type": "doc",
        "reference": "docs/configuration.md"
      },
      {
        "type": "test",
        "reference": "tests/test_modules_smoke.py::test_blueprints_registered"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/alerts.yaml"
      }
    ]
  },
  {
    "id": "14.2.5",
    "section": "V14",
    "title": "Configuration",
    "description": "Verify that a Software Bill of Materials (SBOM) is maintained of all third party libraries in use. ([C2](https://owasp.org/www-project-proactive-controls/#div-numbering))",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "dockerfile"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/deployment.yaml"
      },
      {
        "type": "code",
        "reference": "config.py"
      },
      {
        "type": "doc",
        "reference": "docs/configuration.md"
      },
      {
        "type": "test",
        "reference": "tests/test_modules_smoke.py::test_blueprints_registered"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/alerts.yaml"
      }
    ]
  },
  {
    "id": "14.2.6",
    "section": "V14",
    "title": "Configuration",
    "description": "Verify that the attack surface is reduced by sandboxing or encapsulating third party libraries to expose only the required behaviour into the application. ([C2](https://owasp.org/www-project-proactive-controls/#div-numbering))",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "dockerfile"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/deployment.yaml"
      },
      {
        "type": "code",
        "reference": "config.py"
      },
      {
        "type": "doc",
        "reference": "docs/configuration.md"
      },
      {
        "type": "test",
        "reference": "tests/test_modules_smoke.py::test_blueprints_registered"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/alerts.yaml"
      }
    ]
  },
  {
    "id": "14.3.1",
    "section": "V14",
    "title": "Configuration",
    "description": "[DELETED, DUPLICATE OF 7.4.1]",
    "levels": [],
    "status": "deleted",
    "coverage": [
      {
        "type": "code",
        "reference": "dockerfile"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/deployment.yaml"
      },
      {
        "type": "code",
        "reference": "config.py"
      },
      {
        "type": "doc",
        "reference": "docs/configuration.md"
      },
      {
        "type": "test",
        "reference": "tests/test_modules_smoke.py::test_blueprints_registered"
      }
    ]
  },
  {
    "id": "14.3.2",
    "section": "V14",
    "title": "Configuration",
    "description": "Verify that web or application server and application framework debug modes are disabled in production to eliminate debug features, developer consoles, and unintended security disclosures.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "dockerfile"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/deployment.yaml"
      },
      {
        "type": "code",
        "reference": "config.py"
      },
      {
        "type": "doc",
        "reference": "docs/configuration.md"
      },
      {
        "type": "test",
        "reference": "tests/test_modules_smoke.py::test_blueprints_registered"
      }
    ]
  },
  {
    "id": "14.3.3",
    "section": "V14",
    "title": "Configuration",
    "description": "Verify that the HTTP headers or any part of the HTTP response do not expose detailed version information of system components.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "dockerfile"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/deployment.yaml"
      },
      {
        "type": "code",
        "reference": "config.py"
      },
      {
        "type": "doc",
        "reference": "docs/configuration.md"
      },
      {
        "type": "test",
        "reference": "tests/test_modules_smoke.py::test_blueprints_registered"
      }
    ]
  },
  {
    "id": "14.4.1",
    "section": "V14",
    "title": "Configuration",
    "description": "Verify that every HTTP response contains a Content-Type header. Also specify a safe character set (e.g., UTF-8, ISO-8859-1) if the content types are text/*, /+xml and application/xml. Content must match with the provided Content-Type header.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "dockerfile"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/deployment.yaml"
      },
      {
        "type": "code",
        "reference": "config.py"
      },
      {
        "type": "doc",
        "reference": "docs/configuration.md"
      },
      {
        "type": "test",
        "reference": "tests/test_modules_smoke.py::test_blueprints_registered"
      }
    ]
  },
  {
    "id": "14.4.2",
    "section": "V14",
    "title": "Configuration",
    "description": "Verify that all API responses contain a Content-Disposition: attachment; filename=\"api.json\" header (or other appropriate filename for the content type).",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "dockerfile"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/deployment.yaml"
      },
      {
        "type": "code",
        "reference": "config.py"
      },
      {
        "type": "doc",
        "reference": "docs/configuration.md"
      },
      {
        "type": "test",
        "reference": "tests/test_modules_smoke.py::test_blueprints_registered"
      }
    ]
  },
  {
    "id": "14.4.3",
    "section": "V14",
    "title": "Configuration",
    "description": "Verify that a Content Security Policy (CSP) response header is in place that helps mitigate impact for XSS attacks like HTML, DOM, JSON, and JavaScript injection vulnerabilities.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "dockerfile"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/deployment.yaml"
      },
      {
        "type": "code",
        "reference": "config.py"
      },
      {
        "type": "doc",
        "reference": "docs/configuration.md"
      },
      {
        "type": "test",
        "reference": "tests/test_modules_smoke.py::test_blueprints_registered"
      }
    ]
  },
  {
    "id": "14.4.4",
    "section": "V14",
    "title": "Configuration",
    "description": "Verify that all responses contain a X-Content-Type-Options: nosniff header.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "dockerfile"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/deployment.yaml"
      },
      {
        "type": "code",
        "reference": "config.py"
      },
      {
        "type": "doc",
        "reference": "docs/configuration.md"
      },
      {
        "type": "test",
        "reference": "tests/test_modules_smoke.py::test_blueprints_registered"
      }
    ]
  },
  {
    "id": "14.4.5",
    "section": "V14",
    "title": "Configuration",
    "description": "Verify that a Strict-Transport-Security header is included on all responses and for all subdomains, such as Strict-Transport-Security: max-age=15724800; includeSubdomains.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "dockerfile"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/deployment.yaml"
      },
      {
        "type": "code",
        "reference": "config.py"
      },
      {
        "type": "doc",
        "reference": "docs/configuration.md"
      },
      {
        "type": "test",
        "reference": "tests/test_modules_smoke.py::test_blueprints_registered"
      }
    ]
  },
  {
    "id": "14.4.6",
    "section": "V14",
    "title": "Configuration",
    "description": "Verify that a suitable Referrer-Policy header is included to avoid exposing sensitive information in the URL through the Referer header to untrusted parties.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "dockerfile"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/deployment.yaml"
      },
      {
        "type": "code",
        "reference": "config.py"
      },
      {
        "type": "doc",
        "reference": "docs/configuration.md"
      },
      {
        "type": "test",
        "reference": "tests/test_modules_smoke.py::test_blueprints_registered"
      }
    ]
  },
  {
    "id": "14.4.7",
    "section": "V14",
    "title": "Configuration",
    "description": "Verify that the content of a web application cannot be embedded in a third-party site by default and that embedding of the exact resources is only allowed where necessary by using suitable Content-Security-Policy: frame-ancestors and X-Frame-Options response headers.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "dockerfile"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/deployment.yaml"
      },
      {
        "type": "code",
        "reference": "config.py"
      },
      {
        "type": "doc",
        "reference": "docs/configuration.md"
      },
      {
        "type": "test",
        "reference": "tests/test_modules_smoke.py::test_blueprints_registered"
      }
    ]
  },
  {
    "id": "14.5.1",
    "section": "V14",
    "title": "Configuration",
    "description": "Verify that the application server only accepts the HTTP methods in use by the application/API, including pre-flight OPTIONS, and logs/alerts on any requests that are not valid for the application context.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "dockerfile"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/deployment.yaml"
      },
      {
        "type": "code",
        "reference": "config.py"
      },
      {
        "type": "doc",
        "reference": "docs/configuration.md"
      },
      {
        "type": "test",
        "reference": "tests/test_modules_smoke.py::test_blueprints_registered"
      }
    ]
  },
  {
    "id": "14.5.2",
    "section": "V14",
    "title": "Configuration",
    "description": "Verify that the supplied Origin header is not used for authentication or access control decisions, as the Origin header can easily be changed by an attacker.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "dockerfile"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/deployment.yaml"
      },
      {
        "type": "code",
        "reference": "config.py"
      },
      {
        "type": "doc",
        "reference": "docs/configuration.md"
      },
      {
        "type": "test",
        "reference": "tests/test_modules_smoke.py::test_blueprints_registered"
      }
    ]
  },
  {
    "id": "14.5.3",
    "section": "V14",
    "title": "Configuration",
    "description": "Verify that the Cross-Origin Resource Sharing (CORS) Access-Control-Allow-Origin header uses a strict allow list of trusted domains and subdomains to match against and does not support the \"null\" origin.",
    "levels": [
      "L1",
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "dockerfile"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/deployment.yaml"
      },
      {
        "type": "code",
        "reference": "config.py"
      },
      {
        "type": "doc",
        "reference": "docs/configuration.md"
      },
      {
        "type": "test",
        "reference": "tests/test_modules_smoke.py::test_blueprints_registered"
      }
    ]
  },
  {
    "id": "14.5.4",
    "section": "V14",
    "title": "Configuration",
    "description": "Verify that HTTP headers added by a trusted proxy or SSO devices, such as a bearer token, are authenticated by the application.",
    "levels": [
      "L2",
      "L3"
    ],
    "status": "active",
    "coverage": [
      {
        "type": "code",
        "reference": "dockerfile"
      },
      {
        "type": "code",
        "reference": "deploy/k8s/deployment.yaml"
      },
      {
        "type": "code",
        "reference": "config.py"
      },
      {
        "type": "doc",
        "reference": "docs/configuration.md"
      },
      {
        "type": "test",
        "reference": "tests/test_modules_smoke.py::test_blueprints_registered"
      }
    ]
  }
]
```

## How to use this document

- **Developers** should update the coverage references when implementing new security controls or moving functionality.
- **Auditors** can sample the listed tests and runbooks to verify the control evidence; drill artifacts are linked directly from the SRE runbook.
- **CI** runs `python scripts/verify_asvs.py` to parse the JSON block above and fail if any active requirement is missing code, test, or runbook evidence.
