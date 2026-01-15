-- Database setup for AI Panel Analytics (Cost-optimized: 1 row per user)
-- Run this in Supabase SQL Editor

-- 1. Add unique constraint on first_install_date
-- This allows upsert to work (update existing row instead of creating new)
ALTER TABLE public.ai_panel_analytics
ADD CONSTRAINT ai_panel_analytics_first_install_date_key
UNIQUE (first_install_date);

-- 2. Add updated_at column with auto-update trigger
ALTER TABLE public.ai_panel_analytics
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

-- Create function to auto-update updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger
DROP TRIGGER IF EXISTS update_ai_panel_analytics_updated_at ON public.ai_panel_analytics;
CREATE TRIGGER update_ai_panel_analytics_updated_at
    BEFORE UPDATE ON public.ai_panel_analytics
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 3. Add new columns for extended tracking
ALTER TABLE public.ai_panel_analytics
ADD COLUMN IF NOT EXISTS onboarding_completed BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS tutorial_status TEXT,
ADD COLUMN IF NOT EXISTS tutorial_current_step TEXT,
ADD COLUMN IF NOT EXISTS quick_action_usage_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS shortcut_usage_count INTEGER DEFAULT 0;

-- 4. Create index for common queries
CREATE INDEX IF NOT EXISTS idx_ai_panel_analytics_updated_at
ON public.ai_panel_analytics(updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_ai_panel_analytics_platform
ON public.ai_panel_analytics(platform);

-- 5. Enable Row Level Security (optional but recommended)
ALTER TABLE public.ai_panel_analytics ENABLE ROW LEVEL SECURITY;

-- Create policy to allow Edge Function to insert/update
CREATE POLICY "Allow service role full access" ON public.ai_panel_analytics
FOR ALL
USING (true)
WITH CHECK (true);
