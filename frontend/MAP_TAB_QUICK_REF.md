# Map Tab Quick Reference

## Quick Enable/Disable

### Enable (Default)
```bash
# In frontend/.env.local
VITE_FEATURE_MAP_TAB=true
# or just don't set it (enabled by default)
```

### Disable
```bash
# In frontend/.env.local
VITE_FEATURE_MAP_TAB=false
```

## Required Environment Variables

```bash
# frontend/.env.local
VITE_MAPBOX_TOKEN=your-token-here
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-key-here
VITE_FEATURE_MAP_TAB=true
```

## Get API Keys

**Mapbox**: https://www.mapbox.com → Account → Tokens  
**Supabase**: https://supabase.com → Your Project → Settings → API

## Database Setup

```sql
-- Run in Supabase SQL Editor
CREATE TABLE marks (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL,
  latitude DOUBLE PRECISION NOT NULL,
  longitude DOUBLE PRECISION NOT NULL,
  type TEXT,
  description TEXT
);

ALTER TABLE marks ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow public read" ON marks FOR SELECT USING (true);
```

## Files Modified

```
frontend/
├── src/
│   ├── components/
│   │   └── MapTab.vue               [NEW]
│   ├── config/
│   │   └── features.ts              [NEW]
│   ├── views/
│   │   └── TaskBoard.vue            [MODIFIED]
│   └── locales/
│       ├── en.json                  [MODIFIED]
│       └── zh.json                  [MODIFIED]
└── .env.local.example               [MODIFIED]
```

## Component Architecture

```
features.ts
  ↓ exports { mapTab: boolean }
TaskBoard.vue
  ↓ imports MapTab & features
  ↓ conditionally adds map tab as first tab
  ↓ sets map as default if enabled
MapTab.vue
  ↓ standalone component
  ↓ Mapbox + Supabase integration
```

## Testing

1. **Check tab appears**: Map should be first tab
2. **Check default**: Map should be active on load
3. **Check map loads**: Should show GTA centered
4. **Check markers**: Should display from Supabase
5. **Check disable**: Set VITE_FEATURE_MAP_TAB=false and rebuild

## Common Issues

**Map not loading?**
- Check VITE_MAPBOX_TOKEN is set
- Check browser console for errors

**No markers?**
- Check VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY
- Verify marks table exists
- Check RLS policies allow public read

**Tab not showing?**
- Check VITE_FEATURE_MAP_TAB is not 'false'
- Rebuild after changing: `npm run build`

## Customization

**Change map center** (MapTab.vue line 27):
```typescript
const GTA_CENTER: [number, number] = [-79.3832, 43.6532];
```

**Change zoom level** (MapTab.vue line 28):
```typescript
const GTA_ZOOM = 10;
```

**Change map style** (MapTab.vue line 76):
```typescript
style: 'mapbox://styles/mapbox/dark-v11'
// Options: streets-v12, dark-v11, light-v11, satellite-v9
```

**Change marker icon** (MapTab.vue line 52):
```typescript
el.innerHTML = '📍'; // Change to any emoji or HTML
```
