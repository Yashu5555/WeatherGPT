-- Insert a user
INSERT INTO users (name, email, language, preferences)
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
