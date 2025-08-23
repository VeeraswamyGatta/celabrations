# Global DB type switch variable for cross-module import
import streamlit as st
switch_db_type = st.secrets.get("db_type", "postgres")
# This file marks the app directory as a Python package.
