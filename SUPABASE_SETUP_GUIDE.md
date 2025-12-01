# Supabase Setup Guide

## Getting Your Supabase Credentials

### Step 1: Sign Up for Supabase
1. Go to [https://supabase.com](https://supabase.com)
2. Click **"Start your project"** or **"Sign In"**
3. Sign up with GitHub, Google, or email

### Step 2: Create a New Project
1. After signing in, click **"New Project"**
2. Fill in the project details:
   - **Name**: e.g., "tigu-delivery-markers"
   - **Database Password**: Create a strong password (save it!)
   - **Region**: Choose closest to Toronto (e.g., "us-east-1")
   - **Pricing Plan**: Start with "Free" tier
3. Click **"Create new project"**
4. Wait 1-2 minutes for project to be provisioned

### Step 3: Get Your API Credentials
Once your project is ready:

1. Click on **"Settings"** (gear icon) in the left sidebar
2. Click on **"API"** section
3. You'll see two important values:

   **Project URL** (VITE_SUPABASE_URL):
   ```
   https://xxxxxxxxxx.supabase.co
   ```
   Copy this entire URL

   **anon/public key** (VITE_SUPABASE_ANON_KEY):
   ```
   eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3M...
   ```
   This is a long JWT token - copy the entire string

### Step 4: Add to Your .env.local
Create or edit `frontend/.env.local`:

```bash
VITE_SUPABASE_URL=https://xxxxxxxxxx.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Step 5: Create the Database Table
1. In Supabase dashboard, click **"SQL Editor"** in left sidebar
2. Click **"New query"**
3. Paste this SQL:

```sql
-- Create marks table
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

-- Allow public read access (anonymous users can read markers)
CREATE POLICY "Allow public read access" ON marks
  FOR SELECT USING (true);

-- Optional: Allow authenticated inserts (for admin)
CREATE POLICY "Allow authenticated insert" ON marks
  FOR INSERT WITH CHECK (auth.role() = 'authenticated');

-- Add some sample markers for GTA
INSERT INTO marks (name, latitude, longitude, type, description) VALUES
  ('Toronto Warehouse', 43.6532, -79.3832, 'Warehouse', 'Main distribution center in downtown Toronto'),
  ('Mississauga Hub', 43.5890, -79.6441, 'Hub', 'West GTA distribution hub'),
  ('Markham Center', 43.8561, -79.3370, 'Hub', 'North GTA distribution center'),
  ('Scarborough Depot', 43.7731, -79.2578, 'Depot', 'East GTA depot'),
  ('Brampton Station', 43.7315, -79.7624, 'Station', 'Northwest GTA station'),
  ('Richmond Hill Point', 43.8828, -79.4403, 'Point', 'North York region pickup point');
```

4. Click **"Run"** button (or press Ctrl+Enter)
5. You should see "Success. No rows returned"

### Step 6: Verify Your Setup
1. Click on **"Table Editor"** in left sidebar
2. You should see the **"marks"** table
3. Click on it to see the sample markers
4. You should see 6 markers with Toronto-area coordinates

### Step 7: View on Map (Optional)
1. In Table Editor, select **"marks"** table
2. Click the **"Map view"** icon if available
3. You should see markers plotted on a map

## Security Notes

### What is the anon key?
- The **anon/public key** is safe to use in your frontend
- It's designed to be public (that's why it's called "anon")
- Row Level Security (RLS) policies control what can be accessed
- With our policy, anyone can READ marks, but not modify them

### Row Level Security (RLS)
- We enabled RLS and created a read-only policy
- This means the public can view markers but can't add/edit/delete them
- To add markers, you'd need to be authenticated (or use the Supabase dashboard)

## Testing Your Setup

### Test in Browser Console (Quick Test)
Open your browser console and run:

```javascript
const { createClient } = supabaseJs;
const supabase = createClient(
  'YOUR_SUPABASE_URL',
  'YOUR_ANON_KEY'
);

const { data, error } = await supabase.from('marks').select('*');
console.log(data);
```

You should see your markers in the console.

## Alternative: Use MySQL Instead

If you prefer to use your existing MySQL database instead of Supabase:

1. Create a `marks` table in your MySQL database:
```sql
CREATE TABLE marks (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  latitude DOUBLE NOT NULL,
  longitude DOUBLE NOT NULL,
  type VARCHAR(100),
  description TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

2. Add markers data:
```sql
INSERT INTO marks (name, latitude, longitude, type, description) VALUES
  ('Toronto Warehouse', 43.6532, -79.3832, 'Warehouse', 'Main distribution center'),
  ('Mississauga Hub', 43.5890, -79.6441, 'Hub', 'West GTA hub'),
  ('Markham Center', 43.8561, -79.3370, 'Hub', 'North GTA hub');
```

3. Create a BFF API endpoint in `bff/app/routers/marks.py`:
```python
from fastapi import APIRouter
from app.db import get_db

router = APIRouter()

@router.get("/marks")
async def get_marks():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM marks")
    marks = cursor.fetchall()
    return marks
```

4. Modify `MapTab.vue` to use your BFF API instead of Supabase.

## Troubleshooting

### Can't find API credentials?
- Make sure project is fully created (not still "Setting up database...")
- Go to: Settings → API → Look under "Project API keys"

### Policy error when reading?
- Check RLS is enabled: `ALTER TABLE marks ENABLE ROW LEVEL SECURITY;`
- Check read policy exists: Look in Authentication → Policies

### No data showing?
- Make sure INSERT commands ran successfully
- Check in Table Editor that rows exist
- Try selecting in SQL Editor: `SELECT * FROM marks;`

## Quick Reference

**Location in Supabase Dashboard:**
```
Project Settings → API
```

**What you need:**
- Project URL (starts with https://)
- anon public key (long JWT token)

**In your .env.local:**
```bash
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJ...
```

## Free Tier Limits

Supabase Free tier includes:
- 500 MB database space
- 1 GB file storage
- 2 GB bandwidth per month
- 50,000 monthly active users
- Social OAuth providers

This is more than enough for the map markers feature!

## Support

If you encounter issues:
1. Check Supabase docs: [https://supabase.com/docs](https://supabase.com/docs)
2. Join Supabase Discord: [https://discord.supabase.com](https://discord.supabase.com)
3. Stack Overflow tag: `supabase`
