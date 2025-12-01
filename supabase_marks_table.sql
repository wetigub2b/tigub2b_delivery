-- Create marks table for map markers
CREATE TABLE IF NOT EXISTS public.marks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  latitude DOUBLE PRECISION NOT NULL,
  longitude DOUBLE PRECISION NOT NULL,
  type TEXT,
  description TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE public.marks ENABLE ROW LEVEL SECURITY;

-- Create policy to allow public read access (anonymous users can read markers)
DROP POLICY IF EXISTS "Allow public read access" ON public.marks;
CREATE POLICY "Allow public read access" ON public.marks
  FOR SELECT USING (true);

-- Create policy to allow authenticated users to insert (for admin/management)
DROP POLICY IF EXISTS "Allow authenticated insert" ON public.marks;
CREATE POLICY "Allow authenticated insert" ON public.marks
  FOR INSERT WITH CHECK (auth.role() = 'authenticated');

-- Create policy to allow authenticated users to update
DROP POLICY IF EXISTS "Allow authenticated update" ON public.marks;
CREATE POLICY "Allow authenticated update" ON public.marks
  FOR UPDATE USING (auth.role() = 'authenticated');

-- Create policy to allow authenticated users to delete
DROP POLICY IF EXISTS "Allow authenticated delete" ON public.marks;
CREATE POLICY "Allow authenticated delete" ON public.marks
  FOR DELETE USING (auth.role() = 'authenticated');

-- Add some sample markers for Greater Toronto Area (GTA)
INSERT INTO public.marks (name, latitude, longitude, type, description) VALUES
  ('Toronto Warehouse', 43.6532, -79.3832, 'Warehouse', 'Main distribution center in downtown Toronto'),
  ('Mississauga Hub', 43.5890, -79.6441, 'Hub', 'West GTA distribution hub'),
  ('Markham Center', 43.8561, -79.3370, 'Hub', 'North GTA distribution center'),
  ('Scarborough Depot', 43.7731, -79.2578, 'Depot', 'East GTA depot'),
  ('Brampton Station', 43.7315, -79.7624, 'Station', 'Northwest GTA station'),
  ('Richmond Hill Point', 43.8828, -79.4403, 'Point', 'North York region pickup point'),
  ('Vaughan Facility', 43.8361, -79.4983, 'Facility', 'Vaughan distribution facility'),
  ('Oakville Center', 43.4675, -79.6877, 'Center', 'Oakville service center'),
  ('Ajax Station', 43.8509, -79.0204, 'Station', 'East GTA Ajax station'),
  ('Milton Hub', 43.5183, -79.8774, 'Hub', 'West GTA Milton hub')
ON CONFLICT (id) DO NOTHING;

-- Create index for faster location queries
CREATE INDEX IF NOT EXISTS marks_location_idx ON public.marks (latitude, longitude);

-- Create index for type filtering
CREATE INDEX IF NOT EXISTS marks_type_idx ON public.marks (type);

-- Add comment to table
COMMENT ON TABLE public.marks IS 'Map markers for delivery locations in Greater Toronto Area';
