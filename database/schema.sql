drop database weathergpt;
create database weathergpt;
use weathergpt;
create TABLE users (
    user_id SERIAL PRIMARY KEY,
    user_name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    native_lang VARCHAR(50) DEFAULT 'English',
    preferences TEXT
);

CREATE TABLE weather_queries (
    query_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(user_id),
    question TEXT NOT NULL,
    location VARCHAR(100),
    at_what_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

/*

*/
CREATE TABLE weather_history (
    id SERIAL PRIMARY KEY,
    location VARCHAR(100) NOT NULL,
    at_date DATE NOT NULL,
    temperature DECIMAL(5,2),
    rainfall DECIMAL(6,2),
    humidity DECIMAL(5,2),
    wind DECIMAL(6,2)
);

CREATE TABLE alerts (
    alert_id SERIAL PRIMARY KEY,
    location VARCHAR(100) NOT NULL,
    alert_type VARCHAR(100),
    severity VARCHAR(50),
    details TEXT,
    start_time TIMESTAMP,
    end_time TIMESTAMP
);

CREATE TABLE advisories (
    advisory_id SERIAL PRIMARY KEY,
    location VARCHAR(100) NOT NULL,
    advisory_type VARCHAR(100),
    details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
