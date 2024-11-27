CREATE TABLE notes (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    expire_after_read BOOLEAN NOT NULL,
    password TEXT,
    created_at DATETIME NOT NULL
);
