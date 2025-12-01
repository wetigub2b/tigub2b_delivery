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
    <div ref="mapContainer" class="map"></div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, onUnmounted } from 'vue';
import mapboxgl from 'mapbox-gl';
import axios from 'axios';
import 'mapbox-gl/dist/mapbox-gl.css';

const mapContainer = ref<HTMLDivElement | null>(null);
const loading = ref(true);
const error = ref<string | null>(null);
let map: mapboxgl.Map | null = null;
let markers: mapboxgl.Marker[] = [];

const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN || '';
const API_URL = import.meta.env.VITE_API_URL || '';

const GTA_CENTER: [number, number] = [-79.3832, 43.6532]; // Toronto coordinates
const GTA_ZOOM = 10;

interface Mark {
  id: number;
  name: string;
  latitude: number;
  longitude: number;
  type?: string;
  description?: string;
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

function addMarkers(marks: Mark[]) {
  markers.forEach(marker => marker.remove());
  markers = [];

  marks.forEach((mark) => {
    if (!map) return;

    const el = document.createElement('div');
    el.className = 'custom-marker';
    el.innerHTML = '📍';
    el.style.fontSize = '24px';
    el.style.cursor = 'pointer';

    const popup = new mapboxgl.Popup({ offset: 25 }).setHTML(`
      <div class="marker-popup">
        <h3>${mark.name}</h3>
        ${mark.type ? `<p><strong>Type:</strong> ${mark.type}</p>` : ''}
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
      zoom: GTA_ZOOM
    });

    map.addControl(new mapboxgl.NavigationControl(), 'top-right');
    map.addControl(new mapboxgl.FullscreenControl(), 'top-right');

    map.on('load', async () => {
      try {
        const marks = await fetchMarks();
        addMarkers(marks);
      } catch (err: any) {
        console.error('Error loading marks:', err);
        error.value = err.message;
      } finally {
        loading.value = false;
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

:deep(.custom-marker) {
  transition: transform 0.2s;
}

:deep(.custom-marker:hover) {
  transform: scale(1.2);
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
</style>
