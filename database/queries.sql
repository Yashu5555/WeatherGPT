
INSERT INTO users (user_name, email, native_lang, preferences)
VALUES ('Test User', 'test@example.com', 'English', 'Temperature alerts');

SELECT * FROM users;

INSERT INTO weather_queries (user_id,question,location,at_what_time)
values(1,"Should I carry an umbrella tomorrow evening in Hyderabad?","hyderabad",current_timestamp());

SELECT * FROM weather_queries;

SELECT * FROM weather_history;

SELECT * FROM alerts;

SELECT * FROM advisories;
