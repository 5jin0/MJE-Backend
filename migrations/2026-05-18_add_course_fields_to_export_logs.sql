ALTER TABLE export_logs
ADD COLUMN course_id VARCHAR(255) NULL AFTER page_path,
ADD COLUMN course_title VARCHAR(500) NULL AFTER course_id;
