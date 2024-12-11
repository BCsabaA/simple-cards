CREATE TABLE user_selections (
    user_id INTEGER PRIMARY KEY,
    selected_group_id INTEGER DEFAULT NULL,
    selected_deck_id INTEGER DEFAULT NULL,
    FOREIGN KEY (user_id) REFERENCES user (id),
    FOREIGN KEY (selected_group_id) REFERENCES groups (id),
    FOREIGN KEY (selected_deck_id) REFERENCES deck (id)
);