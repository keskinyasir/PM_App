import streamlit as st
import pandas as pd
from datetime import datetime

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'projects' not in st.session_state:
    st.session_state['projects'] = []

def login():
    st.title("Project Management Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        # Örnek kullanıcı bilgileri: admin@example.com / password123
        if email == "admin@example.com" and password == "password123":
            st.session_state['logged_in'] = True
            st.experimental_rerun()
        else:
            st.error("Invalid email or password")

def logout():
    if st.button("Logout"):
        st.session_state['logged_in'] = False
        st.experimental_rerun()

def main_app():
    st.sidebar.title("Navigation")
    if st.sidebar.button("Logout"):
        logout()

    st.title("📊 Project Dashboard")

    # Yeni proje ekleme formu
    with st.expander("➕ Add New Project", expanded=True):
        name = st.text_input("Project Name", key="name_input")
        desc = st.text_area("Description", key="desc_input")
        start_date = st.date_input("Start Date", key="start_input")
        end_date = st.date_input("End Date", key="end_input")
        status = st.selectbox("Status", ["Not Started", "In Progress", "Completed"], key="status_input")
        if st.button("Add Project", key="add_project"):
            st.session_state['projects'].append({
                "Name": name,
                "Description": desc,
                "Start Date": start_date,
                "End Date": end_date,
                "Status": status
            })
            st.success("Project added successfully!")

    # Projeleri görüntüleme
    if st.session_state['projects']:
        df = pd.DataFrame(st.session_state['projects'])
        st.write("## Active Projects")
        st.table(df)

        # Özet metrikler
        st.write("## Project Summary")
        status_counts = df['Status'].value_counts()
        cols = st.columns(3)
        statuses = ["Not Started", "In Progress", "Completed"]
        for i, stat in enumerate(statuses):
            cols[i].metric(stat, int(status_counts.get(stat, 0)))

        # Durum dağılım grafiği
        st.bar_chart(status_counts)
    else:
        st.info("No projects yet. Add one using the form above.")

# Uygulama akışı
if not st.session_state['logged_in']:
    login()
else:
    main_app()
