-- Pillar schema blueprint for ERP-BERHAN
-- Safe to run repeatedly thanks to IF NOT EXISTS and constraint guards.
-- UUID generation assumes `uuid-ossp` extension is enabled upstream.

-- 1. Identity & Access Model
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY,
    email CITEXT NOT NULL UNIQUE,
    phone CITEXT UNIQUE,
    password_hash TEXT NOT NULL,
    password_rotated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    must_reset_password BOOLEAN NOT NULL DEFAULT FALSE,
    failed_login_attempts INTEGER NOT NULL DEFAULT 0 CHECK (failed_login_attempts >= 0),
    locked_until TIMESTAMPTZ,
    password_version INTEGER NOT NULL DEFAULT 1 CHECK (password_version >= 1),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    user_type TEXT NOT NULL CHECK (user_type IN ('client','employee','admin')),
    mfa_secret TEXT,
    last_login_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_password_history (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    password_hash TEXT NOT NULL,
    rotated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, password_hash)
);

CREATE INDEX IF NOT EXISTS idx_user_password_history_user ON user_password_history(user_id, rotated_at DESC);

CREATE TABLE IF NOT EXISTS roles (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS permissions (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_roles (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, role_id)
);

CREATE TABLE IF NOT EXISTS role_permissions (
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    permission_id UUID NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
    granted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (role_id, permission_id)
);

CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_token_hash TEXT NOT NULL,
    refresh_token_hash TEXT,
    ip_address INET,
    user_agent TEXT,
    expires_at TIMESTAMPTZ NOT NULL,
    is_current BOOLEAN NOT NULL DEFAULT TRUE,
    revoked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_user_sessions_current ON user_sessions(user_id) WHERE is_current;
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_expires ON user_sessions(user_id, expires_at DESC);

CREATE TABLE IF NOT EXISTS auth_logs (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id UUID REFERENCES user_sessions(id) ON DELETE SET NULL,
    event_type TEXT NOT NULL,
    ip_address INET,
    user_agent TEXT,
    success BOOLEAN NOT NULL,
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_auth_logs_user_created ON auth_logs(user_id, created_at DESC);

CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    key_hash TEXT NOT NULL,
    last_used_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, name)
);

CREATE INDEX IF NOT EXISTS idx_api_keys_user_active ON api_keys(user_id) WHERE is_active;

-- 2. Client & Onboarding Model
CREATE TABLE IF NOT EXISTS clients (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    tin TEXT NOT NULL UNIQUE,
    institution_name TEXT NOT NULL,
    industry TEXT,
    status TEXT NOT NULL CHECK (status IN ('pending','approved','rejected','blocked')),
    risk_tier TEXT CHECK (risk_tier IN ('low','medium','high','critical')),
    blocked_reason TEXT,
    approved_by UUID REFERENCES users(id) ON DELETE SET NULL,
    approved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS client_addresses (
    id UUID PRIMARY KEY,
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    address_type TEXT NOT NULL CHECK (address_type IN ('billing','shipping','hq','branch')),
    line1 TEXT NOT NULL,
    line2 TEXT,
    city TEXT,
    state TEXT,
    postal_code TEXT,
    country TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_client_addresses_client ON client_addresses(client_id);

CREATE TABLE IF NOT EXISTS client_contacts (
    id UUID PRIMARY KEY,
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    email CITEXT,
    phone TEXT,
    role TEXT,
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_client_contacts_client ON client_contacts(client_id);

CREATE TABLE IF NOT EXISTS client_approvals (
    id UUID PRIMARY KEY,
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    reviewer_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    decision TEXT NOT NULL CHECK (decision IN ('approved','rejected')),
    notes TEXT,
    decided_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_client_approvals_client_decided ON client_approvals(client_id, decided_at DESC);

CREATE TABLE IF NOT EXISTS client_verifications (
    id UUID PRIMARY KEY,
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    reviewer_id UUID REFERENCES users(id) ON DELETE SET NULL,
    verification_type TEXT NOT NULL CHECK (verification_type IN ('kyc','aml','tin_validation','document_check')),
    status TEXT NOT NULL CHECK (status IN ('pending','in_progress','passed','failed')),
    reference_code TEXT,
    notes TEXT,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_client_verifications_status ON client_verifications(client_id, status);

CREATE TABLE IF NOT EXISTS client_onboarding_tasks (
    id UUID PRIMARY KEY,
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('pending','in_progress','completed','blocked')),
    due_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    assigned_to UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (client_id, name)
);
CREATE INDEX IF NOT EXISTS idx_client_onboarding_tasks_due ON client_onboarding_tasks(client_id, status, due_at);

CREATE TABLE IF NOT EXISTS client_invites (
    id UUID PRIMARY KEY,
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    email CITEXT NOT NULL,
    token_hash TEXT NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    sent_by UUID REFERENCES users(id) ON DELETE SET NULL,
    used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (client_id, email, is_active)
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_client_invites_token ON client_invites(token_hash);

-- 3. Employee & Supervisor Model
CREATE TABLE IF NOT EXISTS positions (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS employees (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    position_id UUID NOT NULL REFERENCES positions(id) ON DELETE RESTRICT,
    hire_date DATE NOT NULL,
    employment_type TEXT NOT NULL CHECK (employment_type IN ('full_time','part_time','contract')),
    supervisor_id UUID REFERENCES employees(id) ON DELETE SET NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (id <> supervisor_id)
);
CREATE INDEX IF NOT EXISTS idx_employees_supervisor ON employees(supervisor_id);

CREATE TABLE IF NOT EXISTS supervisor_links (
    id UUID PRIMARY KEY,
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    supervisor_id UUID NOT NULL REFERENCES employees(id) ON DELETE RESTRICT,
    level SMALLINT NOT NULL CHECK (level >= 1),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (employee_id, supervisor_id)
);
CREATE INDEX IF NOT EXISTS idx_supervisor_links_emp_level ON supervisor_links(employee_id, level);

CREATE TABLE IF NOT EXISTS approval_levels (
    id UUID PRIMARY KEY,
    position_id UUID NOT NULL REFERENCES positions(id) ON DELETE CASCADE,
    level SMALLINT NOT NULL CHECK (level >= 1),
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (position_id, level)
);

-- 4. Orders, Approvals, Commission Engine
CREATE TABLE IF NOT EXISTS orders (
    id UUID PRIMARY KEY,
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE RESTRICT,
    submitted_by UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    submitted_at TIMESTAMPTZ,
    status TEXT NOT NULL CHECK (status IN ('draft','submitted','approved','delivered')),
    total_amount NUMERIC(18,2) NOT NULL DEFAULT 0,
    discount NUMERIC(18,2) NOT NULL DEFAULT 0,
    final_amount NUMERIC(18,2) NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_orders_client_status ON orders(client_id, status);

CREATE TABLE IF NOT EXISTS order_items (
    id UUID PRIMARY KEY,
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_code TEXT NOT NULL,
    description TEXT,
    quantity NUMERIC(12,2) NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(18,2) NOT NULL CHECK (unit_price >= 0),
    discount NUMERIC(18,2) NOT NULL DEFAULT 0,
    final_amount NUMERIC(18,2) NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id);

CREATE TABLE IF NOT EXISTS order_status_history (
    id UUID PRIMARY KEY,
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    status TEXT NOT NULL CHECK (status IN ('draft','submitted','approved','delivered','cancelled')),
    changed_by UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    notes TEXT
);
CREATE INDEX IF NOT EXISTS idx_order_status_history_order ON order_status_history(order_id, changed_at DESC);

CREATE TABLE IF NOT EXISTS order_approvals (
    id UUID PRIMARY KEY,
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    approver_id UUID NOT NULL REFERENCES employees(id) ON DELETE RESTRICT,
    approval_level SMALLINT NOT NULL,
    decision TEXT NOT NULL CHECK (decision IN ('approved','rejected','needs_changes')),
    decided_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    notes TEXT
);
CREATE INDEX IF NOT EXISTS idx_order_approvals_order_level ON order_approvals(order_id, approval_level);

CREATE TABLE IF NOT EXISTS pricing_rules (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    rule_type TEXT NOT NULL CHECK (rule_type IN ('flat','percent','tier')),
    value NUMERIC(18,4) NOT NULL,
    criteria JSONB,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS commissions (
    id UUID PRIMARY KEY,
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE RESTRICT,
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    rule_id UUID REFERENCES pricing_rules(id) ON DELETE SET NULL,
    commission_type TEXT NOT NULL CHECK (commission_type IN ('flat','percent','tier')),
    amount NUMERIC(18,2) NOT NULL CHECK (amount >= 0),
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','approved','paid')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_commissions_employee_status ON commissions(employee_id, status);

CREATE TABLE IF NOT EXISTS delivery_records (
    id UUID PRIMARY KEY,
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    scheduled_date DATE,
    delivered_at TIMESTAMPTZ,
    delivery_status TEXT NOT NULL DEFAULT 'scheduled' CHECK (delivery_status IN ('scheduled','in_transit','delivered','failed')),
    handler_id UUID REFERENCES employees(id) ON DELETE SET NULL,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_delivery_records_order ON delivery_records(order_id);

-- 5. Maintenance, Geo, SLA & Escalation
CREATE TABLE IF NOT EXISTS maintenance_requests (
    id UUID PRIMARY KEY,
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE RESTRICT,
    device_id TEXT,
    issue_description TEXT NOT NULL,
    priority TEXT NOT NULL CHECK (priority IN ('low','medium','high','critical')),
    status TEXT NOT NULL,
    sla_due_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_maintenance_requests_client_status ON maintenance_requests(client_id, status);

CREATE TABLE IF NOT EXISTS maintenance_assignments (
    id UUID PRIMARY KEY,
    request_id UUID NOT NULL REFERENCES maintenance_requests(id) ON DELETE CASCADE,
    technician_id UUID NOT NULL REFERENCES employees(id) ON DELETE RESTRICT,
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    accepted_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    status TEXT NOT NULL DEFAULT 'assigned' CHECK (status IN ('assigned','in_progress','completed','declined'))
);
CREATE INDEX IF NOT EXISTS idx_maintenance_assignments_request ON maintenance_assignments(request_id);

CREATE TABLE IF NOT EXISTS maintenance_status_history (
    id UUID PRIMARY KEY,
    request_id UUID NOT NULL REFERENCES maintenance_requests(id) ON DELETE CASCADE,
    status TEXT NOT NULL,
    changed_by UUID REFERENCES employees(id) ON DELETE SET NULL,
    changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    notes TEXT
);
CREATE INDEX IF NOT EXISTS idx_maintenance_status_history_req ON maintenance_status_history(request_id, changed_at DESC);

CREATE TABLE IF NOT EXISTS maintenance_sla (
    id UUID PRIMARY KEY,
    request_id UUID NOT NULL REFERENCES maintenance_requests(id) ON DELETE CASCADE,
    response_due_at TIMESTAMPTZ,
    resolution_due_at TIMESTAMPTZ,
    acknowledged_at TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ,
    breached BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE UNIQUE INDEX IF NOT EXISTS uniq_maintenance_sla_request ON maintenance_sla(request_id);

CREATE TABLE IF NOT EXISTS maintenance_escalations (
    id UUID PRIMARY KEY,
    request_id UUID NOT NULL REFERENCES maintenance_requests(id) ON DELETE CASCADE,
    assignment_id UUID REFERENCES maintenance_assignments(id) ON DELETE SET NULL,
    escalated_to UUID NOT NULL REFERENCES employees(id) ON DELETE RESTRICT,
    reason TEXT,
    escalated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_maintenance_escalations_req ON maintenance_escalations(request_id, escalated_at DESC);

CREATE TABLE IF NOT EXISTS technician_locations (
    id UUID PRIMARY KEY,
    technician_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    latitude NUMERIC(10,6) NOT NULL,
    longitude NUMERIC(10,6) NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_technician_locations_tech_time ON technician_locations(technician_id, recorded_at DESC);

CREATE TABLE IF NOT EXISTS geo_events (
    id UUID PRIMARY KEY,
    technician_id UUID REFERENCES employees(id) ON DELETE SET NULL,
    device_id TEXT,
    event_type TEXT NOT NULL,
    payload JSONB,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_geo_events_type_time ON geo_events(event_type, occurred_at DESC);

-- 6. Procurement, Shipping, Customs, Warehouse & Landed Cost
CREATE TABLE IF NOT EXISTS suppliers (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    contact_email CITEXT,
    contact_phone TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS purchase_requests (
    id UUID PRIMARY KEY,
    requested_by UUID NOT NULL REFERENCES employees(id) ON DELETE RESTRICT,
    supplier_id UUID REFERENCES suppliers(id) ON DELETE SET NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft','submitted','approved','rejected')),
    total_amount NUMERIC(18,2) NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS purchase_orders (
    id UUID PRIMARY KEY,
    purchase_request_id UUID REFERENCES purchase_requests(id) ON DELETE SET NULL,
    supplier_id UUID NOT NULL REFERENCES suppliers(id) ON DELETE RESTRICT,
    status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open','sent','accepted','fulfilled','cancelled')),
    order_date DATE NOT NULL,
    expected_delivery DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_purchase_orders_supplier_status ON purchase_orders(supplier_id, status);

CREATE TABLE IF NOT EXISTS proforma_invoices (
    id UUID PRIMARY KEY,
    purchase_order_id UUID NOT NULL REFERENCES purchase_orders(id) ON DELETE CASCADE,
    invoice_number TEXT NOT NULL,
    amount NUMERIC(18,2) NOT NULL CHECK (amount >= 0),
    currency TEXT NOT NULL,
    issued_at DATE NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (purchase_order_id, invoice_number)
);

CREATE TABLE IF NOT EXISTS shipments (
    id UUID PRIMARY KEY,
    purchase_order_id UUID NOT NULL REFERENCES purchase_orders(id) ON DELETE CASCADE,
    tracking_number TEXT,
    carrier TEXT,
    status TEXT NOT NULL DEFAULT 'preparing' CHECK (status IN ('preparing','in_transit','arrived','delivered','delayed')),
    departed_at TIMESTAMPTZ,
    arrived_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_shipments_po_status ON shipments(purchase_order_id, status);

CREATE TABLE IF NOT EXISTS shipping_documents (
    id UUID PRIMARY KEY,
    shipment_id UUID NOT NULL REFERENCES shipments(id) ON DELETE CASCADE,
    document_type TEXT NOT NULL,
    document_number TEXT,
    file_uri TEXT,
    issued_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_shipping_documents_shipment ON shipping_documents(shipment_id);

CREATE TABLE IF NOT EXISTS customs_entries (
    id UUID PRIMARY KEY,
    shipment_id UUID NOT NULL REFERENCES shipments(id) ON DELETE CASCADE,
    entry_number TEXT NOT NULL,
    duty NUMERIC(18,2) NOT NULL DEFAULT 0,
    vat NUMERIC(18,2) NOT NULL DEFAULT 0,
    fees NUMERIC(18,2) NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','filed','cleared','rejected')),
    filed_at TIMESTAMPTZ,
    cleared_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (shipment_id, entry_number)
);
CREATE INDEX IF NOT EXISTS idx_customs_entries_status ON customs_entries(status, filed_at);

CREATE TABLE IF NOT EXISTS warehouse_intake (
    id UUID PRIMARY KEY,
    shipment_id UUID NOT NULL REFERENCES shipments(id) ON DELETE CASCADE,
    warehouse_location TEXT NOT NULL,
    received_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    received_by UUID REFERENCES employees(id) ON DELETE SET NULL,
    quantity NUMERIC(18,2) NOT NULL CHECK (quantity >= 0),
    condition_notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_warehouse_intake_shipment ON warehouse_intake(shipment_id);

CREATE TABLE IF NOT EXISTS landed_costs (
    id UUID PRIMARY KEY,
    shipment_id UUID NOT NULL REFERENCES shipments(id) ON DELETE CASCADE,
    duty NUMERIC(18,2) NOT NULL DEFAULT 0 CHECK (duty >= 0),
    vat NUMERIC(18,2) NOT NULL DEFAULT 0 CHECK (vat >= 0),
    freight NUMERIC(18,2) NOT NULL DEFAULT 0 CHECK (freight >= 0),
    bank_charges NUMERIC(18,2) NOT NULL DEFAULT 0 CHECK (bank_charges >= 0),
    warehouse_fees NUMERIC(18,2) NOT NULL DEFAULT 0 CHECK (warehouse_fees >= 0),
    other_costs NUMERIC(18,2) NOT NULL DEFAULT 0 CHECK (other_costs >= 0),
    total_landed_cost NUMERIC(18,2) GENERATED ALWAYS AS (duty + vat + freight + bank_charges + warehouse_fees + other_costs) STORED,
    allocated_cost_per_unit NUMERIC(18,4),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (shipment_id)
);
CREATE INDEX IF NOT EXISTS idx_landed_costs_shipment ON landed_costs(shipment_id);
