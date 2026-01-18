-- Supabase table schema for job_analyses
-- Run this in your Supabase SQL editor

CREATE TABLE IF NOT EXISTS job_analyses (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  job_description TEXT NOT NULL,
  biased_terms TEXT[],
  bias_type TEXT CHECK (bias_type IN ('masculine', 'feminine', 'neutral')),
  bias_explanation TEXT,
  inclusive_alternative TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create an index on created_at for faster queries
CREATE INDEX IF NOT EXISTS idx_job_analyses_created_at ON job_analyses(created_at);

-- Create an index on bias_type for filtering
CREATE INDEX IF NOT EXISTS idx_job_analyses_bias_type ON job_analyses(bias_type);
