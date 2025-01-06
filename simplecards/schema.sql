DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS role;
DROP TABLE IF EXISTS groups;
DROP TABLE IF EXISTS deck;
DROP TABLE IF EXISTS card;

CREATE TABLE user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  email TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL,
  role_id INTEGER NOT NULL,
  total_learned_time TEXT,
  created_on TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  deleted INTEGER DEFAULT 0,
  deleted_on TEXT,
  FOREIGN KEY (role_id) REFERENCES role (id)
);

CREATE TABLE role (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL
);

CREATE TABLE groups (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  owner_id INTEGER NOT NULL,
  name TEXT NOT NULL,
  public INTEGER DEFAULT 0,
  deleted INTEGER DEFAULT 0,
  FOREIGN KEY (owner_id) REFERENCES user (id)
);

CREATE TABLE deck (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  group_id INTEGER NOT NULL,
  public INTEGER DEFAULT 0,
  deleted INTEGER DEFAULT 0,
  FOREIGN KEY (group_id) REFERENCES groups (id)
);

CREATE TABLE card (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  deck_id INTEGER NOT NULL,
  question TEXT NOT NULL,
  answer TEXT NOT NULL,
  public INTEGER DEFAULT 0,
  deleted INTEGER DEFAULT 0,
  FOREIGN KEY (deck_id) REFERENCES deck (id)
);

CREATE TABLE user_selections (
    user_id INTEGER PRIMARY KEY,
    selected_group_id INTEGER DEFAULT NULL,
    selected_deck_id INTEGER DEFAULT NULL,
    FOREIGN KEY (user_id) REFERENCES user (id),
    FOREIGN KEY (selected_group_id) REFERENCES groups (id),
    FOREIGN KEY (selected_deck_id) REFERENCES deck (id)
);

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
    ("by length of text"),
    ("set manually");

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
