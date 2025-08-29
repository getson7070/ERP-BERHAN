-- Row Level Security policies for tenant isolation
-- Enforces org_id scoping on core tables

-- Users table policy
CREATE POLICY users_org_access ON users
    USING (org_id = current_setting('app.org_id')::int);

-- Inventory table policy
CREATE POLICY inventory_org_access ON inventory_items
    USING (org_id = current_setting('app.org_id')::int);

-- Apply policies
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE inventory_items ENABLE ROW LEVEL SECURITY;
