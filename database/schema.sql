-- Voice Agent Database Schema

-- Contacts table
CREATE TABLE IF NOT EXISTS contacts (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    phone_number VARCHAR(20) NOT NULL,
    contact_type VARCHAR(20), -- 'friend' or 'facility'
    created_at TIMESTAMP DEFAULT NOW()
);

-- Calls table
CREATE TABLE IF NOT EXISTS calls (
    id SERIAL PRIMARY KEY,
    contact_id INTEGER REFERENCES contacts(id),
    call_type VARCHAR(20) NOT NULL, -- 'personal_message' or 'facility_test'

    -- Call details
    twilio_call_sid VARCHAR(100) UNIQUE,
    status VARCHAR(20) DEFAULT 'queued', -- 'queued', 'ringing', 'in-progress', 'completed', 'failed', 'no-answer', 'busy'
    direction VARCHAR(10) DEFAULT 'outbound',

    -- Custom message (for personal_message type)
    custom_message TEXT,

    -- Timing
    started_at TIMESTAMP,
    ended_at TIMESTAMP,
    duration INTEGER, -- seconds

    -- Results
    recording_url TEXT,
    recording_file_path TEXT,
    transcript TEXT,
    test_result VARCHAR(10), -- 'PASS'/'FAIL' for facility_test

    created_at TIMESTAMP DEFAULT NOW()
);

-- Transcript segments table (detailed conversation)
CREATE TABLE IF NOT EXISTS transcript_segments (
    id SERIAL PRIMARY KEY,
    call_id INTEGER REFERENCES calls(id) ON DELETE CASCADE,
    speaker VARCHAR(10) NOT NULL, -- 'agent' or 'user'
    text TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT NOW(),
    sequence_number INTEGER NOT NULL
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_calls_status ON calls(status);
CREATE INDEX IF NOT EXISTS idx_calls_twilio_sid ON calls(twilio_call_sid);
CREATE INDEX IF NOT EXISTS idx_calls_created_at ON calls(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_transcript_call_id ON transcript_segments(call_id);

-- Insert sample contact for testing
INSERT INTO contacts (name, phone_number, contact_type)
VALUES ('Test Contact', '+1234567890', 'friend')
ON CONFLICT DO NOTHING;
