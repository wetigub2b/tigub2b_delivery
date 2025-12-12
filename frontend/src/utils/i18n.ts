/**
 * Parse i18n JSON string from backend
 * Example: '{"zh-CN":"仓库1","en-US":"Warehouse 1"}' -> 'Warehouse 1' (if locale is en)
 */
export function parseI18nJson(value: string | null, currentLocale: string = 'en'): string | null {
  if (!value) return null;

  // If it's already a plain string (not JSON), return as-is
  if (!value.startsWith('{')) return value;

  try {
    const parsed = JSON.parse(value);

    // Map common locale codes
    const localeMap: Record<string, string> = {
      en: 'en-US',
      zh: 'zh-CN',
      'en-US': 'en-US',
      'zh-CN': 'zh-CN'
    };

    const mappedLocale = localeMap[currentLocale] || 'en-US';

    // Try to get the value for current locale, fallback to en-US, then first available
    return parsed[mappedLocale] || parsed['en-US'] || Object.values(parsed)[0] || value;
  } catch (e) {
    // If parsing fails, return original value
    return value;
  }
}

/**
 * Map backend Chinese status label to i18n key
 * Backend returns hardcoded Chinese labels, this maps them to i18n keys for proper translation
 */
const prepareStatusLabelToKeyMap: Record<string, string> = {
  '待备货': 'prepareStatus.pendingPrepare',
  '已备货': 'prepareStatus.prepared',
  '司机已确认取货': 'prepareStatus.driverConfirmedPickup',
  '司机配送用户': 'prepareStatus.driverToUser',
  '司机送达仓库': 'prepareStatus.driverToWarehouse',
  '仓库已收货': 'prepareStatus.warehouseReceived',
  '已送达': 'prepareStatus.delivered',
  '司机已认领': 'prepareStatus.driverClaimed',
  '仓库确认送达': 'prepareStatus.warehouseConfirmedReady',
};

/**
 * Get i18n key for prepare status label from backend
 * @param backendLabel - The Chinese label returned from backend
 * @returns i18n key string to use with t() function
 */
export function getPrepareStatusI18nKey(backendLabel: string | null | undefined): string {
  if (!backendLabel) return 'prepareStatus.unknown';
  return prepareStatusLabelToKeyMap[backendLabel] || 'prepareStatus.unknown';
}
