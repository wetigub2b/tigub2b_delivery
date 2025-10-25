from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin, get_current_super_admin, get_db_session
from app.core.security import get_password_hash
from app.models.driver import Driver
from app.models.driver_performance import DriverAlert, DriverPerformance as DriverPerformanceModel, DriverPerformanceLog
from app.models.order import Order
from app.models.user import User
from app.schemas.admin import (
    AdminDashboardStats,
    AlertActionRequest,
    BulkActionRequest,
    DriverAlertResponse,
    DriverAssignment,
    DriverCreate,
    DriverPerformance,
    DriverPerformanceLogEntry,
    DriverPerformanceMetrics,
    DriverResponse,
    DriverUpdate,
    OrderDispatch,
    PerformanceAnalyticsRequest,
    PerformanceComparisonResponse
)

router = APIRouter()


@router.get("/dashboard", response_model=AdminDashboardStats)
async def get_dashboard_stats(
    session: AsyncSession = Depends(get_db_session),
    current_admin: User = Depends(get_current_admin)
) -> AdminDashboardStats:
    """Get admin dashboard statistics"""

    # Get driver statistics from tigu_driver table
    total_drivers_result = await session.execute(
        select(func.count(Driver.id))
    )
    total_drivers = total_drivers_result.scalar() or 0

    active_drivers_result = await session.execute(
        select(func.count(Driver.id)).where(Driver.status == 1)
    )
    active_drivers = active_drivers_result.scalar() or 0

    # Get order statistics
    total_orders_result = await session.execute(select(func.count(Order.order_sn)))
    total_orders = total_orders_result.scalar() or 0

    pending_orders_result = await session.execute(
        select(func.count(Order.order_sn)).where(Order.shipping_status == 0)
    )
    pending_orders = pending_orders_result.scalar() or 0

    in_transit_orders_result = await session.execute(
        select(func.count(Order.order_sn)).where(Order.shipping_status.in_([1, 2]))
    )
    in_transit_orders = in_transit_orders_result.scalar() or 0

    completed_orders_result = await session.execute(
        select(func.count(Order.order_sn)).where(Order.shipping_status == 3)
    )
    completed_orders = completed_orders_result.scalar() or 0

    completion_rate = (completed_orders / total_orders * 100) if total_orders > 0 else 0

    return AdminDashboardStats(
        total_drivers=total_drivers,
        active_drivers=active_drivers,
        total_orders=total_orders,
        pending_orders=pending_orders,
        in_transit_orders=in_transit_orders,
        completed_orders=completed_orders,
        completion_rate=completion_rate
    )


@router.get("/drivers", response_model=List[DriverResponse])
async def get_all_drivers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None, description="Search by name, phone, or vehicle plate"),
    status: Optional[int] = Query(None, description="Filter by status (1=active, 0=inactive)"),
    session: AsyncSession = Depends(get_db_session),
    current_admin: User = Depends(get_current_admin)
) -> List[DriverResponse]:
    """Get list of all drivers with pagination and filtering (with optional user account info)"""

    # LEFT JOIN with sys_user to get login info when available
    query = select(Driver, User).outerjoin(
        User, Driver.phone == User.phonenumber
    )

    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            (Driver.name.ilike(search_pattern)) |
            (Driver.phone.ilike(search_pattern)) |
            (Driver.vehicle_plate.ilike(search_pattern))
        )

    if status is not None:
        query = query.where(Driver.status == status)

    query = query.order_by(desc(Driver.created_at)).offset(skip).limit(limit)

    result = await session.execute(query)
    driver_user_pairs = result.all()

    # Build response with hybrid data
    response = []
    for driver, user in driver_user_pairs:
        driver_data = DriverResponse.model_validate(driver)
        # Add mapped fields for frontend compatibility
        driver_data.user_id = user.user_id if user else driver.id
        driver_data.user_name = user.user_name if user else driver.name
        driver_data.nick_name = user.nick_name if user else driver.name
        driver_data.phonenumber = driver.phone
        driver_data.license_plate = driver.vehicle_plate
        driver_data.role = user.effective_role if user else "driver"
        driver_data.last_login = user.login_date if user else None
        response.append(driver_data)

    return response


@router.get("/drivers/{driver_id}", response_model=DriverResponse)
async def get_driver(
    driver_id: int,
    session: AsyncSession = Depends(get_db_session),
    current_admin: User = Depends(get_current_admin)
) -> DriverResponse:
    """Get specific driver details (with optional user account info)"""

    # LEFT JOIN with sys_user to get login info when available
    result = await session.execute(
        select(Driver, User).outerjoin(
            User, Driver.phone == User.phonenumber
        ).where(Driver.id == driver_id)
    )
    driver_user_pair = result.first()

    if not driver_user_pair:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")

    driver, user = driver_user_pair
    driver_data = DriverResponse.model_validate(driver)
    # Add mapped fields for frontend compatibility
    driver_data.user_id = user.user_id if user else driver.id
    driver_data.user_name = user.user_name if user else driver.name
    driver_data.nick_name = user.nick_name if user else driver.name
    driver_data.phonenumber = driver.phone
    driver_data.license_plate = driver.vehicle_plate
    driver_data.role = user.effective_role if user else "driver"
    driver_data.last_login = user.login_date if user else None

    return driver_data


@router.post("/drivers", response_model=DriverResponse)
async def create_driver(
    driver_data: DriverCreate,
    session: AsyncSession = Depends(get_db_session),
    current_admin: User = Depends(get_current_admin)
) -> DriverResponse:
    """Create a new driver"""

    # Check if phone number already exists
    existing_driver = await session.execute(
        select(Driver).where(Driver.phone == driver_data.phone)
    )
    if existing_driver.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number already exists"
        )

    # Create new driver
    new_driver = Driver(
        name=driver_data.name,
        phone=driver_data.phone,
        email=driver_data.email,
        license_number=driver_data.license_number,
        vehicle_type=driver_data.vehicle_type,
        vehicle_plate=driver_data.vehicle_plate,
        vehicle_model=driver_data.vehicle_model,
        notes=driver_data.notes,
        status=1,  # Active by default
        rating=Decimal("5.00"),
        total_deliveries=0
    )

    session.add(new_driver)
    await session.commit()
    await session.refresh(new_driver)

    # Map fields for frontend compatibility
    driver_data = DriverResponse.model_validate(new_driver)
    driver_data.user_id = new_driver.id
    driver_data.user_name = new_driver.name
    driver_data.nick_name = new_driver.name
    driver_data.phonenumber = new_driver.phone
    driver_data.license_plate = new_driver.vehicle_plate
    driver_data.role = "driver"
    driver_data.last_login = None

    return driver_data


@router.put("/drivers/{driver_id}", response_model=DriverResponse)
async def update_driver(
    driver_id: int,
    driver_data: DriverUpdate,
    session: AsyncSession = Depends(get_db_session),
    current_admin: User = Depends(get_current_admin)
) -> DriverResponse:
    """Update driver information"""

    result = await session.execute(
        select(Driver).where(Driver.id == driver_id)
    )
    driver = result.scalars().first()

    if not driver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")

    # Update only provided fields
    update_data = driver_data.dict(exclude_unset=True)
    if update_data:
        await session.execute(
            update(Driver).where(Driver.id == driver_id).values(**update_data)
        )
        await session.commit()
        await session.refresh(driver)

    # Map fields for frontend compatibility (check if sys_user account exists)
    result = await session.execute(
        select(User).where(User.phonenumber == driver.phone)
    )
    user = result.scalars().first()

    response_data = DriverResponse.model_validate(driver)
    response_data.user_id = user.user_id if user else driver.id
    response_data.user_name = user.user_name if user else driver.name
    response_data.nick_name = user.nick_name if user else driver.name
    response_data.phonenumber = driver.phone
    response_data.license_plate = driver.vehicle_plate
    response_data.role = user.effective_role if user else "driver"
    response_data.last_login = user.login_date if user else None

    return response_data


@router.delete("/drivers/{driver_id}")
async def delete_driver(
    driver_id: int,
    session: AsyncSession = Depends(get_db_session),
    current_admin: User = Depends(get_current_admin)
) -> dict:
    """Delete a driver"""

    result = await session.execute(
        select(Driver).where(Driver.id == driver_id)
    )
    driver = result.scalars().first()

    if not driver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")

    # Hard delete (tigu_driver doesn't have soft delete)
    await session.delete(driver)
    await session.commit()

    return {"message": "Driver deleted successfully"}


@router.post("/drivers/{driver_id}/activate")
async def activate_driver(
    driver_id: int,
    session: AsyncSession = Depends(get_db_session),
    current_admin: User = Depends(get_current_admin)
) -> dict:
    """Activate a driver"""

    await session.execute(
        update(Driver).where(Driver.id == driver_id).values(status=1)
    )
    await session.commit()

    return {"message": "Driver activated successfully"}


@router.post("/drivers/{driver_id}/deactivate")
async def deactivate_driver(
    driver_id: int,
    session: AsyncSession = Depends(get_db_session),
    current_admin: User = Depends(get_current_admin)
) -> dict:
    """Deactivate a driver"""

    await session.execute(
        update(Driver).where(Driver.id == driver_id).values(status=0)
    )
    await session.commit()

    return {"message": "Driver deactivated successfully"}


@router.get("/drivers/{driver_id}/performance", response_model=DriverPerformance)
async def get_driver_performance(
    driver_id: int,
    session: AsyncSession = Depends(get_db_session),
    current_admin: User = Depends(get_current_admin)
) -> DriverPerformance:
    """Get driver performance metrics"""

    # Get total orders assigned to driver
    total_orders_result = await session.execute(
        select(func.count(Order.order_sn)).where(Order.driver_id == driver_id)
    )
    total_orders = total_orders_result.scalar() or 0

    # Get completed orders
    completed_orders_result = await session.execute(
        select(func.count(Order.order_sn)).where(
            Order.driver_id == driver_id,
            Order.shipping_status == 3
        )
    )
    completed_orders = completed_orders_result.scalar() or 0

    completion_rate = (completed_orders / total_orders * 100) if total_orders > 0 else 0

    # Get last delivery
    last_delivery_result = await session.execute(
        select(Order.updated_time).where(
            Order.driver_id == driver_id,
            Order.shipping_status == 3
        ).order_by(desc(Order.updated_time)).limit(1)
    )
    last_delivery = last_delivery_result.scalar()

    return DriverPerformance(
        driver_id=driver_id,
        total_orders=total_orders,
        completed_orders=completed_orders,
        completion_rate=completion_rate,
        last_delivery=last_delivery
    )


@router.post("/drivers/bulk-action")
async def bulk_driver_action(
    action_data: BulkActionRequest,
    session: AsyncSession = Depends(get_db_session),
    current_admin: User = Depends(get_current_admin)
) -> dict:
    """Perform bulk actions on multiple drivers"""

    if action_data.action == "activate":
        await session.execute(
            update(Driver).where(Driver.id.in_(action_data.driver_ids)).values(status=1)
        )
    elif action_data.action == "deactivate":
        await session.execute(
            update(Driver).where(Driver.id.in_(action_data.driver_ids)).values(status=0)
        )
    elif action_data.action == "delete":
        # Hard delete for tigu_driver
        await session.execute(
            select(Driver).where(Driver.id.in_(action_data.driver_ids))
        )
        for driver_id in action_data.driver_ids:
            result = await session.execute(
                select(Driver).where(Driver.id == driver_id)
            )
            driver = result.scalars().first()
            if driver:
                await session.delete(driver)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid action"
        )

    await session.commit()

    return {"message": f"Bulk {action_data.action} completed for {len(action_data.driver_ids)} drivers"}


@router.post("/orders/{order_sn}/assign")
async def assign_order_to_driver(
    order_sn: str,
    assignment: DriverAssignment,
    session: AsyncSession = Depends(get_db_session),
    current_admin: User = Depends(get_current_admin)
) -> dict:
    """Manually assign order to a specific driver"""

    # Check if order exists
    order_result = await session.execute(
        select(Order).where(Order.order_sn == order_sn)
    )
    order = order_result.scalars().first()

    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    # Check if driver exists and is active
    driver_result = await session.execute(
        select(Driver).where(
            Driver.id == assignment.driver_id,
            Driver.status == 1
        )
    )
    driver = driver_result.scalars().first()

    if not driver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active driver not found")

    # Assign order to driver
    await session.execute(
        update(Order).where(Order.order_sn == order_sn).values(
            driver_id=assignment.driver_id,
            updated_time=datetime.now()
        )
    )
    await session.commit()

    return {"message": f"Order {order_sn} assigned to driver {driver.name}"}


@router.post("/orders/dispatch")
async def dispatch_orders(
    dispatch_data: List[OrderDispatch],
    session: AsyncSession = Depends(get_db_session),
    current_admin: User = Depends(get_current_admin)
) -> dict:
    """Bulk dispatch orders to drivers"""

    dispatched_count = 0

    for dispatch in dispatch_data:
        # Check if order exists and is available for dispatch
        order_result = await session.execute(
            select(Order).where(
                Order.order_sn == dispatch.order_sn,
                Order.shipping_status == 0  # Only dispatch pending orders
            )
        )
        order = order_result.scalars().first()

        if not order:
            continue

        # Check if driver exists and is active
        driver_result = await session.execute(
            select(Driver).where(
                Driver.id == dispatch.driver_id,
                Driver.status == 1
            )
        )
        driver = driver_result.scalars().first()

        if not driver:
            continue

        # Assign order to driver
        await session.execute(
            update(Order).where(Order.order_sn == dispatch.order_sn).values(
                driver_id=dispatch.driver_id,
                shipping_status=1,  # Mark as shipped/assigned
                updated_time=datetime.now()
            )
        )
        dispatched_count += 1

    await session.commit()

    return {"message": f"Successfully dispatched {dispatched_count} orders"}


# Performance monitoring endpoints

@router.get("/performance/drivers", response_model=List[DriverPerformanceMetrics])
async def get_drivers_performance(
    start_date: datetime = Query(..., description="Start date for performance period"),
    end_date: datetime = Query(..., description="End date for performance period"),
    driver_ids: Optional[List[int]] = Query(None, description="Specific driver IDs to analyze"),
    session: AsyncSession = Depends(get_db_session),
    current_admin: User = Depends(get_current_admin)
) -> List[DriverPerformanceMetrics]:
    """Get performance metrics for drivers within a time period"""

    # Base query for performance data
    query = select(DriverPerformanceModel, Driver.name).join(
        Driver, DriverPerformanceModel.driver_id == Driver.id
    ).where(
        and_(
            DriverPerformanceModel.period_start >= start_date,
            DriverPerformanceModel.period_end <= end_date
        )
    )

    if driver_ids:
        query = query.where(DriverPerformanceModel.driver_id.in_(driver_ids))

    result = await session.execute(query)
    performance_data = result.all()

    performance_metrics = []
    for perf, driver_name in performance_data:
        success_rate = (perf.successful_deliveries / perf.total_deliveries * 100) if perf.total_deliveries > 0 else 0

        performance_metrics.append(DriverPerformanceMetrics(
            driver_id=perf.driver_id,
            driver_name=driver_name,
            period_start=perf.period_start,
            period_end=perf.period_end,
            total_deliveries=perf.total_deliveries,
            successful_deliveries=perf.successful_deliveries,
            failed_deliveries=perf.failed_deliveries,
            success_rate=success_rate,
            avg_delivery_time=perf.avg_delivery_time,
            total_active_time=perf.total_active_time,
            total_distance=perf.total_distance,
            orders_per_hour=perf.orders_per_hour,
            fuel_efficiency=perf.fuel_efficiency,
            customer_rating=perf.customer_rating,
            on_time_percentage=perf.on_time_percentage
        ))

    return performance_metrics


@router.get("/performance/drivers/{driver_id}/logs", response_model=List[DriverPerformanceLogEntry])
async def get_driver_performance_logs(
    driver_id: int,
    start_date: Optional[datetime] = Query(None, description="Start date for logs"),
    end_date: Optional[datetime] = Query(None, description="End date for logs"),
    action_type: Optional[str] = Query(None, description="Filter by action type"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    session: AsyncSession = Depends(get_db_session),
    current_admin: User = Depends(get_current_admin)
) -> List[DriverPerformanceLogEntry]:
    """Get detailed performance logs for a specific driver"""

    query = select(DriverPerformanceLog).where(DriverPerformanceLog.driver_id == driver_id)

    if start_date:
        query = query.where(DriverPerformanceLog.action_timestamp >= start_date)

    if end_date:
        query = query.where(DriverPerformanceLog.action_timestamp <= end_date)

    if action_type:
        query = query.where(DriverPerformanceLog.action_type == action_type)

    query = query.order_by(desc(DriverPerformanceLog.action_timestamp)).offset(skip).limit(limit)

    result = await session.execute(query)
    logs = result.scalars().all()

    return [DriverPerformanceLogEntry.model_validate(log) for log in logs]


@router.get("/performance/alerts", response_model=List[DriverAlertResponse])
async def get_performance_alerts(
    status: Optional[str] = Query(None, description="Filter by alert status"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    driver_id: Optional[int] = Query(None, description="Filter by driver ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    session: AsyncSession = Depends(get_db_session),
    current_admin: User = Depends(get_current_admin)
) -> List[DriverAlertResponse]:
    """Get performance alerts with filtering options"""

    query = select(DriverAlert, Driver.name).join(
        Driver, DriverAlert.driver_id == Driver.id
    )

    if status:
        query = query.where(DriverAlert.status == status)

    if severity:
        query = query.where(DriverAlert.severity == severity)

    if driver_id:
        query = query.where(DriverAlert.driver_id == driver_id)

    query = query.order_by(desc(DriverAlert.created_at)).offset(skip).limit(limit)

    result = await session.execute(query)
    alerts_data = result.all()

    alerts = []
    for alert, driver_name in alerts_data:
        alerts.append(DriverAlertResponse(
            id=alert.id,
            driver_id=alert.driver_id,
            driver_name=driver_name,
            alert_type=alert.alert_type,
            severity=alert.severity,
            title=alert.title,
            description=alert.description,
            metric_value=alert.metric_value,
            threshold_value=alert.threshold_value,
            status=alert.status,
            created_at=alert.created_at,
            acknowledged_at=alert.acknowledged_at,
            resolved_at=alert.resolved_at
        ))

    return alerts


@router.post("/performance/alerts/{alert_id}/action")
async def handle_alert_action(
    alert_id: int,
    action_request: AlertActionRequest,
    session: AsyncSession = Depends(get_db_session),
    current_admin: User = Depends(get_current_admin)
) -> dict:
    """Handle alert actions (acknowledge, resolve, dismiss)"""

    # Get the alert
    result = await session.execute(
        select(DriverAlert).where(DriverAlert.id == alert_id)
    )
    alert = result.scalars().first()

    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

    current_time = datetime.now()

    if action_request.action == "acknowledge":
        update_data = {
            "status": "acknowledged",
            "acknowledged_at": current_time,
            "updated_at": current_time
        }
    elif action_request.action == "resolve":
        update_data = {
            "status": "resolved",
            "resolved_at": current_time,
            "updated_at": current_time
        }
    elif action_request.action == "dismiss":
        update_data = {
            "status": "dismissed",
            "updated_at": current_time
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid action. Must be 'acknowledge', 'resolve', or 'dismiss'"
        )

    await session.execute(
        update(DriverAlert).where(DriverAlert.id == alert_id).values(**update_data)
    )
    await session.commit()

    return {"message": f"Alert {action_request.action}d successfully"}


@router.post("/performance/analytics", response_model=List[PerformanceComparisonResponse])
async def get_performance_analytics(
    analytics_request: PerformanceAnalyticsRequest,
    session: AsyncSession = Depends(get_db_session),
    current_admin: User = Depends(get_current_admin)
) -> List[PerformanceComparisonResponse]:
    """Get comprehensive performance analytics and comparisons"""

    # Base query for performance data
    query = select(DriverPerformanceModel, Driver.name).join(
        Driver, DriverPerformanceModel.driver_id == Driver.id
    ).where(
        and_(
            DriverPerformanceModel.period_start >= analytics_request.start_date,
            DriverPerformanceModel.period_end <= analytics_request.end_date
        )
    )

    if analytics_request.driver_ids:
        query = query.where(DriverPerformanceModel.driver_id.in_(analytics_request.driver_ids))

    result = await session.execute(query)
    performance_data = result.all()

    # Calculate metrics and rankings
    comparisons = []
    for perf, driver_name in performance_data:
        metrics = {}

        if "delivery_rate" in analytics_request.metrics:
            metrics["delivery_rate"] = (perf.successful_deliveries / perf.total_deliveries * 100) if perf.total_deliveries > 0 else 0

        if "avg_time" in analytics_request.metrics and perf.avg_delivery_time:
            metrics["avg_time"] = float(perf.avg_delivery_time)

        if "customer_rating" in analytics_request.metrics and perf.customer_rating:
            metrics["customer_rating"] = float(perf.customer_rating)

        if "on_time_percentage" in analytics_request.metrics and perf.on_time_percentage:
            metrics["on_time_percentage"] = float(perf.on_time_percentage)

        if "efficiency" in analytics_request.metrics and perf.orders_per_hour:
            metrics["efficiency"] = float(perf.orders_per_hour)

        comparisons.append(PerformanceComparisonResponse(
            driver_id=perf.driver_id,
            driver_name=driver_name,
            metrics=metrics,
            rank=0,  # Will be calculated below
            percentile=0.0  # Will be calculated below
        ))

    # Calculate rankings (simplified - would need more sophisticated ranking in production)
    for i, comparison in enumerate(sorted(comparisons, key=lambda x: sum(x.metrics.values()), reverse=True)):
        comparison.rank = i + 1
        comparison.percentile = ((len(comparisons) - i) / len(comparisons)) * 100

    return comparisons


@router.post("/performance/log")
async def log_driver_action(
    driver_id: int,
    action_type: str,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    order_id: Optional[int] = None,
    duration_minutes: Optional[float] = None,
    distance_km: Optional[float] = None,
    notes: Optional[str] = None,
    session: AsyncSession = Depends(get_db_session),
    current_admin: User = Depends(get_current_admin)
) -> dict:
    """Log a driver action for performance tracking"""

    # Verify driver exists
    driver_result = await session.execute(
        select(Driver).where(Driver.id == driver_id)
    )
    driver = driver_result.scalars().first()

    if not driver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")

    # Create performance log entry
    log_entry = DriverPerformanceLog(
        driver_id=driver_id,
        order_id=order_id,
        action_type=action_type,
        action_timestamp=datetime.now(),
        latitude=latitude,
        longitude=longitude,
        duration_minutes=duration_minutes,
        distance_km=distance_km,
        notes=notes
    )

    session.add(log_entry)
    await session.commit()

    return {"message": "Driver action logged successfully"}