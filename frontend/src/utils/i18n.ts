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
