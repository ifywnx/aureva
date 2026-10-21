"""Simple, testable money rules shared by the public dashboard and approvals.

IMPORTANT: "raised" means manually reconciled donations, not bank transfers
verified by AUREVA. "spent" means approved allocations, not paid-out money.
"""
from collections.abc import Iterable, Mapping
from typing import Any


def confirmed_totals(campaigns: Iterable[Mapping[str, Any]]) -> dict[str, int]:
    """Add figures already aggregated per campaign by the database.

    The SQL campaign query includes only confirmed donations and approved
    expenses. This function does not change their statuses or access rights.
    """
    totals = {"raised": 0, "spent": 0, "contribution_count": 0}
    for campaign in campaigns:
        for field in totals:
            totals[field] += int(campaign[field])
    return totals


def available_to_approve(db: Any, campaign_id: str) -> int:
    """How much of the confirmed ledger has NOT yet been allocated.

    Keep the SQL parameterized (the two '?' markers) on SQLite and PostgreSQL.
    This check runs INSIDE the same write transaction as approving an expense.
    """
    row = db.execute(
        """SELECT
            COALESCE((SELECT SUM(amount) FROM donations
                      WHERE campaign_id=? AND status='confirmed'), 0)
          - COALESCE((SELECT SUM(amount) FROM expenses
                      WHERE campaign_id=? AND status='approved'), 0)""",
        (campaign_id, campaign_id),
    ).fetchone()
    return int(row[0])
