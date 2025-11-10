# Database Migration Guide

## Phase 6 Migration Script

**File**: `phase6_add_indexes.sql`

**Purpose**: Add indexes to `tigu_prepare_goods` table for JOIN performance optimization.

**Changes**:
- Adds `idx_order_ids` index on `order_ids` column
- Adds `idx_delivery_shipping` composite index on `(delivery_type, shipping_type)`

**Risk Level**: MINIMAL (only adds indexes, no data changes)

**Execution Time**: < 5 seconds

---

## How to Run Migration

### Method 1: Using MySQL Command Line (Recommended)

```bash
# Navigate to migrations directory
cd /home/mli/tigub2b/tigub2b_delivery/migrations

# Run migration with sudo mysql
sudo mysql < phase6_add_indexes.sql

# Or with output visible
sudo mysql -v < phase6_add_indexes.sql
```

### Method 2: Using MySQL with Specific User

```bash
# If you have MySQL credentials
mysql -u tigu -p tigu_b2b < phase6_add_indexes.sql

# Enter password when prompted: T1gu125443!
```

### Method 3: Interactive Mode

```bash
# Connect to MySQL
sudo mysql

# Then run:
mysql> USE tigu_b2b;
mysql> source /home/mli/tigub2b/tigub2b_delivery/migrations/phase6_add_indexes.sql
```

### Method 4: Remote Database

```bash
# For remote database
mysql -h <remote_host> -u <username> -p <database_name> < phase6_add_indexes.sql

# Example:
mysql -h 192.168.1.100 -u tigu -p tigu_b2b < phase6_add_indexes.sql
```

---

## Pre-Migration Checklist

**Before running migration:**

1. **Backup Database** (IMPORTANT!)
   ```bash
   # Create backup
   sudo mysqldump tigu_b2b > /tmp/tigu_b2b_backup_$(date +%Y%m%d_%H%M%S).sql

   # Verify backup
   ls -lh /tmp/tigu_b2b_backup_*.sql
   ```

2. **Check Current Database**
   ```bash
   sudo mysql -e "USE tigu_b2b; SELECT COUNT(*) FROM tigu_prepare_goods;"
   ```

3. **Verify Tables Exist**
   ```bash
   sudo mysql -e "USE tigu_b2b; SHOW TABLES LIKE 'tigu_prepare_goods';"
   ```

---

## Verify Migration Success

**After running migration, verify:**

```bash
# Check indexes were created
sudo mysql -e "USE tigu_b2b; SHOW INDEX FROM tigu_prepare_goods WHERE Key_name IN ('idx_order_ids', 'idx_delivery_shipping');"
```

**Expected Output:**
```
Table              | Non_unique | Key_name             | Column_name
tigu_prepare_goods | 1          | idx_order_ids        | order_ids
tigu_prepare_goods | 1          | idx_delivery_shipping| delivery_type
tigu_prepare_goods | 1          | idx_delivery_shipping| shipping_type
```

---

## Test Query Performance

**Test that indexes are being used:**

```bash
sudo mysql -e "USE tigu_b2b; EXPLAIN SELECT delivery_type FROM tigu_prepare_goods WHERE order_ids LIKE '%123%' LIMIT 1;"
```

**Expected**: Should show index usage in the `key` column.

---

## Rollback Instructions

**If you need to undo the migration:**

```bash
# Create rollback script
cat > rollback_phase6.sql << 'EOF'
USE tigu_b2b;
ALTER TABLE tigu_prepare_goods DROP INDEX idx_order_ids;
ALTER TABLE tigu_prepare_goods DROP INDEX idx_delivery_shipping;
SELECT 'Rollback complete' as status;
EOF

# Run rollback
sudo mysql < rollback_phase6.sql
```

---

## Troubleshooting

### Error: "Index already exists"

**Cause**: Migration was already run.

**Solution**: This is safe - the script is idempotent (can run multiple times). The script will skip existing indexes.

### Error: "Table doesn't exist"

**Cause**: Database schema not set up correctly.

**Solution**:
```bash
# Check which tables exist
sudo mysql -e "USE tigu_b2b; SHOW TABLES LIKE 'tigu_%';"

# Verify you're on the correct database
sudo mysql -e "SELECT DATABASE();"
```

### Error: "Access denied"

**Cause**: Insufficient permissions.

**Solution**:
```bash
# Use sudo
sudo mysql < phase6_add_indexes.sql

# Or check credentials
mysql -u root -p < phase6_add_indexes.sql
```

### Slow Execution

**Cause**: Large table size (> 100k rows).

**Solution**: Normal for large tables. Wait for completion (usually < 1 minute even for 1M rows).

---

## Migration to Another Database

### Same Server, Different Database Name

```bash
# Edit the script to use different database
sed 's/tigu_b2b/your_database_name/g' phase6_add_indexes.sql > phase6_for_other_db.sql

# Run migration
sudo mysql < phase6_for_other_db.sql
```

### Different Server

```bash
# Copy migration file to remote server
scp phase6_add_indexes.sql user@remote-server:/tmp/

# SSH to remote server
ssh user@remote-server

# Run migration on remote server
sudo mysql < /tmp/phase6_add_indexes.sql
```

### Docker Container Database

```bash
# Copy file into container
docker cp phase6_add_indexes.sql mysql-container:/tmp/

# Run migration inside container
docker exec -i mysql-container mysql -u root -p < /tmp/phase6_add_indexes.sql

# Or interactive
docker exec -it mysql-container mysql -u root -p
mysql> source /tmp/phase6_add_indexes.sql
```

---

## Migration History

| Version | Date | Description | Status |
|---------|------|-------------|--------|
| Phase 6 | 2025-11-09 | Add indexes to tigu_prepare_goods | ✅ Ready |

---

## Support

**For issues:**
1. Check `/home/mli/tigub2b/tigub2b_delivery/PHASE6_DATABASE_MIGRATION_PLAN_REVISED.md`
2. Review logs: `sudo tail -f /var/log/mysql/error.log`
3. Verify table structure: `sudo mysql -e "DESCRIBE tigu_b2b.tigu_prepare_goods;"`

---

**Last Updated**: 2025-11-09
