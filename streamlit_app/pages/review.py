import streamlit as st

from lib.api import (
    ApiError,
    correct_document,
    decide_document,
    draft_correction_email,
    get_document,
    get_document_file,
    list_gl_accounts,
    select_gl_account,
)

INVOICE_FIELD_LABELS = [
    ("vendor_name", "Vendor name"),
    ("vendor_vat_id", "Vendor VAT ID"),
    ("customer_name", "Customer name"),
    ("customer_vat_id", "Customer VAT ID"),
    ("invoice_number", "Invoice number"),
    ("purchase_order", "Purchase order"),
    ("invoice_date", "Invoice date"),
    ("due_date", "Due date"),
    ("currency", "Currency"),
    ("subtotal", "Subtotal"),
    ("total_tax", "Tax"),
    ("invoice_total", "Total"),
]

RECEIPT_FIELD_LABELS = [
    ("merchant_name", "Merchant name"),
    ("transaction_date", "Transaction date"),
    ("currency", "Currency"),
    ("subtotal", "Subtotal"),
    ("total_tax", "VAT"),
    ("total", "Total"),
]

STATUS_LABELS = {
    "processing": "Processing",
    "needs_review": "Needs review",
    "approved": "Approved",
    "rejected": "Rejected",
    "failed": "Failed",
}


@st.dialog("Correction email")
def _show_correction_email(document_id: int) -> None:
    try:
        draft = draft_correction_email(document_id)
    except ApiError as exc:
        st.error(f"Could not draft an email: {exc.detail}")
        return

    st.text_input("Subject", value=draft.subject, key="correction-email-subject")
    st.text_area("Body", value=draft.body, height=240, key="correction-email-body")
    st.caption("Copy the text above — sending is not part of this app.")
    if st.button("Close"):
        st.rerun()


document_id = st.session_state.get("selected_document_id")

if document_id is None:
    st.info("No document selected. Go to Upload or Inbox to pick one.")
    st.stop()

try:
    document = get_document(document_id)
except ApiError as exc:
    st.error(f"Could not load document: {exc.detail}")
    st.stop()

st.title(document.original_filename)
st.caption(f"Status: {STATUS_LABELS.get(document.status, document.status)}")

is_locked = document.status in ("approved", "rejected")

col_preview, col_fields = st.columns([1, 2])

with col_preview:
    st.subheader("Original document")
    try:
        file_bytes = get_document_file(document.id)
    except ApiError as exc:
        st.warning(f"Could not load original file: {exc.detail}")
    else:
        if document.content_type.startswith("image/"):
            st.image(file_bytes, use_container_width=True)
        else:
            st.download_button(
                "Open original PDF",
                data=file_bytes,
                file_name=document.original_filename,
                mime=document.content_type,
            )

with col_fields:
    st.subheader("Extracted fields")
    fields = document.fields or {}
    field_labels = (
        INVOICE_FIELD_LABELS if document.document_type == "invoice" else RECEIPT_FIELD_LABELS
    )

    with st.form("fields-form"):
        values = {}
        for key, label in field_labels:
            current = fields.get(key)
            values[key] = st.text_input(
                label, value="" if current is None else str(current), disabled=is_locked
            )
        submitted = st.form_submit_button("Save corrections", disabled=is_locked)

    if submitted:
        updates = {
            key: value
            for key, value in values.items()
            if value != ("" if fields.get(key) is None else str(fields.get(key)))
        }
        if updates:
            try:
                document = correct_document(document.id, updates)
            except ApiError as exc:
                st.error(f"Could not save corrections: {exc.detail}")
            else:
                st.toast("Corrections saved.", icon="✅")
                st.rerun()
        else:
            st.info("No changes to save.")

st.divider()
st.subheader("Validation")
if not document.validation.issues:
    st.success("No issues found.")
for issue in document.validation.issues:
    if issue.severity == "error":
        st.error(issue.message)
    else:
        st.warning(issue.message)

st.divider()
st.subheader("GL account")
if document.gl_classification:
    st.caption(
        f"Suggested: {document.gl_classification.account} — "
        f"{document.gl_classification.rationale}"
    )

try:
    gl_accounts = list_gl_accounts()
except ApiError as exc:
    st.error(f"Could not load GL accounts: {exc.detail}")
    gl_accounts = []

current_code = document.selected_gl_account_code or (
    document.gl_classification.account if document.gl_classification else None
)
default_index = gl_accounts.index(current_code) if current_code in gl_accounts else None

selected_account = st.selectbox(
    "Select GL account",
    options=gl_accounts,
    index=default_index,
    placeholder="Choose an account...",
    disabled=is_locked,
)

if st.button("Save GL account", disabled=is_locked or not selected_account):
    try:
        document = select_gl_account(document.id, selected_account)
    except ApiError as exc:
        st.error(f"Could not save GL account: {exc.detail}")
    else:
        st.toast("GL account saved.", icon="✅")
        st.rerun()

st.divider()
st.subheader("Decision")

approval_blocked_reasons = []
if not document.validation.is_valid:
    approval_blocked_reasons.append("open validation errors")
if not document.selected_gl_account_code:
    approval_blocked_reasons.append("no GL account selected")

col_approve, col_reject, col_email = st.columns(3)

with col_approve:
    approve_help = (
        f"Blocked: {', '.join(approval_blocked_reasons)}." if approval_blocked_reasons else None
    )
    if st.button(
        "Approve",
        type="primary",
        disabled=is_locked or bool(approval_blocked_reasons),
        help=approve_help,
    ):
        try:
            document = decide_document(document.id, "approve")
        except ApiError as exc:
            st.error(f"Could not approve: {exc.detail}")
        else:
            st.toast("Approved.", icon="✅")
            st.rerun()

with col_reject:
    if st.button("Reject", disabled=is_locked):
        try:
            document = decide_document(document.id, "reject")
        except ApiError as exc:
            st.error(f"Could not reject: {exc.detail}")
        else:
            st.toast("Rejected.", icon="✅")
            st.rerun()

with col_email:
    if st.button("Draft correction email"):
        _show_correction_email(document.id)
