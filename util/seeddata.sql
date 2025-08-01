INSERT IGNORE INTO applications (name, path) VALUES
    ('food', '/mnt/hdd/aiml339/data/labeldetection-datagen-client/food'),
    ('wine', '/mnt/hdd/aiml339/data/labeldetection-datagen-client/wine'),
    ('pharma', '/mnt/hdd/aiml339/data/labeldetection-datagen-client/pharma');

INSERT IGNORE INTO models (name, host, port) VALUES
    ('qwen2_5-VL-7B', NULL, NULL),
    ('gemma3-4B', NULL, NULL);