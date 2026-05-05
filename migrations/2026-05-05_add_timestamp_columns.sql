ALTER TABLE home_events
ADD COLUMN timestamp VARCHAR(50) NOT NULL AFTER session_id;

ALTER TABLE courses_events
ADD COLUMN timestamp VARCHAR(50) NOT NULL AFTER session_id;

ALTER TABLE export_logs
ADD COLUMN timestamp VARCHAR(50) NOT NULL AFTER session_id;
