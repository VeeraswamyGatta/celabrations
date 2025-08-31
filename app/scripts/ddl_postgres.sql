CREATE TABLE IF NOT EXISTS notification_emails (
    id SERIAL PRIMARY KEY,
    email TEXT NOT NULL UNIQUE
);
-- Postgres DDL for all tables

CREATE TABLE IF NOT EXISTS payment_details (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    amount NUMERIC(10,2) NOT NULL,
    date DATE NOT NULL,
    comments TEXT,
    payment_type TEXT
);

CREATE TABLE IF NOT EXISTS transfers (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    phone TEXT,
    email TEXT
);

CREATE TABLE IF NOT EXISTS sponsorship_items (
    id SERIAL PRIMARY KEY,
    item TEXT UNIQUE NOT NULL,
    amount NUMERIC NOT NULL,
    sponsor_limit INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS sponsors (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT,
    mobile TEXT,
    apartment TEXT NOT NULL,
    sponsorship TEXT,
    donation NUMERIC DEFAULT 0,
    gothram STRING
);

CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    event_date DATE,
    event_time TIME,
    link TEXT,
    description TEXT
);

CREATE TABLE IF NOT EXISTS expenses (
    id SERIAL PRIMARY KEY,
    category TEXT NOT NULL,
    sub_category TEXT NOT NULL,
    amount NUMERIC(10,2) NOT NULL,
    date DATE NOT NULL,
    spent_by TEXT NOT NULL,
    comments TEXT,
    receipt_path TEXT,
    receipt_blob BYTEA,
    status VARCHAR(10) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS prasad_seva (
    id SERIAL PRIMARY KEY,
    seva_type VARCHAR(20),
    names TEXT,
    item_name VARCHAR(100),
    num_people INT,
    apartment VARCHAR(20),
    seva_date DATE,
    pooja_time VARCHAR(20),
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(10) DEFAULT 'active'
);

-- Create table for Laddu Auction Winners in PostgreSQL
CREATE TABLE laddu_winners (
    id SERIAL PRIMARY KEY,
    laddu_number INTEGER NOT NULL,
    winner_name VARCHAR(255) NOT NULL,
    amount INTEGER NOT NULL
);
