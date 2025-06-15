import streamlit as st
import sqlite3
from datetime import date

DB_PATH = 'pm_app.db'

# --- Database Connection ---
def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

# --- Initialize Database (Create tables if not exist) ---
def initialize_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            start_date TEXT,
            end_date TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            title TEXT NOT NULL,
            due_date TEXT,
            assignee TEXT,
            status TEXT,
            FOREIGN KEY(project_id) REFERENCES projects(id)
        )
    """)
    conn.commit()
    conn.close()

# --- Add a new project ---
def add_project(name, description, start_date, end_date):
    conn = get_connection()
    conn.execute("""
        INSERT INTO projects (name, description, start_date, end_date)
        VALUES (?, ?, ?, ?)
    """, (name, description, start_date, end_date))
    conn.commit()
    conn.close()

# --- Fetch all projects ---
def fetch_projects():
    conn = get_connection()
    cursor = conn.execute("SELECT * FROM projects ORDER BY id DESC")
    projects = cursor.fetchall()
    conn.close()
    return projects

# --- Delete a project and its tasks ---
def delete_project(project_id):
    conn = get_connection()
    conn.execute("DELETE FROM tasks WHERE project_id = ?", (project_id,))
    conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    conn.commit()
    conn.close()

# --- Add a new task ---
def add_task(project_id, title, due_date, assignee, status):
    conn = get_connection()
    conn.execute("""
        INSERT INTO tasks (project_id, title, due_date, assignee, status)
        VALUES (?, ?, ?, ?, ?)
    """, (project_id, title, due_date, assignee, status))
    conn.commit()
    conn.close()

# --- Fetch tasks for a specific project ---
def fetch_tasks(project_id=None):
    conn = get_connection()
    if project_id:
        cursor = conn.execute("SELECT * FROM tasks WHERE project_id = ? ORDER BY id DESC", (project_id,))
    else:
        cursor = conn.execute("SELECT * FROM tasks ORDER BY id DESC")
    tasks = cursor.fetchall()
    conn.close()
    return tasks

# --- Delete a task ---
def delete_task(task_id):
    conn = get_connection()
    conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()

# --- Update task status ---
def update_task_status(task_id, new_status):
    conn = get_connection()
    conn.execute("UPDATE tasks SET status = ? WHERE id = ?", (new_status, task_id))
    conn.commit()
    conn.close()

# --- Initialize DB on app start ---
initialize_db()

# --- Streamlit UI ---
st.title("📋 Simple Project and Task Manager")

# Section: Add new project
with st.expander("➕ Add New Project"):
    project_name = st.text_input("Project Name")
    project_description = st.text_area("Description")
    project_start = st.date_input("Start Date", value=date.today())
    project_end = st.date_input("End Date", value=date.today())

    if st.button("Add Project"):
        if not project_name:
            st.error("Project name cannot be empty!")
        elif project_start > project_end:
            st.error("Start date cannot be after end date!")
        else:
            add_project(project_name, project_description, project_start.isoformat(), project_end.isoformat())
            st.success(f"Project '{project_name}' added successfully!")
            st.experimental_rerun()

st.markdown("---")

# Display all projects
projects = fetch_projects()
if projects:
    st.subheader("Projects")
    for project in projects:
        proj_id, name, desc, start, end = project
        with st.expander(f"🗂 {name} (ID: {proj_id})"):
            st.write(f"**Description:** {desc}")
            st.write(f"**Start:** {start} | **End:** {end}")

            # Show tasks under this project
            tasks = fetch_tasks(proj_id)
            if tasks:
                st.markdown("**Tasks:**")
                for task in tasks:
                    t_id, p_id, title, due, assignee, status = task
                    st.write(f"- [{status}] **{title}** | Assignee: {assignee} | Due: {due}")

                    col1, col2 = st.columns([1,3])
                    with col1:
                        if st.button(f"Delete Task {t_id}", key=f"del_task_{t_id}"):
                            delete_task(t_id)
                            st.experimental_rerun()
                    with col2:
                        new_status = st.selectbox(f"Update Status {t_id}", ['To Do', 'In Progress', 'Blocked', 'Completed'],
                                                  index=['To Do', 'In Progress', 'Blocked', 'Completed'].index(status),
                                                  key=f"status_{t_id}")
                        if st.button(f"Update {t_id}", key=f"update_status_{t_id}"):
                            update_task_status(t_id, new_status)
                            st.success(f"Task status updated to '{new_status}'.")
                            st.experimental_rerun()
            else:
                st.info("No tasks for this project.")

            # Add new task to project
            st.markdown("Add New Task")
            task_title = st.text_input(f"Task Title - Project {proj_id}", key=f"title_{proj_id}")
            task_due = st.date_input(f"Due Date - Project {proj_id}", value=date.today(), key=f"due_{proj_id}")
            task_assignee = st.selectbox(f"Assignee - Project {proj_id}", ['Alice', 'Bob', 'Charlie', 'Dana'], key=f"assignee_{proj_id}")
            task_status = st.selectbox(f"Status - Project {proj_id}", ['To Do', 'In Progress', 'Blocked', 'Completed'], key=f"status_task_{proj_id}")

            if st.button(f"Add Task - Project {proj_id}", key=f"add_task_{proj_id}"):
                if not task_title:
                    st.error("Task title cannot be empty!")
                else:
                    add_task(proj_id, task_title, task_due.isoformat(), task_assignee, task_status)
                    st.success(f"Task '{task_title}' added!")
                    st.experimental_rerun()

            # Button to delete the project
            if st.button(f"Delete Project {proj_id}"):
                delete_project(proj_id)
                st.success(f"Project '{name}' deleted.")
                st.experimental_rerun()
else:
    st.info("No projects added yet.")
