CREATE TABLE Users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
);

CREATE TABLE Person (
    id serial PRIMARY KEY,
    name VARCHAR(30) NOT NULL UNIQUE
);

CREATE TABLE Gift (
    id serial PRIMARY KEY,
    person_id integer NOT NULL,
    gift VARCHAR(50) NOT NULL,
    FOREIGN KEY (person_id) REFERENCES Person(id) ON DELETE CASCADE
);
