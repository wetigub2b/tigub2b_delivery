export interface FeatureFlags {
  mapTab: boolean;
  routePlanner: boolean;
}

const featureFlags: FeatureFlags = {
  mapTab: import.meta.env.VITE_FEATURE_MAP_TAB !== 'false',
  routePlanner: import.meta.env.VITE_FEATURE_ROUTE_PLANNER === 'true',
};

export default featureFlags;
