# tugbas_project_app.py
import streamlit as st
import pandas as pd
from datetime import datetime, date
import supabase


# --- Supabase Configuration ---
SUPABASE_URL = "https://sxpjijtxiqhxzgyxpgtm.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InN4cGppanR4aXFoeHpneXhwZ3RtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTAwMTExMzAsImV4cCI6MjA2NTU4NzEzMH0.N_Ud7Pc83W5mf1yYYsJ8NzfQr_AeEkrGYT_CDFt0LB8"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- App Config ---
st.set_page_config(page_title="Tugba's Project", page_icon=":clipboard:", layout="wide")

# --- Styles ---
st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background-color: #f9f9f9; }
[data-testid="stSidebar"] { background-color: #1E3A8A; }
[data-testid="stSidebar"] * { color: #ffffff; }
.stMetric > div { background-color: #FFFFFF; border-left: 4px solid #1E3A8A; border-radius: 8px; padding: 10px; }
thead tr th { background-color: #E1EAF6 !important; color: #1E3A8A !important; }
.stButton>button { background-color: #1E3A8A; color: #ffffff; border-radius: 5px; }
.stButton>button:hover { background-color: #162c61; }
</style>
""", unsafe_allow_html=True)

# --- Authentication ---
def authenticate(email, pwd):
    return email == 'admin@example.com' and pwd == 'password123'

def login_page():
    st.title("Login")
    email = st.text_input("Email")
    pwd = st.text_input("Password", type="password")
    if st.button("Login"):
        if authenticate(email, pwd):
            st.session_state['logged_in'] = True
            st.session_state['user'] = email
        else:
            st.error("Invalid credentials")

# --- Database Operations ---
def fetch_projects():
    try:
        res = supabase.table("projects").select("*").execute()
        return pd.DataFrame(res.data)
    except Exception as e:
        st.error(f"Fetch projects failed: {e}")
        return pd.DataFrame()

def add_project(name, desc, start, end, members, user):
    try:
        data = {
            "name": name,
            "description": desc,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "status": "Not Started",
            "members": ",".join(members),
            "created_by": user,
            "created_at": datetime.now().isoformat()
        }
        supabase.table("projects").insert(data).execute()
        st.success(f"Project '{name}' added successfully")
    except Exception as e:
        st.error(f"Error: {e}")

def update_project_status(project_id, new_status):
    try:
        supabase.table("projects").update({"status": new_status}).eq("id", project_id).execute()
        st.success("Project status updated")
    except Exception as e:
        st.error(f"Update failed: {e}")

def delete_project(project_id):
    try:
        supabase.table("tasks").delete().eq("project_id", project_id).execute()
        supabase.table("projects").delete().eq("id", project_id).execute()
        st.success("Project deleted")
    except Exception as e:
        st.error(f"Delete failed: {e}")

def fetch_tasks():
    try:
        res = supabase.table("tasks").select("*").execute()
        return pd.DataFrame(res.data)
    except Exception as e:
        st.error(f"Fetch tasks failed: {e}")
        return pd.DataFrame()

def add_task(project_id, title, due_date, assignee, status):
    try:
        data = {
            "project_id": project_id,
            "title": title,
            "due_date": due_date.isoformat(),
            "assignee": assignee,
            "status": status,
            "created_at": datetime.now().isoformat()
        }
        supabase.table("tasks").insert(data).execute()
        st.success("Task added")
    except Exception as e:
        st.error(f"Add task failed: {e}")

def update_task(task_id, field, value):
    try:
        supabase.table("tasks").update({field: value}).eq("id", task_id).execute()
        st.success("Task updated")
    except Exception as e:
        st.error(f"Task update failed: {e}")

# --- Metrics ---
def project_metrics():
    df = fetch_projects()
    if df.empty: return pd.Series(dtype=int)
    return df['status'].value_counts()

def task_metrics():
    df = fetch_tasks()
    if df.empty: return pd.Series(dtype=int)
    return df['status'].value_counts()

# --- Main ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user' not in st.session_state:
    st.session_state['user'] = ''

if not st.session_state['logged_in']:
    login_page()
else:
    st.sidebar.header(f"Welcome {st.session_state['user']}")
    menu = st.sidebar.radio("Menu", ["Dashboard", "Projects", "Tasks", "Logout"])

    if menu == "Logout":
        st.session_state['logged_in'] = False
        st.session_state['user'] = ''
        st.experimental_rerun()

    elif menu == "Dashboard":
        st.title("📊 Dashboard")
        st.bar_chart(project_metrics())
        st.bar_chart(task_metrics())

    elif menu == "Projects":
        st.title("📁 Projects")

        with st.expander("➕ Add New Project"):
            name = st.text_input("Name")
            desc = st.text_area("Description")
            start = st.date_input("Start Date", value=date.today())
            end = st.date_input("End Date", value=date.today())
            members = st.multiselect("Members", ["Alice", "Bob", "Charlie", "Dana"])
            if st.button("Create Project"):
                add_project(name, desc, start, end, members, st.session_state['user'])

        df = fetch_projects()
        if not df.empty:
            st.dataframe(df[['id', 'name', 'status', 'start_date', 'end_date']])
            pid = st.selectbox("Select Project ID", df['id'])
            new_status = st.selectbox("New Status", ["Not Started", "In Progress", "On Hold", "Completed"])
            if st.button("Update Project Status"):
                update_project_status(pid, new_status)
            if st.button("Delete Project"):
                delete_project(pid)

    elif menu == "Tasks":
        st.title("✅ Tasks")

        with st.expander("➕ Add New Task"):
            dfp = fetch_projects()
            if not dfp.empty:
                pid = st.selectbox("Project", dfp['id'])
                title = st.text_input("Task Title")
                due = st.date_input("Due Date", value=date.today())
                assignee = st.selectbox("Assignee", ["Alice", "Bob", "Charlie", "Dana"])
                status = st.selectbox("Status", ["To Do", "In Progress", "Blocked", "Completed"])
                if st.button("Add Task"):
                    add_task(pid, title, due, assignee, status)

        dft = fetch_tasks()
        if not dft.empty:
            st.dataframe(dft[['id', 'project_id', 'title', 'due_date', 'status']])
            tid = st.selectbox("Select Task ID", dft['id'])
            tstat = st.selectbox("Update Status", ["To Do", "In Progress", "Blocked", "Completed"])
            if st.button("Update Task"):
                update_task(tid, "status", tstat)
