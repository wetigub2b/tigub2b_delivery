import { Loader } from '@googlemaps/js-api-loader';
import { onMounted } from 'vue';

let loader: Loader | null = null;
let hasDispatched = false;

function loadApi() {
  if (hasDispatched) {
    return;
  }

  if (!loader) {
    loader = new Loader({
      apiKey: import.meta.env.VITE_GOOGLE_MAPS_KEY,
      version: 'weekly',
      libraries: ['maps', 'marker']
    });
  }

  loader
    .load()
    .then(() => {
      window.dispatchEvent(new Event('maps-ready'));
      hasDispatched = true;
    })
    .catch(error => {
      console.error('Failed to load Google Maps', error);
    });
}

export function useGoogleMaps() {
  onMounted(() => {
    loadApi();
  });
}
