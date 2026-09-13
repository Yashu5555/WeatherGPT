-- Insert a sample user
INSERT INTO users (user_name, email, native_lang, preferences)
VALUES ('Test User', 'test@example.com', 'English', 'Temperature alerts');

-- View all users
SELECT * FROM users;

-- View all weather queries
SELECT * FROM weather_queries;

-- View weather history
SELECT * FROM weather_history;

-- View alerts
SELECT * FROM alerts;

-- View advisories
SELECT * FROM advisories;

-- Join users with their weather queries
SELECT
    u.user_name,
    q.question,
    q.location,
    q.at_what_time
FROM users u
JOIN weather_queries q
ON u.user_id = q.user_id;

-- Find Hyderabad weather history
SELECT *
FROM weather_history
WHERE location = 'Hyderabad';

-- Find average temperature by location
SELECT
    location,
    AVG(temperature) AS average_temperature
FROM weather_history
GROUP BY location;

-- Count queries made by each user
SELECT
    u.user_name,
    COUNT(q.query_id) AS total_queries
FROM users u
JOIN weather_queries q
ON u.user_id = q.user_id
GROUP BY u.user_name;