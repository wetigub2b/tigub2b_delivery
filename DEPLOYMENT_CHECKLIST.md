# Deployment Checklist - Dual Workflow Implementation

**Feature Branch**: `feature/updated-workflow`
**Target Branch**: `main`
**Date**: 2024-10-31
**Deployment Status**: Ready for Production

---

## Pre-Deployment Verification ✅

### Database Schema
- ✅ **Database verified** - No migrations required
  - `tigu_order.shipping_type` exists
  - `tigu_order.driver_receive_time` exists
  - `tigu_order.arrive_warehouse_time` exists
  - `tigu_order.warehouse_shipping_time` exists
  - `tigu_order_action` table exists with all fields
  - `tigu_uploaded_files.biz_id` exists

### Code Quality
- ✅ **Unit tests pass** - 17/17 tests passed
- ✅ **Code review** - Self-reviewed, well-documented
- ✅ **Documentation** - Complete implementation plan, test guides, workflow documentation

### Backend Changes
- ✅ **Models**: OrderAction model, timestamp fields added
- ✅ **Services**: order_action_service.py created, workflow functions added
- ✅ **Routes**: Dual workflow endpoints implemented
- ✅ **Schemas**: PickupRequest/Response, updated OrderDetail

### Frontend Changes
- ✅ **Types**: Updated interfaces with new fields
- ✅ **Store**: New actions for workflow steps
- ✅ **Components**: PhotoUploadModal, updated OrderCard/OrderDetail

### Testing
- ✅ **Unit Tests**: 17 tests covering core functionality
- ✅ **Integration Guide**: Comprehensive API testing documentation
- ✅ **Test Summary**: Complete coverage documentation

---

## Deployment Steps

### Step 1: Merge Feature Branch ✅

```bash
# Switch to main branch
git checkout main

# Pull latest changes
git pull origin main

# Merge feature branch
git merge feature/updated-workflow --no-ff

# Push to remote
git push origin main
```

### Step 2: Backend Deployment

**Option A: Docker Deployment** (Recommended)
```bash
cd /home/mli/tigub2b/tigub2b_delivery/bff

# Build Docker image
docker-compose build bff

# Restart service
docker-compose restart bff

# Verify
docker-compose ps
docker-compose logs bff --tail=50
```

**Option B: Direct Deployment**
```bash
cd /home/mli/tigub2b/tigub2b_delivery/bff

# Pull latest code
git pull origin main

# Activate virtual environment
source .venv/bin/activate

# Install/update dependencies (if any)
pip install -r requirements.txt

# Restart service
sudo systemctl restart tigub2b-bff
# OR
pkill -f "uvicorn app.main:app"
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 &

# Verify
curl http://localhost:8000/docs
```

### Step 3: Frontend Deployment

**Option A: Docker/Nginx Deployment**
```bash
cd /home/mli/tigub2b/tigub2b_delivery/frontend

# Build production bundle
npm run build

# Copy to nginx
sudo cp -r dist/* /var/www/delivery.wetigu.com/

# Restart nginx
sudo systemctl restart nginx
```

**Option B: Docker Compose**
```bash
cd /home/mli/tigub2b/tigub2b_delivery

# Build frontend image
docker-compose build frontend

# Restart service
docker-compose restart frontend

# Verify
docker-compose ps
```

### Step 4: Verification

**Backend Health Check**:
```bash
# Check API is running
curl http://localhost:8000/docs

# Check specific endpoint
curl http://localhost:8000/api/v1/orders/available \
  -H "Authorization: Bearer {token}"

# Check logs
tail -f /var/log/tigub2b/bff.log
# OR
docker-compose logs bff --tail=100 -f
```

**Frontend Health Check**:
```bash
# Check frontend loads
curl http://localhost:5173  # Dev
curl https://delivery.wetigu.com  # Production

# Check build
ls -lh /var/www/delivery.wetigu.com/
```

---

## Post-Deployment Validation

### Critical Path Testing

#### Test 1: Warehouse Delivery Workflow
```bash
# Get auth token
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"phone":"1234567890","code":"123456"}' \
  | jq -r '.accessToken')

# Test order SN (replace with actual)
ORDER_SN="TOD_WAREHOUSE_001"
PHOTO="data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD..."

# Step 1: Pickup (should return shippingStatus: 2)
curl -X POST "http://localhost:8000/api/v1/orders/$ORDER_SN/pickup" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"photo\":\"$PHOTO\",\"notes\":\"Test pickup\"}"

# Step 2: Arrive warehouse (should return shippingStatus: 3)
curl -X POST "http://localhost:8000/api/v1/orders/$ORDER_SN/arrive-warehouse" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"photo\":\"$PHOTO\",\"notes\":\"Test arrive\"}"

# Step 3: Warehouse ship (should return shippingStatus: 4)
curl -X POST "http://localhost:8000/api/v1/orders/$ORDER_SN/warehouse-ship" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"photo\":\"$PHOTO\",\"notes\":\"Test ship\"}"

# Step 4: Complete delivery (should return status: "uploaded")
curl -X POST "http://localhost:8000/api/v1/orders/$ORDER_SN/proof" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"photo\":\"$PHOTO\",\"notes\":\"Test complete\"}"
```

#### Test 2: Direct Delivery Workflow
```bash
ORDER_SN="TOD_DIRECT_001"

# Step 1: Pickup (should return shippingStatus: 4)
curl -X POST "http://localhost:8000/api/v1/orders/$ORDER_SN/pickup" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"photo\":\"$PHOTO\",\"notes\":\"Test direct pickup\"}"

# Step 2: Complete delivery (should return status: "uploaded")
curl -X POST "http://localhost:8000/api/v1/orders/$ORDER_SN/proof" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"photo\":\"$PHOTO\",\"notes\":\"Test direct complete\"}"
```

### Database Validation
```sql
-- Check order status updates
SELECT order_sn, shipping_type, shipping_status, order_status,
       driver_receive_time, arrive_warehouse_time,
       warehouse_shipping_time, finish_time
FROM tigu_order
WHERE order_sn IN ('TOD_WAREHOUSE_001', 'TOD_DIRECT_001');

-- Check audit trail
SELECT oa.id, o.order_sn, oa.action_type, oa.shipping_status,
       oa.logistics_voucher_file, oa.create_time, oa.remark
FROM tigu_order_action oa
JOIN tigu_order o ON oa.order_id = o.id
WHERE o.order_sn IN ('TOD_WAREHOUSE_001', 'TOD_DIRECT_001')
ORDER BY oa.create_time ASC;

-- Check file linking
SELECT uf.id, uf.file_url, uf.biz_id, uf.biz_type
FROM tigu_uploaded_files uf
WHERE uf.biz_type = 'order_action'
  AND uf.biz_id IN (
    SELECT oa.id FROM tigu_order_action oa
    JOIN tigu_order o ON oa.order_id = o.id
    WHERE o.order_sn IN ('TOD_WAREHOUSE_001', 'TOD_DIRECT_001')
  );
```

### Frontend Validation (Manual)
- [ ] Login as driver
- [ ] View available orders
- [ ] Verify delivery type badges show correctly
- [ ] Pickup order with photo upload
- [ ] Verify status changes immediately
- [ ] Test warehouse workflow buttons (if applicable)
- [ ] Test direct workflow button (if applicable)
- [ ] Verify timeline shows progress
- [ ] Complete delivery with photo
- [ ] Verify redirect to task board
- [ ] Check order appears in completed tab

---

## Monitoring

### Log Locations
```bash
# Backend logs
tail -f /var/log/tigub2b/bff.log
docker-compose logs bff -f

# Frontend logs
tail -f /var/log/nginx/delivery.wetigu.com.access.log
tail -f /var/log/nginx/delivery.wetigu.com.error.log

# Database queries
sudo tail -f /var/log/mysql/mysql.log | grep tigu_order
```

### Key Metrics to Monitor
- [ ] API response times (< 500ms expected)
- [ ] Photo upload success rate
- [ ] Order status transition errors
- [ ] Database deadlocks or timeouts
- [ ] Frontend JavaScript errors (check browser console)
- [ ] Photo file storage growth

### Error Patterns to Watch
```bash
# Backend errors
grep -i "error\|exception\|failed" /var/log/tigub2b/bff.log

# Photo upload failures
grep -i "photo\|upload\|file" /var/log/tigub2b/bff.log | grep -i error

# Status transition errors
grep -i "shipping_status\|order_status" /var/log/tigub2b/bff.log | grep -i error
```

---

## Rollback Plan

If critical issues occur:

### Quick Rollback
```bash
# Backend
git checkout main
git revert HEAD~7..HEAD  # Revert last 7 commits
git push origin main
docker-compose restart bff

# Frontend
git checkout main
git revert HEAD~3..HEAD  # Revert frontend commits
npm run build
sudo cp -r dist/* /var/www/delivery.wetigu.com/
```

### Database Rollback
No database changes were made, so no rollback needed for schema.

### Cache Clear (if needed)
```bash
# Clear Redis cache
redis-cli FLUSHDB

# Restart services
docker-compose restart
```

---

## Success Criteria

✅ **All must pass before considering deployment successful**:

1. Backend
   - [ ] API returns 200 for health check
   - [ ] All endpoints respond correctly
   - [ ] No errors in logs for 1 hour

2. Workflows
   - [ ] Warehouse delivery completes successfully
   - [ ] Direct delivery completes successfully
   - [ ] Audit trail records created correctly
   - [ ] Photos uploaded and linked

3. Frontend
   - [ ] Application loads without errors
   - [ ] Photo upload modal works
   - [ ] Status updates display correctly
   - [ ] Timeline shows progress

4. Database
   - [ ] Order status updates correctly
   - [ ] Timestamps recorded accurately
   - [ ] File linking via biz_id works
   - [ ] No orphaned records

5. Performance
   - [ ] API response time < 500ms
   - [ ] Photo upload < 2s
   - [ ] No memory leaks
   - [ ] No database connection issues

---

## Deployment Sign-off

**Deployed By**: _______________
**Date**: _______________
**Time**: _______________
**Verification Status**: _______________
**Issues Found**: _______________
**Notes**: _______________

---

## Additional Resources

- Implementation Plan: `/IMPLEMENTATION_PLAN.md`
- Workflow Guide: `/DRIVER_WORKFLOW_GUIDE_UPDATED.md`
- Test Summary: `/bff/tests/TEST_SUMMARY.md`
- API Testing Guide: `/bff/tests/integration/API_TESTING_GUIDE.md`
- Unit Tests: `/bff/tests/unit/`

---

**Status**: ✅ Ready for Deployment
**Risk Level**: Low (no database migrations, backward compatible)
**Estimated Downtime**: 0 minutes (rolling deployment)
