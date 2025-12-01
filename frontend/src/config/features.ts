export interface FeatureFlags {
  mapTab: boolean;
}

const featureFlags: FeatureFlags = {
  mapTab: import.meta.env.VITE_FEATURE_MAP_TAB !== 'false',
};

export default featureFlags;
