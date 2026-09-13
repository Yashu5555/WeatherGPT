DROP DATABASE weathergpt;
CREATE DATABASE weathergpt;
use weathergpt;
create TABLE users (
    user_id int PRIMARY KEY auto_increment,
    user_name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    native_lang VARCHAR(50) DEFAULT 'English',
    preferences TEXT
);

CREATE TABLE weather_queries (
    query_id int PRIMARY KEY auto_increment,
    user_id INT,
    question TEXT NOT NULL,
    location VARCHAR(100),
    at_what_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

/*

*/
CREATE TABLE weather_history (
    id INT PRIMARY KEY auto_increment,
    location VARCHAR(100) NOT NULL,
    at_date DATE NOT NULL,
    temperature DECIMAL(5,2),
    rainfall DECIMAL(6,2),
    humidity DECIMAL(5,2),
    wind DECIMAL(6,2)
);

CREATE TABLE alerts (
    alert_id INT PRIMARY KEY auto_increment,
    location VARCHAR(100) NOT NULL,
    alert_type VARCHAR(100),
    severity VARCHAR(50),
    details TEXT,
    start_time TIMESTAMP,
    end_time TIMESTAMP
);

CREATE TABLE advisories (
    advisory_id INT PRIMARY KEY auto_increment,
    location VARCHAR(100) NOT NULL,
    advisory_type VARCHAR(100),
    details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
