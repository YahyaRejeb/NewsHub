CREATE DATABASE IF NOT EXISTS newshub1;
USE newshub1;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS interests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS user_interests (
    user_id INT NOT NULL,
    interest_id INT NOT NULL,
    PRIMARY KEY (user_id, interest_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (interest_id) REFERENCES interests(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS source (
    id INT AUTO_INCREMENT PRIMARY KEY,
    source_name VARCHAR(100) NOT NULL,
    source_url VARCHAR(255),
    UNIQUE KEY uq_source_name_url (source_name, source_url)
);

CREATE TABLE IF NOT EXISTS news (
    id INT AUTO_INCREMENT PRIMARY KEY,
    external_id VARCHAR(255),
    title VARCHAR(255) NOT NULL,
    content TEXT,
    image_url VARCHAR(255),
    article_url VARCHAR(500) NOT NULL,
    published_at DATETIME,
    interest_id INT,
    source_id INT,
    datatype VARCHAR(50),
    country VARCHAR(10),
    UNIQUE KEY uq_news_article_url (article_url),
    FOREIGN KEY (interest_id) REFERENCES interests(id) ON DELETE SET NULL,
    FOREIGN KEY (source_id) REFERENCES source(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS favorite (
    user_id INT NOT NULL,
    news_id INT NOT NULL,
    saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, news_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (news_id) REFERENCES news(id) ON DELETE CASCADE
);

-- Seed data for interests
INSERT IGNORE INTO interests (name) VALUES 
('Technology'), ('Business'), ('Politics'), 
('Science'), ('Entertainment'), ('Sports'), ('Health');
