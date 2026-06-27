# app/admin_dashboard.py
import streamlit as st
import psycopg2
import pandas as pd
from datetime import datetime
import os
from configs.settings import settings

st.set_page_config(page_title="Admin Dashboard", layout="wide")
st.title("Admin Dashboard - Enterprise RAG")

# Sync connection for simple Streamlit dashboard
@st.cache_resource
def get_db_connection():
    # Replace asyncpg with psycopg2 for pandas
    conn_str = settings.POSTGRES_URL.replace("postgresql+asyncpg://", "postgresql://")
    return psycopg2.connect(conn_str)

try:
    conn = get_db_connection()
except Exception as e:
    st.error(f"Failed to connect to database: {e}")
    st.stop()

# Feature D: Token Budget Dashboard
st.header("Token Budget Tracker")

try:
    budget_df = pd.read_sql_query("""
        SELECT user_id, date, tokens_used 
        FROM token_budgets 
        WHERE date = CURRENT_DATE
    """, conn)
    
    if not budget_df.empty:
        for _, row in budget_df.iterrows():
            user = row['user_id']
            used = row['tokens_used']
            limit = settings.TOKEN_BUDGET_DAILY
            pct = min((used / limit) * 100, 100)
            
            st.write(f"**User: {user}** ({used:,} / {limit:,} tokens)")
            st.progress(pct / 100.0)
            
            if pct >= 80.0:
                st.toast(f"Alert: {user} reached {pct:.1f}% budget limit!", icon="🚨")
                st.warning(f"⚠️ User {user} is at {pct:.1f}% of their daily token budget!")
    else:
        st.info("No token usage today.")
except Exception as e:
    st.error(f"Could not load budgets: {e}")

st.divider()

st.header("Recent Query Logs")
try:
    logs_df = pd.read_sql_query("""
        SELECT id, user_id, query, intent, latency_ms, tokens_used, cost_usd, error, created_at 
        FROM query_logs 
        ORDER BY created_at DESC LIMIT 50
    """, conn)
    st.dataframe(logs_df, use_container_width=True)
except Exception as e:
    st.error(f"Could not load query logs: {e}")
    
st.divider()

st.header("Pending SQL Approvals")
try:
    approvals_df = pd.read_sql_query("""
        SELECT id, session_id, sql_query, status, created_at 
        FROM sql_approvals 
        WHERE status = 'pending'
    """, conn)
    st.dataframe(approvals_df, use_container_width=True)
    
    # In a real app, provide Approve/Reject buttons that call POST /sql/approve
except Exception as e:
    st.error(f"Could not load SQL approvals: {e}")
