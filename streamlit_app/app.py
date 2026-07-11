import streamlit as st

st.set_page_config(page_title="Delta Document Review", layout="wide")

upload_page = st.Page("pages/upload.py", title="Upload", icon=":material/upload_file:")
inbox_page = st.Page("pages/inbox.py", title="Inbox", icon=":material/inbox:")
review_page = st.Page("pages/review.py", title="Review", icon=":material/fact_check:")

pg = st.navigation([upload_page, inbox_page, review_page])
pg.run()
