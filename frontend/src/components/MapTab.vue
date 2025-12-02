<template>
  <div class="map-container">
    <div v-if="loading" class="map-loading">
      <div class="spinner"></div>
      <p>{{ $t('map.loading') }}</p>
    </div>
    <div v-else-if="error" class="map-error">
      <p>{{ error }}</p>
      <button @click="initMap" class="retry-button">{{ $t('map.retry') }}</button>
    </div>
    <div v-if="locationError" class="location-warning">
      <p>⚠️ {{ locationError }}</p>
      <button @click="startLocationTracking" class="retry-button">Enable Location</button>
    </div>
    <div v-if="!loading && !error" class="map-controls">
      <button @click="centerOnDriver" class="control-button" :disabled="!driverMarker">
        📍 My Location
      </button>
    </div>
    <div ref="mapContainer" class="map"></div>

    <!-- Pickup Location Modal -->
    <PickupLocationModal
      v-if="selectedMark"
      :show="showPickupModal"
      :mark="selectedMark"
      @close="closePickupModal"
    />
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, onUnmounted } from 'vue';
import mapboxgl from 'mapbox-gl';
import axios from 'axios';
import 'mapbox-gl/dist/mapbox-gl.css';
import { mobileUtils } from '../utils/mobile';
import PickupLocationModal from './PickupLocationModal.vue';

const mapContainer = ref<HTMLDivElement | null>(null);
const loading = ref(true);
const error = ref<string | null>(null);
const locationError = ref<string | null>(null);
let map: mapboxgl.Map | null = null;
let markers: mapboxgl.Marker[] = [];
let driverMarker: mapboxgl.Marker | null = null;
let watchId: number | null = null;

// Modal state
const showPickupModal = ref(false);
const selectedMark = ref<Mark | null>(null);

const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN || '';
const API_URL = import.meta.env.VITE_API_URL || '';

const GTA_CENTER: [number, number] = [-79.3832, 43.6532]; // Toronto coordinates
const INITIAL_ZOOM = 5; // Initial zoomed out view to see all locations
const DRIVER_ZOOM = 8; // Zoomed in view when centering on driver

interface Mark {
  id: number;
  name: string;
  latitude: number;
  longitude: number;
  type?: string;
  description?: string;
  shop_id?: number;
  warehouse_id?: number;
  order_count: number;
}

async function fetchMarks(): Promise<Mark[]> {
  try {
    const response = await axios.get(`${API_URL}/marks`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('delivery_token')}`
      }
    });
    
    return response.data.marks || [];
  } catch (err: any) {
    console.error('Error fetching marks:', err);
    throw new Error(err.response?.data?.detail || err.message || 'Failed to fetch marks');
  }
}

function openPickupModal(mark: Mark) {
  selectedMark.value = mark;
  showPickupModal.value = true;
}

function closePickupModal() {
  showPickupModal.value = false;
  selectedMark.value = null;
}

function addMarkers(marks: Mark[]) {
  markers.forEach(marker => marker.remove());
  markers = [];

  marks.forEach((mark) => {
    if (!map) return;

    // Only show pickup locations (with shop_id or warehouse_id)
    const isPickupLocation = mark.shop_id || mark.warehouse_id;
    if (!isPickupLocation) return;

    const el = document.createElement('div');
    el.className = 'custom-marker numbered-pin';
    el.innerHTML = `<span class="pin-number">${mark.order_count}</span>`;
    el.style.cursor = 'pointer';
    el.onclick = () => openPickupModal(mark);

    const popup = new mapboxgl.Popup({ offset: 25 }).setHTML(`
      <div class="marker-popup">
        <h3>${mark.name}</h3>
        ${mark.type ? `<p><strong>Type:</strong> ${mark.type}</p>` : ''}
        <p><strong>Available Orders:</strong> ${mark.order_count}</p>
        ${mark.description ? `<p>${mark.description}</p>` : ''}
      </div>
    `);

    const marker = new mapboxgl.Marker(el)
      .setLngLat([mark.longitude, mark.latitude])
      .setPopup(popup)
      .addTo(map);

    markers.push(marker);
  });
}

function updateDriverLocation(longitude: number, latitude: number) {
  if (!map) {
    console.warn('Map not initialized yet');
    return;
  }

  console.log('=== DRIVER LOCATION UPDATE ===');
  console.log('Coordinates:', { longitude, latitude });
  console.log('Are valid?', !isNaN(longitude) && !isNaN(latitude));
  console.log('Map loaded?', map.loaded());

  // Validate coordinates
  if (isNaN(longitude) || isNaN(latitude)) {
    console.error('Invalid coordinates:', { longitude, latitude });
    return;
  }

  if (driverMarker) {
    console.log('Moving existing marker');
    driverMarker.setLngLat([longitude, latitude]);
  } else {
    console.log('Creating NEW marker');

    // Create marker element WITHOUT custom styling that might interfere
    const el = document.createElement('div');
    el.innerHTML = '🚗';
    el.style.fontSize = '32px';
    el.style.lineHeight = '1';
    el.style.cursor = 'pointer';
    el.style.filter = 'drop-shadow(0 2px 4px rgba(0,0,0,0.3))';
    el.style.animation = 'pulse 2s infinite';
    // DO NOT set position, width, height, display, transform - let Mapbox handle it

    const popup = new mapboxgl.Popup({ offset: 25 }).setHTML(`
      <div class="marker-popup">
        <h3>Your Location</h3>
        <p><strong>Lat:</strong> ${latitude.toFixed(6)}</p>
        <p><strong>Lng:</strong> ${longitude.toFixed(6)}</p>
      </div>
    `);

    driverMarker = new mapboxgl.Marker(el)
      .setLngLat([longitude, latitude])
      .setPopup(popup)
      .addTo(map);

    console.log('Marker added to map');
    console.log('Marker LngLat:', driverMarker.getLngLat());

    // Check the actual DOM element position after a tick
    setTimeout(() => {
      const markerEl = driverMarker?.getElement();
      if (markerEl) {
        const transform = window.getComputedStyle(markerEl).transform;
        console.log('Marker DOM transform:', transform);
        console.log('Marker DOM position:', {
          top: markerEl.style.top,
          left: markerEl.style.left
        });
      }
    }, 100);
  }
}

async function startLocationTracking() {
  try {
    console.log('Starting location tracking...');
    locationError.value = null;
    
    const position = await mobileUtils.getCurrentPosition();
    console.log('Got initial position:', position);
    updateDriverLocation(position.longitude, position.latitude);
    
    if (map) {
      map.flyTo({
        center: [position.longitude, position.latitude],
        zoom: DRIVER_ZOOM,
        duration: 1500
      });
    }

    if (mobileUtils.isNative) {
      console.log('Using native geolocation');
      const { Geolocation } = await import('@capacitor/geolocation');
      watchId = await Geolocation.watchPosition(
        { enableHighAccuracy: true, timeout: 10000, maximumAge: 5000 },
        (position, err) => {
          if (err) {
            console.error('Location watch error:', err);
            return;
          }
          if (position) {
            console.log('Position update:', position.coords);
            updateDriverLocation(position.coords.longitude, position.coords.latitude);
          }
        }
      );
    } else {
      console.log('Using browser geolocation');
      if (!navigator.geolocation) {
        const errMsg = 'Geolocation is not supported by this browser';
        console.error(errMsg);
        locationError.value = errMsg;
        return;
      }
      watchId = navigator.geolocation.watchPosition(
        (position) => {
          console.log('Position update:', position.coords);
          updateDriverLocation(position.coords.longitude, position.coords.latitude);
        },
        (err) => {
          console.error('Location watch error:', err.code, err.message);
          if (err.code === 1) {
            locationError.value = 'Location permission denied. Please enable location access in your browser.';
          } else if (err.code === 2) {
            locationError.value = 'Location unavailable. Please check your device settings.';
          } else if (err.code === 3) {
            locationError.value = 'Location request timed out. Please try again.';
          }
        },
        { enableHighAccuracy: true, timeout: 10000, maximumAge: 5000 }
      );
    }
  } catch (err: any) {
    console.error('Error getting driver location:', err);
    console.error('Error details:', err.message, err.code);
    locationError.value = err.message || 'Failed to get location. Please check browser permissions.';
  }
}

function stopLocationTracking() {
  if (watchId !== null) {
    if (mobileUtils.isNative) {
      import('@capacitor/geolocation').then(({ Geolocation }) => {
        Geolocation.clearWatch({ id: watchId as any });
      });
    } else {
      navigator.geolocation.clearWatch(watchId);
    }
    watchId = null;
  }
  
  if (driverMarker) {
    driverMarker.remove();
    driverMarker = null;
  }
}

function centerOnDriver() {
  if (map && driverMarker) {
    const lngLat = driverMarker.getLngLat();
    map.flyTo({
      center: [lngLat.lng, lngLat.lat],
      zoom: DRIVER_ZOOM,
      duration: 1000
    });
  }
}

async function initMap() {
  if (!mapContainer.value) return;

  loading.value = true;
  error.value = null;

  try {
    if (!MAPBOX_TOKEN) {
      throw new Error('Mapbox token is not configured. Please set VITE_MAPBOX_TOKEN in .env.local');
    }

    if (!API_URL) {
      throw new Error('API URL is not configured. Please set VITE_API_URL in .env.local');
    }

    mapboxgl.accessToken = MAPBOX_TOKEN;

    map = new mapboxgl.Map({
      container: mapContainer.value,
      style: 'mapbox://styles/mapbox/streets-v12',
      center: GTA_CENTER,
      zoom: INITIAL_ZOOM
    });

    map.addControl(new mapboxgl.NavigationControl(), 'top-right');
    map.addControl(new mapboxgl.FullscreenControl(), 'top-right');

    map.on('load', async () => {
      try {
        console.log('Map loaded successfully');
        const marks = await fetchMarks();
        addMarkers(marks);
        loading.value = false;
      } catch (err: any) {
        console.error('Error loading marks:', err);
        error.value = err.message;
        loading.value = false;
      }
    });

    // Wait for map to be fully rendered (idle) before adding driver location
    map.on('idle', async () => {
      // Only start tracking once, when map is truly ready
      if (!driverMarker && !watchId) {
        console.log('Map is idle and ready for driver marker');
        await startLocationTracking();
      }
    });

    map.on('error', (e) => {
      console.error('Map error:', e);
      error.value = 'Failed to load map. Please check your connection and try again.';
      loading.value = false;
    });

  } catch (err: any) {
    console.error('Error initializing map:', err);
    error.value = err.message;
    loading.value = false;
  }
}

onMounted(() => {
  initMap();
});

onUnmounted(() => {
  stopLocationTracking();
  markers.forEach(marker => marker.remove());
  markers = [];
  if (map) {
    map.remove();
    map = null;
  }
});
</script>

<style scoped>
.map-container {
  position: relative;
  width: 100%;
  height: calc(100vh - 200px);
  min-height: 500px;
  border-radius: var(--radius-md);
  overflow: hidden;
  background: var(--color-gray-lighter);
}

.map {
  width: 100%;
  height: 100%;
}

.map-loading,
.map-error {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: var(--color-white);
  z-index: 1000;
  gap: var(--spacing-md);
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

.map-error p {
  color: var(--color-danger);
  text-align: center;
  padding: 0 var(--spacing-lg);
}

.retry-button {
  padding: var(--spacing-sm) var(--spacing-lg);
  background: var(--color-primary);
  color: var(--color-white);
  border: none;
  border-radius: var(--radius-md);
  font-weight: var(--font-weight-semibold);
  cursor: pointer;
  transition: all var(--transition-base);
}

.retry-button:hover {
  background: var(--color-primary-dark);
}

.location-warning {
  position: absolute;
  top: var(--spacing-md);
  left: 50%;
  transform: translateX(-50%);
  background: var(--color-warning);
  color: var(--color-white);
  padding: var(--spacing-md);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
  z-index: 1000;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-sm);
  max-width: 90%;
}

.location-warning p {
  margin: 0;
  font-weight: var(--font-weight-semibold);
  text-align: center;
}

.location-warning .retry-button {
  background: var(--color-white);
  color: var(--color-warning);
}

.location-warning .retry-button:hover {
  background: var(--color-gray-lighter);
}

.map-controls {
  position: absolute;
  top: var(--spacing-md);
  right: var(--spacing-md);
  z-index: 1000;
  display: flex;
  gap: var(--spacing-sm);
}

.control-button {
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--color-white);
  color: var(--color-text-primary);
  border: 1px solid var(--color-gray-light);
  border-radius: var(--radius-md);
  font-weight: var(--font-weight-semibold);
  cursor: pointer;
  box-shadow: var(--shadow-md);
  transition: all var(--transition-base);
}

.control-button:hover:not(:disabled) {
  background: var(--color-primary);
  color: var(--color-white);
  border-color: var(--color-primary);
}

.control-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

:deep(.custom-marker) {
  transition: transform 0.2s;
}

:deep(.custom-marker:hover) {
  transform: scale(1.2);
}

/* Remove the :deep(.driver-marker-icon) styles as they interfere with Mapbox positioning */

/* Note: Mapbox markers use CSS transforms for positioning.
   Any custom CSS that affects transform, position, width, height, or display
   can break the marker positioning system. Keep styling minimal. */

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
}

:deep(.marker-popup h3) {
  margin: 0 0 var(--spacing-xs) 0;
  font-size: 1rem;
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
}

:deep(.marker-popup p) {
  margin: var(--spacing-xs) 0;
  font-size: 0.875rem;
  color: var(--color-text-secondary);
}

:deep(.mapboxgl-popup-content) {
  padding: var(--spacing-md);
  border-radius: var(--radius-sm);
  box-shadow: var(--shadow-lg);
}

/* Numbered pin styles for pickup locations */
:deep(.numbered-pin) {
  width: 28px;
  height: 28px;
  background: #e53935;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
  border: 2px solid white;
}

:deep(.numbered-pin .pin-number) {
  color: white;
  font-size: 12px;
  font-weight: bold;
}

/* Empty pin styles - no longer used but kept for reference */
:deep(.empty-pin) {
  opacity: 0.5;
}

:deep(.empty-pin .pin-icon) {
  font-size: 24px;
  filter: grayscale(100%);
}
</style>
