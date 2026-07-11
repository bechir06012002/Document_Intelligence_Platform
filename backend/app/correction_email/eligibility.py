from app.pipeline.validate import ValidationIssue

# Findings that are Delta's own internal determination, not a defect on the
# supplier's document, and therefore not something to ask the supplier to fix.
NOT_SUPPLIER_FIXABLE = frozenset({"duplicate_invoice", "low_extraction_confidence"})


def eligible_issues(issues: list[ValidationIssue]) -> list[ValidationIssue]:
    return [issue for issue in issues if issue.code not in NOT_SUPPLIER_FIXABLE]
