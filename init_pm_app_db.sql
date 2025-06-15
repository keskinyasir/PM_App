
-- Create projects table
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_code TEXT UNIQUE,
    name TEXT NOT NULL,
    description TEXT,
    start_date TEXT,
    end_date TEXT,
    status TEXT,
    members TEXT,
    created_by TEXT,
    created_at TEXT
);

-- Create tasks table
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    title TEXT NOT NULL,
    due_date TEXT,
    assignee TEXT,
    status TEXT,
    created_at TEXT,
    FOREIGN KEY(project_id) REFERENCES projects(id)
);
