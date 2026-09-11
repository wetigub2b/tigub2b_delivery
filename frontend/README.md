# Delivery Frontend (Vue.js)

## Tech Stack
- Vue 3 + Vite + TypeScript for SPA experience on tablets/phones
- Pinia for state management (driver/session/order queues, notifications)
- Vue Router with guarded routes per driver role
- Axios for BFF access with auth interceptors
- Mapbox GL for driver map (`MapTab`, `AddressMapModal`); Google Maps JS API for route panels

## Core Screens
- **Authentication**: driver login with phone + OTP, token refresh background
- **Task Board**: segmented tabs for `Pending Pickup`, `In Transit`, `Completed`, filtered via order status/shipping status
- **Map Tab**: pickup pins from `GET /marks`; driver `🚗` pin from browser/Capacitor GPS
- **Route Planner**: map view with optimized sequence, live traffic overlays
- **Order Detail**: item list, receiver contact, pickup/drop geolocation, scan SKU via device camera
- **Proof of Delivery**: capture signature/photo, damage notes, offline cache until sync
- **Notifications**: bell icon with unread badge, backed by BFF (`/notifications/mine`, 30s polling) — no Supabase

## GPS / Location Behavior (`MapTab.vue`, `utils/mobile.ts`)
- High-accuracy GPS first (`20s` timeout), coarse fallback, then IP fallback (desktop)
- Fixes worse than `±100m` don't auto-center the map
- IP fallback (`±10km`, e.g. wrong city on VPN) is never shown as the driver pin — map falls back to Toronto-area view
- Desktop browsers often lack a GPS/WiFi provider: use Chrome + Location allowed + WiFi on + VPN off; mobile GPS is authoritative

## State & Data Flow
- Global store keeps `activeOrders`, `completedOrders`, `driverProfile`
- BFF responses normalized by `order_id` referencing tables `tigu_order` & `tigu_order_item`
- Background sync task polls `/orders/assigned` every 60s (adaptive)
- Notifications polled from BFF every 30s (`useNotificationStore`)

## Directory Blueprint
```
frontend/
  src/
    api/       # Axios clients & typing
    components/
    composables/
    lib/
      notifications.ts  # Notification types (local, no Supabase)
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
- Use `.env.local` for `VITE_API_URL`, `VITE_GOOGLE_MAPS_KEY`, `VITE_MAPBOX_TOKEN`
- Handle `shipping_type` codes: `0=Express`, `1=Pickup`, `2=Local Delivery`
- Display `order_status` labels using status helpers
- Map warehouses using `tigu_warehouse` longitude/latitude if present
