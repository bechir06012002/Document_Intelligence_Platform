import streamlit as st

from lib.api import ApiError, delete_document, list_documents

STATUS_ICONS = {
    "processing": "🔄",
    "needs_review": "🟡",
    "approved": "✅",
    "rejected": "⛔",
    "failed": "❌",
}


@st.dialog("Delete document?")
def _confirm_delete(document_id: int) -> None:
    st.write(f"Delete document #{document_id}? This cannot be undone.")
    col_cancel, col_confirm = st.columns(2)
    with col_cancel:
        if st.button("Cancel", use_container_width=True):
            st.session_state["pending_delete_id"] = None
            st.rerun()
    with col_confirm:
        if st.button("Delete", type="primary", use_container_width=True):
            try:
                delete_document(document_id)
            except ApiError as exc:
                st.error(f"Delete failed: {exc.detail}")
            else:
                st.session_state["pending_delete_id"] = None
                st.rerun()


st.title("Document history")

try:
    documents = list_documents()
except ApiError as exc:
    st.error(f"Could not load documents: {exc.detail}")
    documents = []

if not documents:
    st.info("No documents yet. Upload one to get started.")

for document in documents:
    col_info, col_open, col_delete = st.columns([6, 1, 1])
    icon = STATUS_ICONS.get(document.status, "•")
    label = document.vendor_or_merchant_name or document.original_filename
    amount = f"{document.currency} {document.total}" if document.total else ""

    with col_info:
        st.write(f"{icon} **{label}** — {document.document_type or 'unclassified'} — {amount}")
        st.caption(
            f"#{document.id} · {document.original_filename} · "
            f"{document.status} · {document.created_at}"
        )
    with col_open:
        if st.button("Open", key=f"open-{document.id}"):
            st.session_state["selected_document_id"] = document.id
            st.switch_page("pages/review.py")
    with col_delete:
        if st.button("Delete", key=f"delete-{document.id}"):
            st.session_state["pending_delete_id"] = document.id

pending_delete_id = st.session_state.get("pending_delete_id")
if pending_delete_id is not None:
    _confirm_delete(pending_delete_id)
