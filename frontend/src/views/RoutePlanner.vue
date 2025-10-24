<template>
  <section class="planner">
    <header class="planner__header">
      <div class="planner__header-content">
        <button class="planner__back-btn" @click="goBack">
          ← {{ $t('routePlanner.backToTasks') }}
        </button>
        <div>
          <h2>{{ $t('routePlanner.title') }}</h2>
          <p>{{ $t('routePlanner.description') }}</p>
        </div>
      </div>
      <button class="planner__refresh" @click="fetchRoute">
        {{ $t('routePlanner.refreshPlan') }}
      </button>
    </header>

    <div class="planner__content">
      <!-- Open Full Route Button -->
      <div v-if="route?.stops && route.stops.length > 0" class="planner__map-actions">
        <button class="planner__maps-btn planner__maps-btn--primary" @click="openFullRouteInMaps">
          <span class="planner__maps-icon">🗺️</span>
          {{ $t('routePlanner.openFullRoute') }}
        </button>
        <p class="planner__maps-hint">{{ $t('routePlanner.mapsHint') }}</p>
      </div>

      <!-- Stops List -->
      <div class="planner__stops">
        <h3>{{ $t('routePlanner.stops') }} ({{ route?.stops?.length ?? 0 }})</h3>
        <div class="planner__stops-list">
          <div v-for="stop in route?.stops ?? []" :key="stop.orderSn" class="planner__stop">
            <div class="planner__stop-header">
              <span class="planner__stop-number">{{ stop.sequence }}</span>
              <div class="planner__stop-info">
                <strong class="planner__stop-name">{{ stop.receiverName }}</strong>
                <p class="planner__stop-address">{{ stop.address }}</p>
                <small v-if="stop.eta" class="planner__stop-eta"
                  >{{ $t('routePlanner.eta') }}: {{ stop.eta }}</small
                >
              </div>
            </div>
            <div class="planner__stop-actions">
              <button
                class="planner__stop-btn planner__stop-btn--navigate"
                @click="navigateToStop(stop)"
              >
                <span>📍</span> {{ $t('routePlanner.navigate') }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useOrdersStore } from '@/store/orders';

interface RouteStop {
  orderSn: string;
  sequence: number;
  address: string;
  receiverName: string;
  eta?: string;
}

const router = useRouter();
const ordersStore = useOrdersStore();

onMounted(() => {
  fetchRoute();
});

const route = computed(() => ordersStore.routePlan);

function fetchRoute() {
  ordersStore.fetchRoutePlan();
}

function goBack() {
  router.push('/');
}

function encodeAddress(address: string): string {
  return encodeURIComponent(address);
}

function openFullRouteInMaps() {
  const stops = route.value?.stops ?? [];
  if (stops.length === 0) return;

  if (stops.length === 1) {
    // Single stop - just navigate to it
    const destination = encodeAddress(stops[0].address);
    window.open(`https://www.google.com/maps/dir/?api=1&destination=${destination}`, '_blank');
    return;
  }

  // Multiple stops - create route with waypoints
  const origin = encodeAddress(stops[0].address);
  const destination = encodeAddress(stops[stops.length - 1].address);

  // Middle stops as waypoints (skip first and last)
  const waypoints = stops
    .slice(1, -1)
    .map((stop) => encodeAddress(stop.address))
    .join('|');

  let url = `https://www.google.com/maps/dir/?api=1&origin=${origin}&destination=${destination}`;
  if (waypoints) {
    url += `&waypoints=${waypoints}`;
  }
  url += '&travelmode=driving';

  window.open(url, '_blank');
}

function navigateToStop(stop: RouteStop) {
  const destination = encodeAddress(stop.address);
  window.open(
    `https://www.google.com/maps/dir/?api=1&destination=${destination}&travelmode=driving`,
    '_blank'
  );
}
</script>

<style scoped>
.planner {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.planner__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #ffffff;
  padding: 16px 20px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.08);
}

.planner__header-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.planner__back-btn {
  background: #f1f5f9;
  color: #475569;
  border: 1px solid #e2e8f0;
  padding: 8px 12px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 4px;
}

.planner__back-btn:hover {
  background: #e2e8f0;
  color: #334155;
}

.planner__refresh {
  background: #2563eb;
  color: #ffffff;
  border: none;
  padding: 10px 16px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.planner__refresh:hover {
  background: #1d4ed8;
}

.planner__content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* Map Actions Section */
.planner__map-actions {
  background: #ffffff;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.08);
  text-align: center;
}

.planner__maps-btn {
  background: #10b981;
  color: #ffffff;
  border: none;
  padding: 14px 24px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 16px;
  font-weight: 600;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.planner__maps-btn:hover {
  background: #059669;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
}

.planner__maps-icon {
  font-size: 20px;
}

.planner__maps-hint {
  margin: 12px 0 0;
  color: #64748b;
  font-size: 14px;
}

/* Stops Section */
.planner__stops {
  background: #ffffff;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.08);
}

.planner__stops h3 {
  margin: 0 0 16px;
  color: #1e293b;
  font-size: 18px;
}

.planner__stops-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.planner__stop {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 16px;
  transition: all 0.2s ease;
}

.planner__stop:hover {
  border-color: #cbd5e1;
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.06);
}

.planner__stop-header {
  display: flex;
  gap: 12px;
  margin-bottom: 12px;
}

.planner__stop-number {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  background: #2563eb;
  color: #ffffff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 14px;
}

.planner__stop-info {
  flex: 1;
  min-width: 0;
}

.planner__stop-name {
  display: block;
  color: #1e293b;
  font-size: 16px;
  margin-bottom: 4px;
}

.planner__stop-address {
  margin: 0 0 4px;
  color: #64748b;
  font-size: 14px;
  line-height: 1.5;
}

.planner__stop-eta {
  color: #94a3b8;
  font-size: 13px;
}

.planner__stop-actions {
  display: flex;
  gap: 8px;
}

.planner__stop-btn {
  flex: 1;
  border: none;
  padding: 10px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.planner__stop-btn--navigate {
  background: #3b82f6;
  color: #ffffff;
}

.planner__stop-btn--navigate:hover {
  background: #2563eb;
  transform: translateY(-1px);
}

/* Responsive styles */
@media (max-width: 768px) {
  .planner__header-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .planner__header {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }

  .planner__refresh {
    align-self: stretch;
    text-align: center;
  }

  .planner__maps-btn {
    width: 100%;
    justify-content: center;
  }

  .planner__stop-header {
    flex-direction: column;
    gap: 8px;
  }

  .planner__stop-actions {
    flex-direction: column;
  }
}
</style>
