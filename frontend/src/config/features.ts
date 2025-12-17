export interface FeatureFlags {
  mapTab: boolean;
  routePlanner: boolean;
  adminDispatch: boolean;
  adminReports: boolean;
}

const featureFlags: FeatureFlags = {
  mapTab: import.meta.env.VITE_FEATURE_MAP_TAB !== 'false',
  routePlanner: import.meta.env.VITE_FEATURE_ROUTE_PLANNER === 'true',
  adminDispatch: import.meta.env.VITE_FEATURE_ADMIN_DISPATCH !== 'false',
  adminReports: import.meta.env.VITE_FEATURE_ADMIN_REPORTS !== 'false',
};

export default featureFlags;
