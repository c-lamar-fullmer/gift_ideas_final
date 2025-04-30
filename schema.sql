CREATE TABLE Users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL
);

CREATE TABLE Person (
    id serial PRIMARY KEY,
    user_id INTEGER NOT NULL,
    name VARCHAR(30) NOT NULL UNIQUE,
    FOREIGN KEY (user_id) REFERENCES Users(id) ON DELETE CASCADE
);

CREATE TABLE Gift (
    id serial PRIMARY KEY,
    person_id integer NOT NULL,
    gift VARCHAR(50) NOT NULL,
    FOREIGN KEY (person_id) REFERENCES Person(id) ON DELETE CASCADE
);