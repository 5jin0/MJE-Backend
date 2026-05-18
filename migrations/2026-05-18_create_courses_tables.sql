CREATE TABLE IF NOT EXISTS courses (
    course_id VARCHAR(36) PRIMARY KEY,
    grade VARCHAR(50) NOT NULL,
    area VARCHAR(100) NOT NULL,
    start_time VARCHAR(10) NOT NULL,
    transport VARCHAR(50) NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT NOT NULL,
    estimated_duration_minutes INT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS course_places (
    id INT AUTO_INCREMENT PRIMARY KEY,
    course_id VARCHAR(36) NOT NULL,
    place_order INT NOT NULL,
    place_type VARCHAR(50) NOT NULL,
    place_id INT NULL,
    name VARCHAR(500) NOT NULL,
    category VARCHAR(500) NULL,
    road_address VARCHAR(1000) NULL,
    address VARCHAR(1000) NULL,
    mapx VARCHAR(50) NULL,
    mapy VARCHAR(50) NULL,
    link VARCHAR(2000) NULL,
    telephone VARCHAR(100) NULL,
    keyword VARCHAR(500) NULL,
    collected_at VARCHAR(50) NULL,
    start_time VARCHAR(10) NULL,
    end_time VARCHAR(10) NULL,
    duration_minutes INT NULL,
    move_time_to_next_minutes INT NULL,
    FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE
);
