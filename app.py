import streamlit as st
import requests
from requests.auth import HTTPBasicAuth
import os
import pandas as pd
import matplotlib.pyplot as plt

# -------------------------
# Config
# -------------------------
API_BASE = "https://dev.gcp.csye7125.xyz"  # Go backend
LLM_API_URL = os.getenv("API_URL", API_BASE)  # AI features behind same or different endpoint

# -------------------------
# Page Setup
# -------------------------
st.set_page_config(page_title="Course Feedback Assistant", layout="wide")
st.title("🎓 Course Feedback Explorer")

# -------------------------
# Session State
# -------------------------
if "is_authenticated" not in st.session_state:
    st.session_state.is_authenticated = False
if "auth_user" not in st.session_state:
    st.session_state.auth_user = None

# -------------------------
# Health Check
# -------------------------
with st.expander("🔍 Check Backend Health", expanded=False):
    if st.button("Check Health"):
        try:
            res = requests.get(f"{API_BASE}/healthz", timeout=5)
            if res.status_code == 200:
                st.success("✅ Backend is healthy")
            else:
                st.error(f"❌ Backend check failed: {res.text}")
        except Exception as e:
            st.error(f"Error: {e}")

# -------------------------
# User Authentication
# -------------------------
st.sidebar.header("👤 Login or Register")

with st.sidebar.form("login_form"):
    login_username = st.text_input("Username", key="login_user")
    login_password = st.text_input("Password", type="password", key="login_pass")
    login_btn = st.form_submit_button("Login")

if login_btn:
    try:
        res = requests.get(f"{API_BASE}/v1/user", auth=HTTPBasicAuth(login_username, login_password), timeout=5)
        if res.status_code == 200:
            st.session_state.is_authenticated = True
            st.session_state.auth_user = login_username
            st.sidebar.success("Logged in successfully!")
        else:
            st.sidebar.error("Invalid credentials.")
    except Exception as e:
        st.sidebar.error(f"Login error: {e}")

# -------------------------
# Protected Section
# -------------------------
if st.session_state.is_authenticated:
    st.success(f"🔐 Logged in as {st.session_state.auth_user}")

    mode = st.sidebar.selectbox(
        "Choose Action", [
            "Chat with Feedback",
            "📊 Sentiment Trend by Year"
        ]
    )

    # --- Chat with LLM ---
    if mode == "Chat with Feedback":
        st.subheader("🤖 Ask a question about course feedback")

        # Show LinkedIn hashtag tip
        default_course = "CSYE6225"
        hashtag_url = f"https://www.linkedin.com/search/results/all/?keywords=%23{default_course.lower()}&origin=HISTORY"
        st.markdown(f"🔍 Want to explore social media buzz? Check [LinkedIn posts for #{default_course}]({hashtag_url})")

        user_input = st.text_input("Type your question:", placeholder="e.g. What are the top complaints about CSYE6225?")
        if st.button("Ask") and user_input:
            try:
                response = requests.post(f"{LLM_API_URL}/ask", json={"question": user_input})
                st.code(response.text, language='json')
                data = response.json()
                answer = data.get("answer", "No answer found.")
                st.success(answer)
            except Exception as e:
                st.error(f"Error: {e}")

    # --- Sentiment Trend by Year ---
    elif mode == "📊 Sentiment Trend by Year":
        st.subheader("📈 Average Sentiment by Year")
        years = st.multiselect("Select years to analyze:", options=[2021, 2022, 2023, 2024], default=[2021, 2022, 2023, 2024])

        if st.button("Get Sentiment Data"):
            if not years:
                st.warning("Please select at least one year.")
            else:
                with st.spinner("Fetching sentiment data..."):
                    try:
                        response = requests.post(f"{LLM_API_URL}/sentiment", json={"years": years})
                        response.raise_for_status()
                        data = response.json()

                        df = pd.DataFrame.from_dict(data, orient="index")
                        df.index.name = "Year"
                        df = df.sort_index()

                        st.subheader("📈 Average Positive Sentiment by Year")
                        st.bar_chart(df["avg_positive"])

                        st.subheader("📉 Average Negative Sentiment by Year")
                        st.bar_chart(df["avg_negative"])

                        st.subheader("🧾 Number of Entries Used")
                        st.table(df["count"])

                    except requests.RequestException as e:
                        st.error(f"Request failed: {e}")
else:
    st.warning("🔒 Please log in to use feedback features.")
