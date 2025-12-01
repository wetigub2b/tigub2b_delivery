# Map Tab Feature

## Overview
The Map Tab feature adds a Mapbox-powered map view to the driver's dashboard, displaying markers fetched from Supabase. This feature is designed to be easily toggled on/off via environment variables.

## Features
- **Mapbox Integration**: Uses Mapbox GL JS for high-performance map rendering
- **GTA (Greater Toronto Area) Focus**: Map centers on Toronto by default
- **Dynamic Markers**: Fetches and displays markers from Supabase database
- **Interactive Popups**: Click markers to see details (name, type, description)
- **Navigation Controls**: Zoom, rotate, and fullscreen controls
- **Feature Flag**: Can be easily enabled/disabled without code changes

## Configuration

### Environment Variables
Add these to your `.env.local` file:

```bash
# Mapbox configuration
VITE_MAPBOX_TOKEN=your-mapbox-access-token

# Supabase configuration
VITE_SUPABASE_URL=your-supabase-project-url
VITE_SUPABASE_ANON_KEY=your-supabase-anon-key

# Feature flag (set to 'false' to disable)
VITE_FEATURE_MAP_TAB=true
```

### Getting API Keys

#### Mapbox Token
1. Sign up at [https://www.mapbox.com](https://www.mapbox.com)
2. Go to Account → Tokens
3. Create a new token or use the default public token
4. Copy the token to `VITE_MAPBOX_TOKEN`

#### Supabase Setup
1. Sign up at [https://supabase.com](https://supabase.com)
2. Create a new project
3. Get your project URL and anon key from Settings → API
4. Copy them to `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY`

### Database Schema
Create a `marks` table in your Supabase database:

```sql
CREATE TABLE marks (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL,
  latitude DOUBLE PRECISION NOT NULL,
  longitude DOUBLE PRECISION NOT NULL,
  type TEXT,
  description TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE marks ENABLE ROW LEVEL SECURITY;

-- Allow public read access
CREATE POLICY "Allow public read access" ON marks
  FOR SELECT USING (true);
```

### Sample Data
```sql
INSERT INTO marks (name, latitude, longitude, type, description) VALUES
  ('Toronto Warehouse', 43.6532, -79.3832, 'Warehouse', 'Main distribution center'),
  ('Mississauga Hub', 43.5890, -79.6441, 'Hub', 'West GTA hub'),
  ('Markham Center', 43.8561, -79.3370, 'Hub', 'North GTA hub');
```

## Enabling/Disabling the Feature

### To Enable
Set in `.env.local`:
```bash
VITE_FEATURE_MAP_TAB=true
```
Or simply don't set it (default is enabled)

### To Disable
Set in `.env.local`:
```bash
VITE_FEATURE_MAP_TAB=false
```

After changing the feature flag, rebuild the application:
```bash
npm run build
```

## File Structure

### New Files
- `frontend/src/config/features.ts` - Feature flag configuration
- `frontend/src/components/MapTab.vue` - Map tab component
- `MAP_TAB_FEATURE.md` - This documentation

### Modified Files
- `frontend/src/views/TaskBoard.vue` - Added map tab integration
- `frontend/src/locales/en.json` - Added English translations
- `frontend/src/locales/zh.json` - Added Chinese translations
- `frontend/.env.local.example` - Added configuration examples
- `frontend/package.json` - Added dependencies

## Dependencies
- `mapbox-gl` - Mapbox GL JS library
- `@supabase/supabase-js` - Supabase client

## Usage

### As a Driver
1. Log in to the driver dashboard
2. The "Map" tab will appear as the first tab (if enabled)
3. Click on markers to see location details
4. Use navigation controls to zoom and pan
5. Switch between Map and other tabs as needed

### As a Developer
The feature is isolated in `MapTab.vue` component. To customize:

#### Change Map Center
Edit `MapTab.vue`:
```typescript
const GTA_CENTER: [number, number] = [-79.3832, 43.6532]; // [longitude, latitude]
const GTA_ZOOM = 10;
```

#### Customize Marker Appearance
Edit the `addMarkers` function in `MapTab.vue`:
```typescript
el.innerHTML = '📍'; // Change emoji or HTML
el.style.fontSize = '24px'; // Change size
```

#### Change Map Style
Edit `initMap` function:
```typescript
map = new mapboxgl.Map({
  style: 'mapbox://styles/mapbox/streets-v12', // Try: dark-v11, light-v11, satellite-v9
  // ... other options
});
```

## Troubleshooting

### Map Not Loading
- Check that `VITE_MAPBOX_TOKEN` is set correctly
- Check browser console for errors
- Verify internet connection

### No Markers Appearing
- Check that `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` are set
- Verify `marks` table exists in Supabase
- Check Row Level Security policies allow public read access
- Check browser console for Supabase errors

### Feature Not Showing
- Verify `VITE_FEATURE_MAP_TAB` is not set to 'false'
- Rebuild the application: `npm run build`
- Clear browser cache

## Performance Considerations
- Markers are loaded once when the map initializes
- Map instance is properly cleaned up when component unmounts
- Consider implementing marker clustering for large datasets

## Future Enhancements
- Real-time marker updates using Supabase subscriptions
- Marker filtering by type
- Route visualization
- Driver location tracking
- Heat maps for delivery density
- Custom marker icons based on type
