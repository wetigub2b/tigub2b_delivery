# MySQL Marks Table Migration Guide

## Overview
This migration creates the `tigu_driver_marks` table in your existing MySQL database for storing map markers. This replaces the Supabase solution with a simpler, integrated MySQL approach.

## Files Changed

### Backend (BFF)
- ✅ `bff/app/api/v1/routes/marks.py` - API endpoint for marks
- ✅ `bff/app/schemas/marks.py` - Pydantic schemas
- ✅ `bff/app/services/marks_service.py` - Business logic
- ✅ `bff/app/api/v1/api.py` - Router registration

### Frontend
- ✅ `frontend/src/components/MapTab.vue` - Updated to use BFF API
- ✅ `frontend/package.json` - Removed @supabase/supabase-js
- ✅ `frontend/.env.local.example` - Removed Supabase config

### Database
- ✅ `migrations/create_tigu_driver_marks.sql` - Migration SQL

## Step-by-Step Migration

### Step 1: Run Database Migration

```bash
# Connect to MySQL
sudo mysql tigu_b2b

# Or if you need password
mysql -u your_user -p tigu_b2b

# Run the migration
source /home/mli/tigub2b/tigub2b_delivery/migrations/create_tigu_driver_marks.sql

# Or directly
sudo mysql tigu_b2b < /home/mli/tigub2b/tigub2b_delivery/migrations/create_tigu_driver_marks.sql
```

Expected output:
```
Query OK, 0 rows affected (0.05 sec)
Query OK, 10 rows affected (0.01 sec)
```

### Step 2: Verify Table Creation

```bash
sudo mysql -e "USE tigu_b2b; DESCRIBE tigu_driver_marks;"
```

Should show:
```
+-------------+---------------+------+-----+-------------------+
| Field       | Type          | Null | Key | Default           |
+-------------+---------------+------+-----+-------------------+
| id          | int           | NO   | PRI | NULL              |
| name        | varchar(255)  | NO   |     | NULL              |
| latitude    | decimal(10,8) | NO   | MUL | NULL              |
| longitude   | decimal(11,8) | NO   |     | NULL              |
| type        | varchar(50)   | YES  | MUL | NULL              |
| description | text          | YES  |     | NULL              |
| is_active   | tinyint(1)    | YES  | MUL | 1                 |
| created_at  | timestamp     | YES  |     | CURRENT_TIMESTAMP |
| updated_at  | timestamp     | YES  |     | CURRENT_TIMESTAMP |
+-------------+---------------+------+-----+-------------------+
```

### Step 3: Verify Sample Data

```bash
sudo mysql -e "USE tigu_b2b; SELECT COUNT(*) as total FROM tigu_driver_marks WHERE is_active = 1;"
```

Should return: `total: 10`

### Step 4: Remove Supabase Dependency

```bash
cd /home/mli/tigub2b/tigub2b_delivery/frontend
npm uninstall @supabase/supabase-js
```

### Step 5: Update Environment Variables

Edit your `.env.local` (if it exists):

```bash
cd /home/mli/tigub2b/tigub2b_delivery/frontend
nano .env.local
```

**Remove these lines** (no longer needed):
```
VITE_SUPABASE_URL=...
VITE_SUPABASE_ANON_KEY=...
```

**Keep these lines**:
```
VITE_API_URL=https://your-domain.com/api
VITE_MAPBOX_TOKEN=your-mapbox-token
VITE_FEATURE_MAP_TAB=true
```

### Step 6: Rebuild and Deploy

```bash
cd /home/mli/tigub2b/tigub2b_delivery

# Rebuild frontend
cd frontend
npm run build

# Deploy both backend and frontend
cd ..
./deploy_all.sh
```

## Testing

### Test 1: Check API Endpoint

```bash
# Get auth token first (login as driver)
TOKEN="your-driver-token"

# Test marks endpoint
curl -H "Authorization: Bearer $TOKEN" \
     http://localhost:8000/api/marks
```

Expected response:
```json
{
  "marks": [
    {
      "id": 1,
      "name": "Toronto Warehouse",
      "latitude": 43.6532,
      "longitude": -79.3832,
      "type": "Warehouse",
      "description": "Main distribution center in downtown Toronto",
      "is_active": true,
      "created_at": "2024-12-01T...",
      "updated_at": "2024-12-01T..."
    },
    ...
  ],
  "total": 10
}
```

### Test 2: Check Map in Browser

1. Login to driver dashboard
2. Click the "Map" tab (first tab)
3. Should see 10 markers in GTA area
4. Click markers to see popups with details

## Rollback (If Needed)

If you need to rollback:

```bash
# Drop the table
sudo mysql -e "USE tigu_b2b; DROP TABLE IF EXISTS tigu_driver_marks;"

# Remove backend files
rm /home/mli/tigub2b/tigub2b_delivery/bff/app/api/v1/routes/marks.py
rm /home/mli/tigub2b/tigub2b_delivery/bff/app/schemas/marks.py
rm /home/mli/tigub2b/tigub2b_delivery/bff/app/services/marks_service.py

# Reinstall Supabase (if needed)
cd /home/mli/tigub2b/tigub2b_delivery/frontend
npm install @supabase/supabase-js
```

## Adding More Markers

To add more markers:

```sql
USE tigu_b2b;

INSERT INTO tigu_driver_marks (name, latitude, longitude, type, description) VALUES
    ('New Location', 43.1234, -79.5678, 'Hub', 'Description here');
```

Or use MySQL admin tools like phpMyAdmin, MySQL Workbench, etc.

## Benefits Over Supabase

✅ **Simpler**: No external service dependency
✅ **Faster**: Same database as your orders
✅ **Cheaper**: No additional costs
✅ **Consistent**: All data in one place
✅ **Secure**: Uses existing auth system
✅ **Maintainable**: Easier to manage

## Troubleshooting

### Error: "Could not find table tigu_driver_marks"

**Solution**: Run the migration SQL again.

### Error: "Authorization required"

**Solution**: The marks endpoint requires authentication. Make sure you're logged in as a driver.

### Map shows no markers

**Check**:
1. Database has data: `SELECT COUNT(*) FROM tigu_driver_marks;`
2. API is running: `curl http://localhost:8000/api/marks`
3. Browser console for errors (F12)
4. VITE_API_URL is set correctly

### Migration fails with "Table already exists"

**Solution**: The migration uses `CREATE TABLE IF NOT EXISTS`, so it's safe to run multiple times. If you need to recreate it:

```sql
DROP TABLE IF EXISTS tigu_driver_marks;
-- Then run migration again
```

## Next Steps

- Add admin interface to manage markers (CRUD operations)
- Add marker filtering by type
- Add custom marker icons based on type
- Add distance calculation from driver location
- Add marker search functionality

