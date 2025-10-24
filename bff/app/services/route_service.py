import hashlib
from typing import List

from app.schemas.order import OrderSummary
from app.schemas.route import RoutePlan, RouteStop


async def build_route_plan(orders: List[OrderSummary]) -> RoutePlan:
    """Build a simple route plan from orders. No external API calls needed."""
    stops: List[RouteStop] = []

    # Create stops from orders in sequence
    for idx, order in enumerate(orders, start=1):
        stops.append(
            RouteStop(
                order_sn=order.order_sn,
                sequence=idx,
                address=order.receiver_address,
                receiver_name=order.receiver_name,
                eta=None,  # ETA will be provided by Google Maps when user opens the route
                latitude=order.pickup_location.latitude if order.pickup_location else None,
                longitude=order.pickup_location.longitude if order.pickup_location else None
            )
        )

    # Generate unique plan ID based on order sequence
    plan_id = hashlib.md5("".join(stop.order_sn for stop in stops).encode()).hexdigest()
    return RoutePlan(id=plan_id, stops=stops)
