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
                <p class="planner__stop-package-id">
                  <span class="package-id-label">{{ $t('routePlanner.packageId') }}:</span>
                  <span class="package-id-value">{{ stop.orderSn }}</span>
                </p>
                <p class="planner__stop-address">{{ stop.address }}</p>
                <small v-if="stop.eta" class="planner__stop-eta"
                  >{{ $t('routePlanner.eta') }}: {{ stop.eta }}</small
                >
              </div>
            </div>
            <div class="planner__stop-actions">
              <button
                class="planner__stop-btn planner__stop-btn--details"
                @click="openPackageDetails(stop.orderSn)"
              >
                <span>📦</span> {{ $t('routePlanner.viewPackage') }}
              </button>
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

    <!-- Package Orders Modal -->
    <PackageOrdersModal
      v-if="selectedPackageSn"
      :show="showPackageModal"
      :package-sn="selectedPackageSn"
      :order-count="0"
      @close="closePackageModal"
    />
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { useOrdersStore } from '@/store/orders';
import PackageOrdersModal from '@/components/PackageOrdersModal.vue';

interface RouteStop {
  orderSn: string;
  sequence: number;
  address: string;
  receiverName: string;
  eta?: string;
}

const router = useRouter();
const ordersStore = useOrdersStore();

// Modal state
const showPackageModal = ref(false);
const selectedPackageSn = ref<string | null>(null);

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

function openPackageDetails(packageSn: string) {
  selectedPackageSn.value = packageSn;
  showPackageModal.value = true;
}

function closePackageModal() {
  showPackageModal.value = false;
  selectedPackageSn.value = null;
}
</script>

<style scoped>
.planner {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.planner__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--color-white);
  padding: var(--spacing-lg) var(--spacing-xl);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-md);
}

.planner__header-content {
  display: flex;
  align-items: center;
  gap: var(--spacing-lg);
}

.planner__back-btn {
  background: var(--color-bg-lighter);
  color: var(--color-text-secondary);
  border: 1px solid var(--color-gray-light);
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  transition: all var(--transition-base);
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}

.planner__back-btn:hover {
  background: var(--color-gray-lighter);
  color: var(--color-text-primary);
  border-color: var(--color-gray);
}

.planner__refresh {
  background: var(--color-primary);
  color: var(--color-white);
  border: none;
  padding: var(--spacing-sm) var(--spacing-lg);
  border-radius: var(--radius-full);
  cursor: pointer;
  font-weight: var(--font-weight-semibold);
  transition: all var(--transition-base);
}

.planner__refresh:hover {
  background: var(--color-primary-dark);
}

.planner__content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

/* Map Actions Section */
.planner__map-actions {
  background: var(--color-white);
  padding: var(--spacing-xl);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-md);
  text-align: center;
}

.planner__maps-btn {
  background: var(--color-success);
  color: var(--color-white);
  border: none;
  padding: var(--spacing-md) var(--spacing-2xl);
  border-radius: var(--radius-full);
  cursor: pointer;
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  transition: all var(--transition-base);
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.planner__maps-btn:hover {
  background: #059669;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(40, 167, 69, 0.3);
}

.planner__maps-icon {
  font-size: var(--font-size-xl);
}

.planner__maps-hint {
  margin: var(--spacing-md) 0 0;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

/* Stops Section */
.planner__stops {
  background: var(--color-white);
  padding: var(--spacing-xl);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-md);
}

.planner__stops h3 {
  margin: 0 0 var(--spacing-lg);
  color: var(--color-text-primary);
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
}

.planner__stops-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.planner__stop {
  border: 1px solid var(--color-gray-light);
  border-radius: var(--radius-sm);
  padding: var(--spacing-lg);
  transition: all var(--transition-base);
}

.planner__stop:hover {
  border-color: var(--color-gray);
  box-shadow: var(--shadow-sm);
}

.planner__stop-header {
  display: flex;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-md);
}

.planner__stop-number {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  background: var(--color-primary);
  color: var(--color-white);
  border-radius: var(--radius-circle);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: var(--font-weight-semibold);
  font-size: var(--font-size-sm);
}

.planner__stop-info {
  flex: 1;
  min-width: 0;
}

.planner__stop-name {
  display: block;
  color: var(--color-text-primary);
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  margin-bottom: var(--spacing-xs);
}

.planner__stop-package-id {
  margin: 0 0 var(--spacing-xs);
  font-size: var(--font-size-sm);
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}

.package-id-label {
  color: var(--color-text-secondary);
  font-weight: var(--font-weight-medium);
}

.package-id-value {
  color: var(--color-primary);
  font-weight: var(--font-weight-semibold);
  font-family: monospace;
}

.planner__stop-address {
  margin: 0 0 var(--spacing-xs);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  line-height: var(--line-height-relaxed);
}

.planner__stop-eta {
  color: var(--color-text-light);
  font-size: var(--font-size-xs);
}

.planner__stop-actions {
  display: flex;
  gap: var(--spacing-sm);
}

.planner__stop-btn {
  flex: 1;
  border: none;
  padding: var(--spacing-sm) var(--spacing-lg);
  border-radius: var(--radius-full);
  cursor: pointer;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  transition: all var(--transition-base);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-xs);
}

.planner__stop-btn--details {
  background: var(--color-white);
  color: var(--color-primary);
  border: 1px solid var(--color-primary);
}

.planner__stop-btn--details:hover {
  background: var(--color-primary);
  color: var(--color-white);
  transform: translateY(-1px);
}

.planner__stop-btn--navigate {
  background: var(--color-primary);
  color: var(--color-white);
}

.planner__stop-btn--navigate:hover {
  background: var(--color-primary-dark);
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
