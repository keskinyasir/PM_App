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

# --- DB Operations ---
def add_project(name, description, start_date, end_date):
    conn = get_connection()
    conn.execute("""
        INSERT INTO projects (name, description, start_date, end_date)
        VALUES (?, ?, ?, ?)
    """, (name, description, start_date, end_date))
    conn.commit()
    conn.close()

def fetch_projects():
    conn = get_connection()
    cursor = conn.execute("SELECT * FROM projects ORDER BY id DESC")
    projects = cursor.fetchall()
    conn.close()
    return projects

def delete_project(project_id):
    conn = get_connection()
    conn.execute("DELETE FROM tasks WHERE project_id = ?", (project_id,))
    conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    conn.commit()
    conn.close()

def add_task(project_id, title, due_date, assignee, status):
    conn = get_connection()
    conn.execute("""
        INSERT INTO tasks (project_id, title, due_date, assignee, status)
        VALUES (?, ?, ?, ?, ?)
    """, (project_id, title, due_date, assignee, status))
    conn.commit()
    conn.close()

def fetch_tasks(project_id=None):
    conn = get_connection()
    if project_id:
        cursor = conn.execute("SELECT * FROM tasks WHERE project_id = ? ORDER BY id DESC", (project_id,))
    else:
        cursor = conn.execute("SELECT * FROM tasks ORDER BY id DESC")
    tasks = cursor.fetchall()
    conn.close()
    return tasks

def delete_task(task_id):
    conn = get_connection()
    conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()

def update_task_status(task_id, new_status):
    conn = get_connection()
    conn.execute("UPDATE tasks SET status = ? WHERE id = ?", (new_status, task_id))
    conn.commit()
    conn.close()

# --- Initialize DB ---
initialize_db()

st.title("📋 Simple Project and Task Manager")

# --- State keys helpers ---
def reset_project_inputs():
    for key in ['project_name', 'project_description', 'project_start', 'project_end']:
        if key in st.session_state:
            del st.session_state[key]

def reset_task_inputs(proj_id):
    keys = [f'task_title_{proj_id}', f'task_due_{proj_id}', f'task_assignee_{proj_id}', f'task_status_{proj_id}']
    for key in keys:
        if key in st.session_state:
            del st.session_state[key]

# --- Add New Project ---
with st.expander("➕ Add New Project"):
    project_name = st.text_input("Project Name", key='project_name')
    project_description = st.text_area("Description", key='project_description')
    project_start = st.date_input("Start Date", value=date.today(), key='project_start')
    project_end = st.date_input("End Date", value=date.today(), key='project_end')

    if st.button("Add Project"):
        if not project_name:
            st.error("Project name cannot be empty!")
        elif project_start > project_end:
            st.error("Start date cannot be after end date!")
        else:
            add_project(project_name, project_description, project_start.isoformat(), project_end.isoformat())
            st.success(f"Project '{project_name}' added successfully!")
            reset_project_inputs()

st.markdown("---")

# --- Display Projects ---
projects = fetch_projects()
if projects:
    st.subheader("Projects")
    for project in projects:
        proj_id, name, desc, start, end = project
        with st.expander(f"🗂 {name} (ID: {proj_id})"):
            st.write(f"**Description:** {desc}")
            st.write(f"**Start:** {start} | **End:** {end}")

            # --- Show Tasks ---
            tasks = fetch_tasks(proj_id)
            if tasks:
                st.markdown("**Tasks:**")
                for task in tasks:
                    t_id, p_id, title, due, assignee, status = task
                    st.write(f"- [{status}] **{title}** | Assignee: {assignee} | Due: {due}")

                    cols = st.columns([1,3])
                    if cols[0].button(f"Delete Task {t_id}", key=f"del_task_{t_id}"):
                        delete_task(t_id)
                        st.experimental_rerun = lambda: None  # dummy, ignore
                        st.success("Task deleted.")
                        st.experimental_rerun = None
                        st.experimental_rerun = None  # We can't rerun, so use workaround: show success and reload UI
                        # Instead of rerun, just reload page manually or rely on session_state

                    new_status = cols[1].selectbox(f"Update Status {t_id}", ['To Do', 'In Progress', 'Blocked', 'Completed'],
                                                  index=['To Do', 'In Progress', 'Blocked', 'Completed'].index(status),
                                                  key=f"status_{t_id}")
                    if cols[1].button(f"Update {t_id}", key=f"update_status_{t_id}"):
                        update_task_status(t_id, new_status)
                        st.success(f"Task status updated to '{new_status}'.")

            else:
                st.info("No tasks for this project.")

            # --- Add New Task ---
            st.markdown("Add New Task")
            task_title = st.text_input(f"Task Title - Project {proj_id}", key=f"task_title_{proj_id}")
            task_due = st.date_input(f"Due Date - Project {proj_id}", value=date.today(), key=f"task_due_{proj_id}")
            task_assignee = st.selectbox(f"Assignee - Project {proj_id}", ['Alice', 'Bob', 'Charlie', 'Dana'], key=f"task_assignee_{proj_id}")
            task_status = st.selectbox(f"Status - Project {proj_id}", ['To Do', 'In Progress', 'Blocked', 'Completed'], key=f"task_status_{proj_id}")

            if st.button(f"Add Task - Project {proj_id}", key=f"add_task_{proj_id}"):
                if not task_title:
                    st.error("Task title cannot be empty!")
                else:
                    add_task(proj_id, task_title, task_due.isoformat(), task_assignee, task_status)
                    st.success(f"Task '{task_title}' added!")
                    reset_task_inputs(proj_id)

            # --- Delete Project ---
            if st.button(f"Delete Project {proj_id}"):
                delete_project(proj_id)
                st.success(f"Project '{name}' deleted.")
else:
    st.info("No projects added yet.")
