-- Create branch_mapping table
CREATE TABLE IF NOT EXISTS branch_mapping (
    kode_cabang VARCHAR(2) PRIMARY KEY,
    nama_cabang TEXT NOT NULL,
    source VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create product_mapping tables
CREATE TABLE IF NOT EXISTS deposito_product_mapping (
    kode_produk VARCHAR(50) PRIMARY KEY,
    nama_produk TEXT NOT NULL,
    source VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tabungan_product_mapping (
    kode_produk VARCHAR(50) PRIMARY KEY,
    nama_produk TEXT NOT NULL,
    source VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS pembiayaan_product_mapping (
    kode_produk VARCHAR(50) PRIMARY KEY,
    nama_produk TEXT NOT NULL,
    source VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS rahn_product_mapping (
    kode_produk VARCHAR(50) PRIMARY KEY,
    nama_produk TEXT NOT NULL,
    source VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create deposito_data table
CREATE TABLE IF NOT EXISTS deposito_data (
    tanggal DATE,
    kode_cabang VARCHAR(2),
    kode_produk VARCHAR(50),
    nominal DECIMAL(18,2),
    source VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create tabungan_data table
CREATE TABLE IF NOT EXISTS tabungan_data (
    tanggal DATE,
    kode_cabang VARCHAR(2),
    kode_produk VARCHAR(50),
    nominal DECIMAL(18,2),
    source VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create pembiayaan_data table
CREATE TABLE IF NOT EXISTS pembiayaan_data (
    tanggal DATE,
    kode_cabang VARCHAR(2),
    kode_produk VARCHAR(50),
    kolektibilitas INT,
    jml_pencairan DECIMAL(18,2),
    byr_pokok DECIMAL(18,2),
    outstanding DECIMAL(18,2),
    kd_sts_pemb VARCHAR(2),
    kode_grup1 VARCHAR(10),
    kode_grup2 VARCHAR(10),
    kd_kolektor VARCHAR(4),
    source VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create group_mapping tables
CREATE TABLE IF NOT EXISTS grup1_mapping (
    kode_grup1 VARCHAR(10) PRIMARY KEY,
    nama_grup TEXT NOT NULL,
    keterangan TEXT,
    source VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS grup2_mapping (
    kode_grup2 VARCHAR(10) PRIMARY KEY,
    nama_grup TEXT NOT NULL,
    keterangan TEXT,
    source VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create rahn_data table
CREATE TABLE IF NOT EXISTS rahn_data (
    tanggal DATE,
    kode_cabang VARCHAR(2),
    kode_produk VARCHAR(50),
    nominal DECIMAL(18,2),
    kolektibilitas INT,
    source VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    password_hash TEXT NOT NULL,
    is_admin BOOLEAN NOT NULL,
    branch_access TEXT NOT NULL,
    tab_access TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create functions for updated_at timestamp
CREATE OR REPLACE FUNCTION update_modified_column() 
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for updated_at
CREATE TRIGGER update_deposito_data_updated_at
BEFORE UPDATE ON deposito_data
FOR EACH ROW
EXECUTE FUNCTION update_modified_column();

CREATE TRIGGER update_tabungan_data_updated_at
BEFORE UPDATE ON tabungan_data
FOR EACH ROW
EXECUTE FUNCTION update_modified_column();

CREATE TRIGGER update_pembiayaan_data_updated_at
BEFORE UPDATE ON pembiayaan_data
FOR EACH ROW
EXECUTE FUNCTION update_modified_column();

CREATE TRIGGER update_rahn_data_updated_at
BEFORE UPDATE ON rahn_data
FOR EACH ROW
EXECUTE FUNCTION update_modified_column();

CREATE TRIGGER update_branch_mapping_updated_at
BEFORE UPDATE ON branch_mapping
FOR EACH ROW
EXECUTE FUNCTION update_modified_column();

CREATE TRIGGER update_deposito_product_mapping_updated_at
BEFORE UPDATE ON deposito_product_mapping
FOR EACH ROW
EXECUTE FUNCTION update_modified_column();

CREATE TRIGGER update_tabungan_product_mapping_updated_at
BEFORE UPDATE ON tabungan_product_mapping
FOR EACH ROW
EXECUTE FUNCTION update_modified_column();

CREATE TRIGGER update_pembiayaan_product_mapping_updated_at
BEFORE UPDATE ON pembiayaan_product_mapping
FOR EACH ROW
EXECUTE FUNCTION update_modified_column();

CREATE TRIGGER update_rahn_product_mapping_updated_at
BEFORE UPDATE ON rahn_product_mapping
FOR EACH ROW
EXECUTE FUNCTION update_modified_column();

CREATE TRIGGER update_grup1_mapping_updated_at
BEFORE UPDATE ON grup1_mapping
FOR EACH ROW
EXECUTE FUNCTION update_modified_column();

CREATE TRIGGER update_grup2_mapping_updated_at
BEFORE UPDATE ON grup2_mapping
FOR EACH ROW
EXECUTE FUNCTION update_modified_column();

CREATE TRIGGER update_users_updated_at
BEFORE UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION update_modified_column();

-- User Management Functions

-- Function to create a new user
CREATE OR REPLACE FUNCTION create_user(
    p_user_id TEXT,
    p_password TEXT,
    p_branch_access TEXT,
    p_tab_access TEXT,
    p_is_admin BOOLEAN DEFAULT FALSE
) RETURNS BOOLEAN AS $$
DECLARE
    v_password_hash TEXT;
BEGIN
    -- Hash the password
    v_password_hash := encode(digest(p_password, 'sha256'), 'hex');
    
    -- Insert the new user
    BEGIN
        INSERT INTO users (user_id, password_hash, is_admin, branch_access, tab_access)
        VALUES (p_user_id, v_password_hash, p_is_admin, p_branch_access, p_tab_access);
        RETURN TRUE;
    EXCEPTION WHEN unique_violation THEN
        RETURN FALSE;
    END;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to verify a user's password
CREATE OR REPLACE FUNCTION verify_password(
    p_user_id TEXT,
    p_password TEXT
) RETURNS BOOLEAN AS $$
DECLARE
    v_password_hash TEXT;
    v_stored_hash TEXT;
BEGIN
    -- Hash the provided password
    v_password_hash := encode(digest(p_password, 'sha256'), 'hex');
    
    -- Get the stored hash
    SELECT password_hash INTO v_stored_hash
    FROM users
    WHERE user_id = p_user_id;
    
    -- Compare hashes
    RETURN v_stored_hash = v_password_hash;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to change a user's password
CREATE OR REPLACE FUNCTION change_password(
    p_user_id TEXT,
    p_old_password TEXT,
    p_new_password TEXT
) RETURNS BOOLEAN AS $$
DECLARE
    v_verified BOOLEAN;
BEGIN
    -- Verify the old password
    v_verified := verify_password(p_user_id, p_old_password);
    
    IF v_verified THEN
        -- Update with the new password hash
        UPDATE users
        SET password_hash = encode(digest(p_new_password, 'sha256'), 'hex')
        WHERE user_id = p_user_id;
        
        RETURN TRUE;
    ELSE
        RETURN FALSE;
    END IF;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function for admin to change a user's password
CREATE OR REPLACE FUNCTION admin_change_password(
    p_user_id TEXT,
    p_new_password TEXT
) RETURNS BOOLEAN AS $$
BEGIN
    -- Update with the new password hash
    UPDATE users
    SET password_hash = encode(digest(p_new_password, 'sha256'), 'hex')
    WHERE user_id = p_user_id;
    
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to update a user's access
CREATE OR REPLACE FUNCTION update_user_access(
    p_user_id TEXT,
    p_branch_access TEXT,
    p_tab_access TEXT
) RETURNS BOOLEAN AS $$
BEGIN
    UPDATE users
    SET branch_access = p_branch_access,
        tab_access = p_tab_access
    WHERE user_id = p_user_id;
    
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to delete a user
CREATE OR REPLACE FUNCTION delete_user(
    p_user_id TEXT
) RETURNS BOOLEAN AS $$
BEGIN
    -- Prevent deletion of admin user
    IF p_user_id = 'admin' THEN
        RETURN FALSE;
    END IF;
    
    DELETE FROM users
    WHERE user_id = p_user_id;
    
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create default admin user if not exists
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM users WHERE user_id = 'admin') THEN
        PERFORM create_user('admin', 'admin1122', 'all', 'all', TRUE);
    END IF;
END
$$;

-- Enable Row Level Security (RLS) on all tables
ALTER TABLE deposito_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE tabungan_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE pembiayaan_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE rahn_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE branch_mapping ENABLE ROW LEVEL SECURITY;
ALTER TABLE deposito_product_mapping ENABLE ROW LEVEL SECURITY;
ALTER TABLE tabungan_product_mapping ENABLE ROW LEVEL SECURITY;
ALTER TABLE pembiayaan_product_mapping ENABLE ROW LEVEL SECURITY;
ALTER TABLE rahn_product_mapping ENABLE ROW LEVEL SECURITY;
ALTER TABLE grup1_mapping ENABLE ROW LEVEL SECURITY;
ALTER TABLE grup2_mapping ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Drop existing policies for users table
DROP POLICY IF EXISTS "Admin users can manage all users" ON users;
DROP POLICY IF EXISTS "Users can view their own data" ON users;

-- Create new policies without recursion
CREATE POLICY "Admin users can manage all users" 
ON users FOR ALL 
USING (
    current_setting('app.is_admin', true)::boolean = true
);

CREATE POLICY "Users can view their own data" 
ON users FOR SELECT 
USING (auth.uid()::text = user_id);

-- Function to set admin context
CREATE OR REPLACE FUNCTION set_admin_context() RETURNS void AS $$
BEGIN
    PERFORM set_config('app.is_admin', 'true', false);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to clear admin context
CREATE OR REPLACE FUNCTION clear_admin_context() RETURNS void AS $$
BEGIN
    PERFORM set_config('app.is_admin', 'false', false);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- DEPOSITO DATA POLICIES
-- Admin users can manage all deposito data
CREATE POLICY "Admin users can manage all deposito data" 
ON deposito_data FOR ALL 
USING (
    auth.uid()::text IN (
        SELECT user_id FROM users WHERE is_admin = true
    )
);
-- Normal users can only view deposito data based on branch access
CREATE POLICY "Users can view deposito data based on branch access" 
ON deposito_data FOR SELECT 
USING (
    auth.uid()::text IN (
        SELECT user_id FROM users 
        WHERE branch_access = 'all' OR branch_access LIKE '%' || kode_cabang || '%'
    )
);

-- TABUNGAN DATA POLICIES
-- Admin users can manage all tabungan data
CREATE POLICY "Admin users can manage all tabungan data" 
ON tabungan_data FOR ALL 
USING (
    auth.uid()::text IN (
        SELECT user_id FROM users WHERE is_admin = true
    )
);
-- Normal users can only view tabungan data based on branch access
CREATE POLICY "Users can view tabungan data based on branch access" 
ON tabungan_data FOR SELECT 
USING (
    auth.uid()::text IN (
        SELECT user_id FROM users 
        WHERE branch_access = 'all' OR branch_access LIKE '%' || kode_cabang || '%'
    )
);

-- PEMBIAYAAN DATA POLICIES
-- Admin users can manage all pembiayaan data
CREATE POLICY "Admin users can manage all pembiayaan data" 
ON pembiayaan_data FOR ALL 
USING (
    auth.uid()::text IN (
        SELECT user_id FROM users WHERE is_admin = true
    )
);
-- Normal users can only view pembiayaan data based on branch access
CREATE POLICY "Users can view pembiayaan data based on branch access" 
ON pembiayaan_data FOR SELECT 
USING (
    auth.uid()::text IN (
        SELECT user_id FROM users 
        WHERE branch_access = 'all' OR branch_access LIKE '%' || kode_cabang || '%'
    )
);

-- RAHN DATA POLICIES
-- Admin users can manage all rahn data
CREATE POLICY "Admin users can manage all rahn data" 
ON rahn_data FOR ALL 
USING (
    auth.uid()::text IN (
        SELECT user_id FROM users WHERE is_admin = true
    )
);
-- Normal users can only view rahn data based on branch access
CREATE POLICY "Users can view rahn data based on branch access" 
ON rahn_data FOR SELECT 
USING (
    auth.uid()::text IN (
        SELECT user_id FROM users 
        WHERE branch_access = 'all' OR branch_access LIKE '%' || kode_cabang || '%'
    )
);

-- BRANCH MAPPING POLICIES
-- Admin users can manage all branch mappings
CREATE POLICY "Admin users can manage all branch mappings" 
ON branch_mapping FOR ALL 
USING (
    auth.uid()::text IN (
        SELECT user_id FROM users WHERE is_admin = true
    )
);
-- All authenticated users can view branch mappings
CREATE POLICY "All authenticated users can view branch mappings" 
ON branch_mapping FOR SELECT 
USING (auth.role() = 'authenticated');

-- DEPOSITO PRODUCT MAPPING POLICIES
-- Admin users can manage all deposito product mappings
CREATE POLICY "Admin users can manage all deposito product mappings" 
ON deposito_product_mapping FOR ALL 
USING (
    auth.uid()::text IN (
        SELECT user_id FROM users WHERE is_admin = true
    )
);
-- All authenticated users can view deposito product mappings
CREATE POLICY "All authenticated users can view deposito product mappings" 
ON deposito_product_mapping FOR SELECT 
USING (auth.role() = 'authenticated');

-- TABUNGAN PRODUCT MAPPING POLICIES
-- Admin users can manage all tabungan product mappings
CREATE POLICY "Admin users can manage all tabungan product mappings" 
ON tabungan_product_mapping FOR ALL 
USING (
    auth.uid()::text IN (
        SELECT user_id FROM users WHERE is_admin = true
    )
);
-- All authenticated users can view tabungan product mappings
CREATE POLICY "All authenticated users can view tabungan product mappings" 
ON tabungan_product_mapping FOR SELECT 
USING (auth.role() = 'authenticated');

-- PEMBIAYAAN PRODUCT MAPPING POLICIES
-- Admin users can manage all pembiayaan product mappings
CREATE POLICY "Admin users can manage all pembiayaan product mappings" 
ON pembiayaan_product_mapping FOR ALL 
USING (
    auth.uid()::text IN (
        SELECT user_id FROM users WHERE is_admin = true
    )
);
--All authenticated users can view pembiayaan product mappings
CREATE POLICY "All authenticated users can view pembiayaan product mappings" 
ON pembiayaan_product_mapping FOR SELECT 
USING (auth.role() = 'authenticated');

-- Rahn product mappings
-- Admin users can manage all pembiayaan product mappings
CREATE POLICY "Admin users can manage all rahn product mappings" 
ON rahn_product_mapping FOR ALL 
USING (
    auth.uid()::text IN (
        SELECT user_id FROM users WHERE is_admin = true
    )
);
--All authenticated users can view pembiayaan product mappings
CREATE POLICY "All authenticated users can view rahn product mappings" 
ON rahn_product_mapping FOR SELECT 
USING (auth.role() = 'authenticated');

-- GROUP MAPPING POLICIES

-- Group 1 mappings
CREATE POLICY "Admin users can manage all grup1 mappings" 
ON grup1_mapping FOR ALL 
USING (
    auth.uid()::text IN (
        SELECT user_id FROM users WHERE is_admin = true
    )
);

CREATE POLICY "All authenticated users can view grup1 mappings" 
ON grup1_mapping FOR SELECT 
USING (auth.role() = 'authenticated');

-- Group 2 mappings
CREATE POLICY "Admin users can manage all grup2 mappings" 
ON grup2_mapping FOR ALL 
USING (
    auth.uid()::text IN (
        SELECT user_id FROM users WHERE is_admin = true
    )
);

CREATE POLICY "All authenticated users can view grup2 mappings" 
ON grup2_mapping FOR SELECT 
USING (auth.role() = 'authenticated');

-- Indexes for deposito_data
CREATE INDEX IF NOT EXISTS idx_deposito_data_tanggal ON deposito_data(tanggal);
CREATE INDEX IF NOT EXISTS idx_deposito_data_kode_cabang ON deposito_data(kode_cabang);
CREATE INDEX IF NOT EXISTS idx_deposito_data_kode_produk ON deposito_data(kode_produk);
CREATE INDEX IF NOT EXISTS idx_deposito_data_tanggal_cabang ON deposito_data(tanggal, kode_cabang);
CREATE INDEX IF NOT EXISTS idx_deposito_data_tanggal_produk ON deposito_data(tanggal, kode_produk);
CREATE INDEX IF NOT EXISTS idx_deposito_data_updated_at ON deposito_data(updated_at);

-- Indexes for tabungan_data
CREATE INDEX IF NOT EXISTS idx_tabungan_data_tanggal ON tabungan_data(tanggal);
CREATE INDEX IF NOT EXISTS idx_tabungan_data_kode_cabang ON tabungan_data(kode_cabang);
CREATE INDEX IF NOT EXISTS idx_tabungan_data_kode_produk ON tabungan_data(kode_produk);
CREATE INDEX IF NOT EXISTS idx_tabungan_data_tanggal_cabang ON tabungan_data(tanggal, kode_cabang);
CREATE INDEX IF NOT EXISTS idx_tabungan_data_tanggal_produk ON tabungan_data(tanggal, kode_produk);
CREATE INDEX IF NOT EXISTS idx_tabungan_data_updated_at ON tabungan_data(updated_at);

-- Indexes for pembiayaan_data
CREATE INDEX IF NOT EXISTS idx_pembiayaan_data_tanggal ON pembiayaan_data(tanggal);
CREATE INDEX IF NOT EXISTS idx_pembiayaan_data_kode_cabang ON pembiayaan_data(kode_cabang);
CREATE INDEX IF NOT EXISTS idx_pembiayaan_data_kode_produk ON pembiayaan_data(kode_produk);
CREATE INDEX IF NOT EXISTS idx_pembiayaan_data_kolektibilitas ON pembiayaan_data(kolektibilitas);
CREATE INDEX IF NOT EXISTS idx_pembiayaan_data_kode_grup1 ON pembiayaan_data(kode_grup1);
CREATE INDEX IF NOT EXISTS idx_pembiayaan_data_kode_grup2 ON pembiayaan_data(kode_grup2);
CREATE INDEX IF NOT EXISTS idx_pembiayaan_data_tanggal_cabang ON pembiayaan_data(tanggal, kode_cabang);
CREATE INDEX IF NOT EXISTS idx_pembiayaan_data_tanggal_produk ON pembiayaan_data(tanggal, kode_produk);
CREATE INDEX IF NOT EXISTS idx_pembiayaan_data_updated_at ON pembiayaan_data(updated_at);

-- Indexes for rahn_data
CREATE INDEX IF NOT EXISTS idx_rahn_data_tanggal ON rahn_data(tanggal);
CREATE INDEX IF NOT EXISTS idx_rahn_data_kode_cabang ON rahn_data(kode_cabang);
CREATE INDEX IF NOT EXISTS idx_rahn_data_kode_produk ON rahn_data(kode_produk);
CREATE INDEX IF NOT EXISTS idx_rahn_data_kolektibilitas ON rahn_data(kolektibilitas);
CREATE INDEX IF NOT EXISTS idx_rahn_data_tanggal_cabang ON rahn_data(tanggal, kode_cabang);
CREATE INDEX IF NOT EXISTS idx_rahn_data_tanggal_produk ON rahn_data(tanggal, kode_produk);
CREATE INDEX IF NOT EXISTS idx_rahn_data_updated_at ON rahn_data(updated_at);

-- Indexes for users table
CREATE INDEX IF NOT EXISTS idx_users_is_admin ON users(is_admin);
CREATE INDEX IF NOT EXISTS idx_users_updated_at ON users(updated_at);

-- ============================================================================
-- SUMMARY VIEWS
-- ============================================================================

-- View for overall database summary (all tables)
CREATE OR REPLACE VIEW database_summary AS
SELECT
    'branch_mapping' AS table_name,
    MAX(updated_at) AS last_update,
    COUNT(*) AS row_count
FROM branch_mapping
UNION ALL
SELECT
    'deposito_product_mapping' AS table_name,
    MAX(updated_at) AS last_update,
    COUNT(*) AS row_count
FROM deposito_product_mapping
UNION ALL
SELECT
    'tabungan_product_mapping' AS table_name,
    MAX(updated_at) AS last_update,
    COUNT(*) AS row_count
FROM tabungan_product_mapping
UNION ALL
SELECT
    'pembiayaan_product_mapping' AS table_name,
    MAX(updated_at) AS last_update,
    COUNT(*) AS row_count
FROM pembiayaan_product_mapping
UNION ALL
SELECT
    'rahn_product_mapping' AS table_name,
    MAX(updated_at) AS last_update,
    COUNT(*) AS row_count
FROM rahn_product_mapping
UNION ALL
SELECT
    'grup1_mapping' AS table_name,
    MAX(updated_at) AS last_update,
    COUNT(*) AS row_count
FROM grup1_mapping
UNION ALL
SELECT
    'grup2_mapping' AS table_name,
    MAX(updated_at) AS last_update,
    COUNT(*) AS row_count
FROM grup2_mapping
UNION ALL
SELECT
    'deposito_data' AS table_name,
    MAX(updated_at) AS last_update,
    COUNT(*) AS row_count
FROM deposito_data
UNION ALL
SELECT
    'tabungan_data' AS table_name,
    MAX(updated_at) AS last_update,
    COUNT(*) AS row_count
FROM tabungan_data
UNION ALL
SELECT
    'pembiayaan_data' AS table_name,
    MAX(updated_at) AS last_update,
    COUNT(*) AS row_count
FROM pembiayaan_data
UNION ALL
SELECT
    'rahn_data' AS table_name,
    MAX(updated_at) AS last_update,
    COUNT(*) AS row_count
FROM rahn_data
ORDER BY table_name;

-- Function to generate period string (e.g., 'Jan 2021')
CREATE OR REPLACE FUNCTION get_period_string(date_value DATE) 
RETURNS TEXT AS $$
BEGIN
    RETURN TO_CHAR(date_value, 'Mon YYYY');
END;
$$ LANGUAGE plpgsql;

-- View for deposito_data summary by period
CREATE OR REPLACE VIEW deposito_data_summary AS
SELECT
    'deposito_data' AS table_name,
    get_period_string(tanggal) AS period,
    COUNT(*) AS row_count,
    MAX(updated_at) AS last_update
FROM deposito_data
GROUP BY get_period_string(tanggal)
ORDER BY MIN(tanggal) DESC;

-- View for tabungan_data summary by period
CREATE OR REPLACE VIEW tabungan_data_summary AS
SELECT
    'tabungan_data' AS table_name,
    get_period_string(tanggal) AS period,
    COUNT(*) AS row_count,
    MAX(updated_at) AS last_update
FROM tabungan_data
GROUP BY get_period_string(tanggal)
ORDER BY MIN(tanggal) DESC;

-- View for pembiayaan_data summary by period
CREATE OR REPLACE VIEW pembiayaan_data_summary AS
SELECT
    'pembiayaan_data' AS table_name,
    get_period_string(tanggal) AS period,
    COUNT(*) AS row_count,
    MAX(updated_at) AS last_update
FROM pembiayaan_data
GROUP BY get_period_string(tanggal)
ORDER BY MIN(tanggal) DESC;

-- View for rahn_data summary by period
CREATE OR REPLACE VIEW rahn_data_summary AS
SELECT
    'rahn_data' AS table_name,
    get_period_string(tanggal) AS period,
    COUNT(*) AS row_count,
    MAX(updated_at) AS last_update
FROM rahn_data
GROUP BY get_period_string(tanggal)
ORDER BY MIN(tanggal) DESC;

-- Combined view for all data tables by period
CREATE OR REPLACE VIEW all_data_summary_by_period AS
SELECT * FROM deposito_data_summary
UNION ALL
SELECT * FROM tabungan_data_summary
UNION ALL
SELECT * FROM pembiayaan_data_summary
UNION ALL
SELECT * FROM rahn_data_summary
ORDER BY table_name, period; 