# Delivery Frontend (Vue.js)

## Tech Stack
- Vue 3 + Vite + TypeScript for SPA experience on tablets/phones
- Pinia for state management (driver/session/order queues)
- Vue Router with guarded routes per driver role
- Axios for BFF access with auth interceptors
- Google Maps JavaScript API + Directions/Distance Matrix services

## Core Screens
- **Authentication**: driver login with phone + OTP, token refresh background
- **Task Board**: segmented tabs for `Pending Pickup`, `In Transit`, `Completed`, filtered via order status/shipping status
- **Route Planner**: map view with optimized sequence, live traffic overlays
- **Order Detail**: item list, receiver contact, pickup/drop geolocation, scan SKU via device camera
- **Proof of Delivery**: capture signature/photo, damage notes, offline cache until sync
- **Returns & Exceptions**: start return workflow, flag failed delivery reasons (uses dicts `order_shipping_status`, `order_status`)

## State & Data Flow
- Global store keeps `activeOrders`, `completedOrders`, `driverProfile`
- BFF responses normalized by `order_id` referencing tables `tigu_order` & `tigu_order_item`
- Background sync task polls `/orders/assigned` every 60s (adaptive)
- Websocket channel for immediate reassignments, new rush tasks

## Directory Blueprint
```
frontend/
  src/
    api/       # Axios clients & typing
    components/
    composables/
    features/
      assignments/
      navigation/
      proof/
    router/
    store/
    styles/
    views/
  public/
```

## Developer Commands
- `npm install`
- `npm run dev` – local dev with Vite proxying to BFF (`/api`)
- `npm run build`
- `npm run test:unit` (Vitest)
- `npm run lint`

## Integration Notes
- Use `.env.local` for `VITE_API_URL`, `VITE_GOOGLE_MAPS_KEY`
- Handle `shipping_type` codes: `0=Express`, `1=Pickup`, `2=Local Delivery`
- Display `order_status` labels using `sys_dict_data` JSON fields
- Map warehouses using `tigu_warehouse` longitude/latitude if present
