# HR Lifecycle Module

This document describes the full employee lifecycle flows implemented under the `/hr` blueprint.

## 1. Employee Lifecycle

- **Onboarding**
  - Endpoint: `POST /hr/employees/<id>/onboarding`
  - Data: `start_date`, `contract_type` (`permanent` | `contract`), `checklist`, `completed`, `notes`
  - Behaviour:
    - Upserts a single onboarding record per employee per org.
    - Can be updated by HR/Admin.

- **Offboarding**
  - Endpoint: `POST /hr/employees/<id>/offboarding`
  - Data: `last_working_day`, `reason`, `checklist`, `completed`, `notes`
  - Behaviour:
    - Creates an offboarding record.
    - Marks `Employee.is_active = False`.

## 2. Performance Reviews

- Endpoint: `GET/POST /hr/employees/<id>/reviews`
- Each review has `period_start`, `period_end`, `score`, optional `rating` and `summary`.
- Only `hr` and `admin` roles may create and view reviews.

## 3. Leave Management

- **Employee self-service**
  - Endpoint: `POST /hr/employees/<id>/leave`
  - Only the employee (or HR/Admin) may create leave for `<id>`.
- **HR/Admin decision**
  - Endpoint: `POST /hr/leave/<leave_id>/decision`
  - `decision` must be `approved` or `rejected`.
  - Records the approver and `decided_at`.

## 4. Edge Cases

- Contract vs permanent staff:
  - Contract type is stored on `HROnboarding.contract_type`.
  - Policy decisions (max leave, probation periods) must be enforced in business logic that consumes this model.
- Rehiring:
  - Multiple onboarding records are possible only if you extend the model; currently one record per employee is assumed.
- Data retention:
  - HR records (on/off-boarding, reviews, leave) should follow local labour law retention policies.
