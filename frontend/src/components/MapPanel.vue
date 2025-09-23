<template>
  <div class="map-panel">
    <div ref="mapEl" class="map-panel__canvas"></div>
    <p v-if="!isApiLoaded" class="map-panel__placeholder">
      {{ $t('mapPanel.loadingMessage') }}
    </p>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref, watch } from 'vue';

interface StopSummary {
  orderSn: string;
  sequence: number;
  latitude?: number;
  longitude?: number;
}

const props = defineProps<{ stops: StopSummary[] }>();

const mapEl = ref<HTMLDivElement | null>(null);
const map = ref<google.maps.Map>();
const markers: google.maps.Marker[] = [];
const isApiLoaded = ref(false);

function initMap() {
  if (!mapEl.value || typeof google === 'undefined' || !google.maps) {
    return;
  }

  map.value = new google.maps.Map(mapEl.value, {
    center: { lat: 43.6532, lng: -79.3832 },
    zoom: 10,
    mapId: 'TIGU_DELIVERY'
  });

  isApiLoaded.value = true;
  renderStops();
}

function renderStops() {
  if (!map.value || typeof google === 'undefined' || !google.maps) {
    return;
  }

  markers.forEach(marker => marker.setMap(null));
  markers.length = 0;

  const bounds = new google.maps.LatLngBounds();

  props.stops.forEach(stop => {
    if (stop.latitude && stop.longitude) {
      const position = { lat: stop.latitude, lng: stop.longitude };
      const marker = new google.maps.Marker({
        map: map.value ?? undefined,
        position,
        label: String(stop.sequence)
      });
      markers.push(marker);
      bounds.extend(position);
    }
  });

  if (!bounds.isEmpty() && map.value) {
    map.value.fitBounds(bounds);
  }
}

function handleMapsReady() {
  initMap();
}

onMounted(() => {
  if (typeof window !== 'undefined') {
    window.addEventListener('maps-ready', handleMapsReady);
  }
  initMap();
});

onBeforeUnmount(() => {
  if (typeof window !== 'undefined') {
    window.removeEventListener('maps-ready', handleMapsReady);
  }
});

watch(
  () => props.stops,
  () => {
    if (isApiLoaded.value) {
      renderStops();
    }
  },
  { deep: true }
);
</script>

<style scoped>
.map-panel {
  position: relative;
  background: #e2e8f0;
  border-radius: 12px;
  overflow: hidden;
  min-height: 420px;
}

.map-panel__canvas {
  width: 100%;
  height: 100%;
}

.map-panel__placeholder {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #475569;
  background: rgba(226, 232, 240, 0.75);
}
</style>
