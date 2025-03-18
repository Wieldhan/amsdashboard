-- Drop existing policies
DROP POLICY IF EXISTS "Admin users can manage all users" ON users;
DROP POLICY IF EXISTS "Users can view their own data" ON users;
DROP POLICY IF EXISTS "Admin users can manage all branch mappings" ON branch_mapping;
DROP POLICY IF EXISTS "All authenticated users can view branch mappings" ON branch_mapping;

-- Create new policies using service role instead of admin context
-- Service role bypasses RLS completely, so these policies are for regular users

-- For users table
CREATE POLICY "Users can view their own data" 
ON users FOR SELECT 
USING (auth.uid()::text = user_id);

-- For branch mapping table - allow all authenticated users to view
CREATE POLICY "All authenticated users can view branch mappings" 
ON branch_mapping FOR SELECT 
USING (auth.role() = 'authenticated');

-- Make sure admin access is given to specific users if needed
UPDATE users SET is_admin = true WHERE user_id = 'admin';

-- Enable row-level security on all tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE branch_mapping ENABLE ROW LEVEL SECURITY; 