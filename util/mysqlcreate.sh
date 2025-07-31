#!/bin/bash

# Usage: ./mysqlcreate.sh root_user root_password target_user

ROOT_USER=$1
TARGET_USER=$2
DATABASE_NAME="labeldetection_dataset_localdb"

mysql -u "$ROOT_USER" -p <<EOF
-- Create DB
CREATE DATABASE IF NOT EXISTS \`$DATABASE_NAME\`;
USE \`$DATABASE_NAME\`;

SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS Applications;
DROP TABLE IF EXISTS Models;
DROP TABLE IF EXISTS TrainingImages;
DROP TABLE IF EXISTS ImagePrompts;
DROP TABLE IF EXISTS SystemPrompts;

DROP TABLE IF EXISTS applications;
DROP TABLE IF EXISTS models;
DROP TABLE IF EXISTS training_images;
DROP TABLE IF EXISTS image_prompts;
DROP TABLE IF EXISTS system_prompts;
DROP TABLE IF EXISTS image_prompts_models;

SET FOREIGN_KEY_CHECKS = 1;

CREATE TABLE applications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    path VARCHAR(512) NOT NULL,
    leading_prompt TEXT,
    middle_prompt TEXT,
    trailing_prompt TEXT
);

CREATE TABLE models (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    host VARCHAR(512),
    port INT
);

CREATE TABLE training_images (
    id INT AUTO_INCREMENT PRIMARY KEY,
    application_id INT NOT NULL,
    guid VARCHAR(255) NOT NULL,
    filetype VARCHAR(16) NOT NULL,
    tesseract_ocr_extract TEXT,
    processed BOOLEAN,
    FOREIGN KEY (application_id) REFERENCES applications(id)
);

CREATE TABLE image_prompts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    application_id INT NOT NULL,
    prompt TEXT,
    json_property TEXT,
    json_placeholder TEXT,
    FOREIGN KEY (application_id) REFERENCES applications(id)
);

CREATE TABLE image_prompts_models (
    image_prompt_id INT NOT NULL,
    model_id INT NOT NULL,
    PRIMARY KEY (image_prompt_id, model_id),
    FOREIGN KEY (image_prompt_id) REFERENCES image_prompts(id) ON DELETE CASCADE,
    FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE CASCADE
);

CREATE TABLE datasets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    application_id INT NOT NULL,
    description TEXT,
    reviewed BIT,
    evaluation TEXT,
    auto_description TEXT,
    FOREIGN KEY (application_id) REFERENCES applications(id) ON DELETE CASCADE
);

-- Grant read/write privileges
GRANT SELECT, INSERT, UPDATE, DELETE ON \`$DATABASE_NAME\`.* TO '$TARGET_USER'@'localhost';

FLUSH PRIVILEGES;
EOF

mysql -u "$ROOT_USER" -p"$ROOT_PASSWORD" "$DATABASE_NAME" < seeddata.sql