import { watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { useHead } from '@unhead/vue';

export function useI18nHead() {
  const { t, locale } = useI18n();

  // Update document title and meta when locale changes
  const updateHead = () => {
    const title = t('app.title');
    const description = t('app.description');

    // Update document title
    document.title = title;

    // Update meta description
    const metaDescription = document.querySelector('meta[name="description"]');
    if (metaDescription) {
      metaDescription.setAttribute('content', description);
    }

    // Update HTML lang attribute
    document.documentElement.lang = locale.value;

    // Update PWA manifest name if needed
    const manifestLink = document.querySelector('link[rel="manifest"]');
    if (manifestLink) {
      // We could dynamically generate manifest here if needed
    }
  };

  // Update head on locale change
  watch(locale, updateHead, { immediate: true });

  return {
    updateHead
  };
}

// Helper function to get localized error messages
export function useI18nError() {
  const { t } = useI18n();

  const getErrorMessage = (error: any): string => {
    if (typeof error === 'string') {
      return error;
    }

    if (error?.response?.status) {
      switch (error.response.status) {
        case 401:
          return t('errors.unauthorized');
        case 403:
          return t('errors.forbidden');
        case 404:
          return t('errors.notFound');
        case 500:
          return t('errors.serverError');
        default:
          return t('errors.unknownError');
      }
    }

    if (error?.code === 'NETWORK_ERROR') {
      return t('errors.networkError');
    }

    return t('errors.unknownError');
  };

  return {
    getErrorMessage
  };
}

// Helper function for mobile-specific translations
export function useI18nMobile() {
  const { t } = useI18n();

  const getMobileMessage = (type: string): string => {
    switch (type) {
      case 'location':
        return t('mobile.locationPermission');
      case 'camera':
        return t('mobile.cameraPermission');
      case 'storage':
        return t('mobile.storagePermission');
      case 'offline':
        return t('mobile.networkOffline');
      case 'gps':
        return t('mobile.gpsDisabled');
      default:
        return t('errors.unknownError');
    }
  };

  return {
    getMobileMessage
  };
}