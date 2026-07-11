import streamlit as st

from lib.api import ApiError, upload_document

ALLOWED_EXTENSIONS = ["pdf", "png", "jpg", "jpeg"]
MAX_BYTES = 4 * 1024 * 1024

st.title("Upload a document")
st.caption(
    "Upload a supplier invoice or an employee expense receipt "
    "(PDF, PNG, or JPEG, up to 4 MB)."
)

uploaded_file = st.file_uploader("Choose a file", type=ALLOWED_EXTENSIONS)

if uploaded_file is not None:
    content = uploaded_file.getvalue()

    if len(content) > MAX_BYTES:
        st.error(f"File is {len(content) / 1_048_576:.1f} MB, which exceeds the 4 MB limit.")
    else:
        if uploaded_file.type and uploaded_file.type.startswith("image/"):
            st.image(content, caption=uploaded_file.name, width=400)
        else:
            st.caption(f"Selected: {uploaded_file.name} ({len(content) / 1024:.0f} KB)")

        if st.button("Process document", type="primary"):
            with st.spinner("Extracting, classifying, and validating..."):
                try:
                    document = upload_document(
                        uploaded_file.name,
                        uploaded_file.type or "application/octet-stream",
                        content,
                    )
                except ApiError as exc:
                    st.error(f"Upload failed: {exc.detail}")
                else:
                    st.session_state["selected_document_id"] = document.id
                    st.switch_page("pages/review.py")
