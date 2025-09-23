<template>
  <section class="planner">
    <header class="planner__header">
      <div class="planner__header-content">
        <button @click="goBack" class="planner__back-btn">
          ← {{ $t('routePlanner.backToTasks') }}
        </button>
        <div>
          <h2>{{ $t('routePlanner.title') }}</h2>
          <p>{{ $t('routePlanner.description') }}</p>
        </div>
      </div>
      <button class="planner__refresh" @click="fetchRoute">{{ $t('routePlanner.refreshPlan') }}</button>
    </header>

    <div class="planner__content">
      <MapPanel :stops="route?.stops ?? []" />
      <aside class="planner__sidebar">
        <h3>{{ $t('routePlanner.stops') }}</h3>
        <ol>
          <li v-for="stop in route?.stops ?? []" :key="stop.orderSn">
            <strong>{{ stop.sequence }}. {{ stop.receiverName }}</strong>
            <p>{{ stop.address }}</p>
            <small>{{ stop.eta }}</small>
          </li>
        </ol>
      </aside>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useOrdersStore } from '@/store/orders';
import MapPanel from '@/components/MapPanel.vue';
import { useGoogleMaps } from '@/composables/useGoogleMaps';

const router = useRouter();
const ordersStore = useOrdersStore();

useGoogleMaps();

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
}

.planner__content {
  display: grid;
  grid-template-columns: 3fr 2fr;
  gap: 16px;
}

.planner__sidebar {
  background: #ffffff;
  padding: 16px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.08);
}

.planner__sidebar ol {
  margin: 0;
  padding-left: 20px;
  display: grid;
  gap: 12px;
}

/* Responsive styles */
@media (max-width: 768px) {
  .planner__header-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .planner__content {
    grid-template-columns: 1fr;
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
}
</style>
