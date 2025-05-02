-- schema.sql

-- Create the database
CREATE DATABASE gift_ideas;

-- Connect to the database
\c gift_ideas;

-- Create the Users table
CREATE TABLE Users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL
);

-- Create the Person table
CREATE TABLE Person (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    name VARCHAR(50) NOT NULL UNIQUE,
    FOREIGN KEY (user_id) REFERENCES Users(id) ON DELETE CASCADE
);

-- Create the Gift table
CREATE TABLE Gift (
    id SERIAL PRIMARY KEY,
    person_id INTEGER NOT NULL,
    gift VARCHAR(100) NOT NULL,
    FOREIGN KEY (person_id) REFERENCES Person(id) ON DELETE CASCADE
);