import hashlib
from typing import List

import httpx

from app.core.config import get_settings
from app.schemas.order import OrderSummary
from app.schemas.route import RoutePlan, RouteStop


async def build_route_plan(orders: List[OrderSummary]) -> RoutePlan:
    """Request optimized route from Google Maps; fall back to naive ordering."""
    settings = get_settings()
    stops: List[RouteStop] = []

    if settings.google_maps_api_key and orders:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                waypoints = "|".join(order.receiver_address for order in orders)
                params = {
                    "origin": orders[0].pickup_location.address if orders[0].pickup_location else orders[0].receiver_address,
                    "destination": orders[-1].receiver_address,
                    "waypoints": waypoints,
                    "key": settings.google_maps_api_key
                }
                response = await client.get(
                    "https://maps.googleapis.com/maps/api/directions/json",
                    params=params
                )
                response.raise_for_status()
                data = response.json()
                legs = data.get("routes", [{}])[0].get("legs", [])
                for idx, (order, leg) in enumerate(zip(orders, legs), start=1):
                    eta = leg.get("duration", {}).get("text")
                    stops.append(
                        RouteStop(
                            order_sn=order.order_sn,
                            sequence=idx,
                            address=order.receiver_address,
                            receiver_name=order.receiver_name,
                            eta=eta,
                            latitude=order.pickup_location.latitude if order.pickup_location else None,
                            longitude=order.pickup_location.longitude if order.pickup_location else None
                        )
                    )
        except httpx.HTTPError:
            stops = []

    if not stops:
        for idx, order in enumerate(orders, start=1):
            stops.append(
                RouteStop(
                    order_sn=order.order_sn,
                    sequence=idx,
                    address=order.receiver_address,
                    receiver_name=order.receiver_name,
                    eta=None,
                    latitude=order.pickup_location.latitude if order.pickup_location else None,
                    longitude=order.pickup_location.longitude if order.pickup_location else None
                )
            )

    plan_id = hashlib.md5("".join(stop.order_sn for stop in stops).encode()).hexdigest()
    return RoutePlan(id=plan_id, stops=stops)
