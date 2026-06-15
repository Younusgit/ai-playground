-- AI Playground Database Schema
-- Run this on Supabase SQL Editor or psql

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    credits INTEGER DEFAULT 100,
    is_banned BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- API Keys table (admin managed)
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    provider VARCHAR(50) UNIQUE NOT NULL,
    key_value TEXT NOT NULL,
    label VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Models table
CREATE TABLE IF NOT EXISTS models (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    display_name VARCHAR(100) NOT NULL,
    provider VARCHAR(50) NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    description TEXT,
    is_enabled BOOLEAN DEFAULT TRUE,
    cost_per_1k_input DECIMAL(10,6) DEFAULT 0,
    cost_per_1k_output DECIMAL(10,6) DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- User limits table
CREATE TABLE IF NOT EXISTS user_limits (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    daily_message_limit INTEGER DEFAULT 50,
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id)
);

-- Usage logs table
CREATE TABLE IF NOT EXISTS usage_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    model_id UUID REFERENCES models(id) ON DELETE SET NULL,
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    duration_ms INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_usage_user_id ON usage_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_usage_created_at ON usage_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_usage_model_id ON usage_logs(model_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Insert default models
INSERT INTO models (display_name, provider, model_name, description) VALUES
    ('GPT-4o', 'openai', 'gpt-4o', 'OpenAI most capable model'),
    ('GPT-4o Mini', 'openai', 'gpt-4o-mini', 'Fast and affordable GPT-4'),
    ('GPT-3.5 Turbo', 'openai', 'gpt-3.5-turbo', 'Fast OpenAI model'),
    ('Claude 3.5 Sonnet', 'anthropic', 'claude-sonnet-4-6', 'Anthropic Claude Sonnet'),
    ('Claude 3 Haiku', 'anthropic', 'claude-haiku-4-5-20251001', 'Fast Anthropic model'),
    ('Gemini 1.5 Pro', 'google', 'gemini-1.5-pro', 'Google Gemini Pro'),
    ('Gemini 1.5 Flash', 'google', 'gemini-1.5-flash', 'Fast Google Gemini'),
    ('Llama 3.1 70B', 'groq', 'llama-3.1-70b-versatile', 'Fast Llama via Groq'),
    ('Mixtral 8x7B', 'groq', 'mixtral-8x7b-32768', 'Mixtral via Groq'),
    ('Llama 3.1 405B', 'together', 'meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo', 'Largest open model')
ON CONFLICT DO NOTHING;

-- Update function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
