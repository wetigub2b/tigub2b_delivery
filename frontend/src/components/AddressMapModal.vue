<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="show" class="modal-overlay" @click="handleClose">
        <div class="modal-container" @click.stop>
          <div class="modal-header">
            <h3>{{ $t('addressMap.title') }}</h3>
            <button class="modal-close" @click="handleClose" aria-label="Close">
              ✕
            </button>
          </div>

          <div class="modal-body">
            <div class="address-display">
              <span class="address-icon">📍</span>
              <span class="address-text">{{ address }}</span>
            </div>

            <div v-if="isLoading" class="loading-state">
              <div class="spinner"></div>
              <p>{{ $t('common.loading') }}</p>
            </div>

            <div v-else-if="error" class="error-state">
              <p>{{ error }}</p>
              <button @click="geocodeAddress" class="retry-button">{{ $t('map.retry') }}</button>
            </div>

            <div v-else class="map-container">
              <div ref="mapContainer" class="map"></div>
            </div>
          </div>

          <div class="modal-footer">
            <button class="modal-button modal-button--secondary" @click="openInGoogleMaps">
              {{ $t('addressMap.openInGoogleMaps') }}
            </button>
            <button class="modal-button modal-button--primary" @click="handleClose">
              {{ $t('common.close') }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, watch, onUnmounted, nextTick } from 'vue';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';

const props = defineProps<{
  show: boolean;
  address: string;
}>();

const emit = defineEmits<{
  close: [];
}>();

const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN || '';

const mapContainer = ref<HTMLDivElement | null>(null);
const isLoading = ref(false);
const error = ref<string | null>(null);
const mapReady = ref(false);
let map: mapboxgl.Map | null = null;
let marker: mapboxgl.Marker | null = null;

watch(() => props.show, async (newValue) => {
  if (newValue && props.address) {
    await geocodeAddress();
  } else {
    cleanupMap();
    mapReady.value = false;
  }
}, { immediate: true });

async function geocodeAddress() {
  isLoading.value = true;
  error.value = null;
  mapReady.value = false;

  try {
    const response = await fetch(
      `https://api.mapbox.com/geocoding/v5/mapbox.places/${encodeURIComponent(props.address)}.json?access_token=${MAPBOX_TOKEN}&limit=1`
    );
    
    if (!response.ok) {
      throw new Error('Failed to geocode address');
    }

    const data = await response.json();
    
    if (data.features && data.features.length > 0) {
      const [lng, lat] = data.features[0].center;
      console.log('Geocoded coordinates:', lng, lat);
      
      // Set loading to false first to show the map container
      isLoading.value = false;
      
      // Wait for DOM to update, then init map
      await nextTick();
      // Use requestAnimationFrame to ensure layout is complete
      requestAnimationFrame(() => {
        setTimeout(() => {
          console.log('Initializing map, container:', mapContainer.value);
          if (mapContainer.value) {
            console.log('Container dimensions:', mapContainer.value.offsetWidth, mapContainer.value.offsetHeight);
          }
          initMap(lng, lat);
        }, 100);
      });
    } else {
      error.value = 'Address not found';
      isLoading.value = false;
    }
  } catch (err: any) {
    console.error('Geocoding error:', err);
    error.value = err.message || 'Failed to find address location';
    isLoading.value = false;
  }
}

function initMap(lng: number, lat: number) {
  console.log('initMap called with:', lng, lat, 'container:', mapContainer.value);
  if (!mapContainer.value) {
    console.error('Map container not available');
    return;
  }
  if (!MAPBOX_TOKEN) {
    console.error('Mapbox token not available');
    error.value = 'Mapbox token not configured';
    return;
  }

  cleanupMap();

  mapboxgl.accessToken = MAPBOX_TOKEN;

  try {
    map = new mapboxgl.Map({
      container: mapContainer.value,
      style: 'mapbox://styles/mapbox/streets-v12',
      center: [lng, lat],
      zoom: 15
    });

    map.on('load', () => {
      mapReady.value = true;
      // Ensure map resizes properly after load
      if (map) {
        map.resize();
      }
    });

    map.on('error', (e) => {
      console.error('Mapbox error:', e);
    });

    map.addControl(new mapboxgl.NavigationControl(), 'top-right');

    // Add marker at the address location
    marker = new mapboxgl.Marker({ color: '#e53935' })
      .setLngLat([lng, lat])
      .setPopup(new mapboxgl.Popup().setHTML(`<p>${props.address}</p>`))
      .addTo(map);

    // Open popup by default
    marker.togglePopup();
  } catch (err: any) {
    console.error('Error creating map:', err);
    error.value = err.message || 'Failed to initialize map';
  }
}

function cleanupMap() {
  if (marker) {
    marker.remove();
    marker = null;
  }
  if (map) {
    map.remove();
    map = null;
  }
}

function openInGoogleMaps() {
  const url = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(props.address)}`;
  window.open(url, '_blank');
}

function handleClose() {
  emit('close');
}

onUnmounted(() => {
  cleanupMap();
});
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2147483647;
  padding: var(--spacing-lg);
}

.modal-container {
  background: var(--color-white);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xl);
  max-width: 600px;
  width: 100%;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-lg);
  border-bottom: 1px solid var(--color-gray-light);
}

.modal-header h3 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
}

.modal-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: var(--color-text-secondary);
  cursor: pointer;
  padding: var(--spacing-xs);
  line-height: 1;
  transition: color var(--transition-base);
}

.modal-close:hover {
  color: var(--color-text-primary);
}

.modal-body {
  padding: var(--spacing-lg);
  overflow-y: auto;
  flex: 1;
}

.address-display {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-sm);
  padding: var(--spacing-md);
  background: var(--color-gray-lighter);
  border-radius: var(--radius-md);
  margin-bottom: var(--spacing-lg);
}

.address-icon {
  font-size: 1.25rem;
}

.address-text {
  font-size: 0.9rem;
  color: var(--color-text-primary);
  line-height: 1.4;
}

.map-container {
  width: 100%;
  height: 300px;
  min-height: 300px;
  border-radius: var(--radius-md);
  overflow: hidden;
  background: #e0e0e0;
  position: relative;
}

.map {
  width: 100%;
  height: 100%;
  min-height: 300px;
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
}

/* Ensure Mapbox styles are not affected by scoped CSS */
:deep(.mapboxgl-map) {
  width: 100% !important;
  height: 100% !important;
  position: absolute !important;
  top: 0;
  left: 0;
}

:deep(.mapboxgl-canvas-container) {
  width: 100% !important;
  height: 100% !important;
}

:deep(.mapboxgl-canvas) {
  width: 100% !important;
  height: 100% !important;
}

:deep(.mapboxgl-ctrl-top-right) {
  top: 10px;
  right: 10px;
}

.loading-state,
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-xl);
  text-align: center;
  gap: var(--spacing-md);
  min-height: 200px;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid var(--color-gray-light);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.error-state p {
  color: var(--color-danger);
}

.retry-button {
  padding: var(--spacing-sm) var(--spacing-lg);
  background: var(--color-primary);
  color: var(--color-white);
  border: none;
  border-radius: var(--radius-md);
  font-weight: var(--font-weight-semibold);
  cursor: pointer;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-md);
  padding: var(--spacing-lg);
  border-top: 1px solid var(--color-gray-light);
}

.modal-button {
  padding: var(--spacing-sm) var(--spacing-lg);
  border-radius: var(--radius-md);
  font-weight: var(--font-weight-semibold);
  cursor: pointer;
  transition: all var(--transition-base);
  border: 1px solid transparent;
  font-size: 0.875rem;
}

.modal-button--primary {
  background: var(--color-primary);
  color: var(--color-white);
  border-color: var(--color-primary);
}

.modal-button--primary:hover {
  background: var(--color-primary-dark);
  border-color: var(--color-primary-dark);
}

.modal-button--secondary {
  background: var(--color-white);
  color: var(--color-primary);
  border-color: var(--color-primary);
}

.modal-button--secondary:hover {
  background: var(--color-primary);
  color: var(--color-white);
}

/* Modal transitions */
.modal-enter-active,
.modal-leave-active {
  transition: opacity var(--transition-base);
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .modal-container,
.modal-leave-active .modal-container {
  transition: transform var(--transition-base);
}

.modal-enter-from .modal-container,
.modal-leave-to .modal-container {
  transform: scale(0.95);
}

@media (max-width: 768px) {
  .modal-overlay {
    padding: var(--spacing-md);
  }

  .modal-container {
    max-height: 90vh;
  }

  .modal-footer {
    flex-direction: column;
  }

  .modal-button {
    width: 100%;
  }
}
</style>
