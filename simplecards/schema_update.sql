CREATE TABLE learn_mode (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(30)
);

INSERT INTO learn_mode (name) VALUES
    ("by name A to Z"),
    ("by name Z to A"),
    ("by id 1 to n"),
    ("by id n to 1"),
    ("random");

CREATE TABLE read_time (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(30)
);

INSERT INTO read_time (name) VALUES
    ("by_char"),
    ("by_value");

CREATE TABLE user_settings (
    user_id INTEGER PRIMARY KEY,
    learn_mode_id INTEGER DEFAULT 1,
    repeat_list INTEGER DEFAULT 0,
    read_time_id INTEGER DEFAULT 1,
    ms_per_char INTEGER DEFAULT 50,
    q_min_read INTEGER DEFAULT 1000,
    a_min_read INTEGER DEFAULT 3000,
    q_read INTEGER DEFAULT 2000,
    a_read INTEGER DEFAULT 5000,
    FOREIGN KEY (learn_mode_id) REFERENCES learn_mode (id),
    FOREIGN KEY (read_time_id) REFERENCES read_time (id)
);
