-- Snowflake DDL for all tables
CREATE DATABASE IF NOT EXISTS ganesh_db;

DROP SCHEMA IF EXISTS ganesh_db.ganesh_schema;

CREATE SCHEMA ganesh_db.ganesh_schema;

use schema ganesh_db.ganesh_schema;

CREATE TABLE notification_emails (
    id INTEGER AUTOINCREMENT PRIMARY KEY,
    email STRING NOT NULL UNIQUE
);

CREATE TABLE payment_details (
    id INTEGER AUTOINCREMENT PRIMARY KEY,
    name STRING NOT NULL,
    amount NUMBER(10,2) NOT NULL,
    date DATE NOT NULL,
    comments STRING,
    payment_type STRING
);

CREATE TABLE transfers (
    id INTEGER AUTOINCREMENT PRIMARY KEY,
    name STRING NOT NULL,
    phone STRING,
    email STRING
);

CREATE TABLE sponsorship_items (
    id INTEGER AUTOINCREMENT PRIMARY KEY,
    item STRING UNIQUE NOT NULL,
    amount NUMBER NOT NULL,
    sponsor_limit INTEGER NOT NULL
);

CREATE TABLE sponsors (
    id INTEGER AUTOINCREMENT PRIMARY KEY,
    name STRING NOT NULL,
    email STRING,
    mobile STRING,
    apartment STRING NOT NULL,
    sponsorship STRING,
    donation NUMBER DEFAULT 0,
    gothram STRING
);

CREATE TABLE events (
    id INTEGER AUTOINCREMENT PRIMARY KEY,
    title STRING NOT NULL,
    event_date DATE,
    event_time TIME,
    link STRING,
    description STRING
);

CREATE TABLE expenses (
    id INTEGER AUTOINCREMENT PRIMARY KEY,
    category STRING NOT NULL,
    sub_category STRING NOT NULL,
    amount NUMBER(10,2) NOT NULL,
    date DATE NOT NULL,
    spent_by STRING NOT NULL,
    comments STRING,
    receipt_path STRING,
    receipt_blob BINARY,
    status STRING DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE prasad_seva (
    id INTEGER AUTOINCREMENT PRIMARY KEY,
    seva_type STRING,
    names STRING,
    item_name STRING,
    num_people INTEGER,
    apartment STRING,
    seva_date DATE,
    pooja_time STRING,
    created_by STRING,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status STRING DEFAULT 'active'
);

-- Create table for Laddu Auction Winners in Snowflake
CREATE TABLE laddu_winners (
    id INTEGER AUTOINCREMENT PRIMARY KEY,
    laddu_number INTEGER NOT NULL,
    winner_name STRING NOT NULL,
    amount INTEGER NOT NULL
);

-- Create table for settlements in Snowflake
CREATE TABLE settlements (
    id INTEGER AUTOINCREMENT PRIMARY KEY,
    name STRING NOT NULL,
    amount NUMBER(10,2) NOT NULL,
    sent_by STRING NOT NULL,
    comments STRING
);