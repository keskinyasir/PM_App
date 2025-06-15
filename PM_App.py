import streamlit as st
import pandas as pd
from datetime import datetime, date
from supabase import create_client, Client

# --- Supabase Setup ---
SUPABASE_URL = "https://sxpjijtxiqhxzgyxpgtm.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InN4cGppanR4aXFoeHpneXhwZ3RtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTAwMTExMzAsImV4cCI6MjA2NTU4NzEzMH0.N_Ud7Pc83W5mf1yYYsJ8NzfQr_AeEkrGYT_CDFt0LB8"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Authentication ---
def authenticate(email, pwd):
    return email == 'admin@example.com' and pwd == 'password123'

def login_page():
    st.title('Login')
    email = st.text_input('Email', key='login_email')
    pwd = st.text_input('Password', type='password', key='login_password')
    login_clicked = st.button('Login')

    if login_clicked:
        if authenticate(email, pwd):
            st.session_state['logged_in'] = True
            st.session_state['user'] = email
            st.success(f"Welcome, {email}!")
        else:
            st.error('Invalid credentials')

# --- Supabase Helpers ---
def fetch_projects():
    try:
        response = supabase.table("projects").select("*").execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Failed to fetch projects: {e}")
        return pd.DataFrame()

def fetch_tasks():
    try:
        response = supabase.table("tasks").select("*").execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Failed to fetch tasks: {e}")
        return pd.DataFrame()

def add_project(name, desc, start, end, members):
    try:
        response = supabase.table("projects").insert({
            "name": name,
            "description": desc,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "status": "Not Started",
            "members": members,
            "created_by": st.session_state['user'],
            "created_at": datetime.now().isoformat()
        }).execute()
        st.success(f"Project '{name}' added")
    except Exception as e:
        st.error(f"Error adding project: {e}")

def delete_project(pid):
    try:
        supabase.table("tasks").delete().eq("project_id", pid).execute()
        supabase.table("projects").delete().eq("id", pid).execute()
        st.success(f"Project {pid} deleted")
    except Exception as e:
        st.error(f"Failed to delete project {pid}: {e}")

def update_project_status(pid, status):
    try:
        supabase.table("projects").update({"status": status}).eq("id", pid).execute()
        st.success(f"Project {pid} updated to {status}")
    except Exception as e:
        st.error(f"Failed to update project status: {e}")

def add_task(pid, title, due, assignee, status):
    try:
        supabase.table("tasks").insert({
            "project_id": pid,
            "title": title,
            "due_date": due.isoformat(),
            "assignee": assignee,
            "status": status,
            "created_at": datetime.now().isoformat()
        }).execute()
        st.success(f"Task '{title}' added to project {pid}")
    except Exception as e:
        st.error(f"Failed to add task: {e}")

def update_task(task_id, field, value):
    if field not in ['title', 'due_date', 'assignee', 'status']:
        st.error(f"Field '{field}' is not allowed to update")
        return
    try:
        supabase.table("tasks").update({field: value}).eq("id", task_id).execute()
        st.success(f"Task {task_id} updated: {field} → {value}")
    except Exception as e:
        st.error(f"Failed to update task: {e}")
