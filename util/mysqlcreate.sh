#!/bin/bash

# Usage: ./mysqlcreate.sh root_user root_password target_user

ROOT_USER=$1
TARGET_USER=$2
DATABASE_NAME="labeldetection_dataset_localdb"

mysql -u "$ROOT_USER" -p <<EOF
-- Create DB
CREATE DATABASE IF NOT EXISTS \`$DATABASE_NAME\`;

USE \`$DATABASE_NAME\`;

-- Drop existing tables to allow schema updates
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS Applications;
DROP TABLE IF EXISTS Models;
DROP TABLE IF EXISTS TrainingImages;
DROP TABLE IF EXISTS ImagePrompts;
DROP TABLE IF EXISTS SystemPrompts;

SET FOREIGN_KEY_CHECKS = 1;

-- Create tables

CREATE TABLE Applications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    path VARCHAR(512) NOT NULL
);

CREATE TABLE Models (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    host VARCHAR(512),
    port INT
);

CREATE TABLE TrainingImages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    applicationId INT NOT NULL,
    guid VARCHAR(255) NOT NULL,
    filetype VARCHAR(16) NOT NULL,
    tesseract_ocr_extract TEXT,
    processed BIT,
    FOREIGN KEY (applicationId) REFERENCES Applications(id)
);

CREATE TABLE ImagePrompts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    application_id INT NOT NULL,
    target_model INT NOT NULL,
    prompt TEXT,
    FOREIGN KEY (application_id) REFERENCES Applications(id),
    FOREIGN KEY (target_model) REFERENCES Models(id)
);

CREATE TABLE SystemPrompts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    application_id INT NOT NULL,
    target_model INT NOT NULL,
    prompt TEXT,
    FOREIGN KEY (application_id) REFERENCES Applications(id),
    FOREIGN KEY (target_model) REFERENCES Models(id)
);

-- Grant read/write privileges
GRANT SELECT, INSERT, UPDATE, DELETE ON \`$DATABASE_NAME\`.* TO '$TARGET_USER'@'localhost';

FLUSH PRIVILEGES;
EOF

mysql -u "$ROOT_USER" -p"$ROOT_PASSWORD" "$DATABASE_NAME" < seeddata.sql