-- Add this to your schema if not present
CREATE TABLE IF NOT EXISTS notification_emails (
    id SERIAL PRIMARY KEY,
    email TEXT NOT NULL UNIQUE
);
