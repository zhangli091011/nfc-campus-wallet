-- Test script to validate the NFC Campus E-Wallet database schema
-- Run this after creating the schema to verify everything works correctly

-- Test 1: Create test users
INSERT INTO users (uid, balance) VALUES ('A1B2C3D4', 100.00);
INSERT INTO users (uid, balance) VALUES ('E5F6G7H8', 250.50);
INSERT INTO users (uid) VALUES ('I9J0K1L2'); -- Test default balance of 0.00

-- Test 2: Verify users created
SELECT 'Test 1: Users Created' AS test_name;
SELECT * FROM users;

-- Test 3: Test UID uniqueness constraint (this should fail)
SELECT 'Test 2: UID Uniqueness (should fail)' AS test_name;
-- Uncomment to test: INSERT INTO users (uid, balance) VALUES ('A1B2C3D4', 50.00);

-- Test 4: Record payment transaction
INSERT INTO transactions (uid, type, amount, balance_after, merchant_id)
VALUES ('A1B2C3D4', 'payment', 25.00, 75.00, 'MERCHANT001');

-- Test 5: Record recharge transaction
INSERT INTO transactions (uid, type, amount, balance_after)
VALUES ('A1B2C3D4', 'recharge', 50.00, 125.00);

-- Test 6: Record payment without merchant_id
INSERT INTO transactions (uid, type, amount, balance_after)
VALUES ('E5F6G7H8', 'payment', 30.50, 220.00);

-- Test 7: Verify transactions created
SELECT 'Test 3: Transactions Created' AS test_name;
SELECT * FROM transactions;

-- Test 8: Test foreign key constraint
SELECT 'Test 4: Foreign Key Constraint' AS test_name;
-- This should fail because UID doesn't exist:
-- INSERT INTO transactions (uid, type, amount, balance_after) VALUES ('INVALID', 'payment', 10.00, 0.00);

-- Test 9: Query transaction history for a user (ordered by date descending)
SELECT 'Test 5: Transaction History for A1B2C3D4' AS test_name;
SELECT * FROM transactions WHERE uid = 'A1B2C3D4' ORDER BY created_at DESC;

-- Test 10: Test cascade delete
SELECT 'Test 6: Cascade Delete' AS test_name;
DELETE FROM users WHERE uid = 'I9J0K1L2';
-- Verify user and their transactions are deleted
SELECT COUNT(*) AS remaining_users FROM users;
SELECT COUNT(*) AS remaining_transactions FROM transactions WHERE uid = 'I9J0K1L2';

-- Test 11: Verify indexes exist
SELECT 'Test 7: Verify Indexes' AS test_name;
SHOW INDEX FROM users;
SHOW INDEX FROM transactions;

-- Test 12: Test currency precision
SELECT 'Test 8: Currency Precision' AS test_name;
INSERT INTO users (uid, balance) VALUES ('PRECISION_TEST', 123.45);
SELECT uid, balance FROM users WHERE uid = 'PRECISION_TEST';

-- Cleanup
SELECT 'Cleanup: Removing test data' AS test_name;
DELETE FROM transactions;
DELETE FROM users;

SELECT 'All tests completed successfully!' AS result;
