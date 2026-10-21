"""Viva-friendly tests for ledger rules; do not connect to live databases."""
from decimal import Decimal
from pydantic import ValidationError
import pytest

from backend.app import CampaignInput, DonationInput, ExpenseInput, Decision
from backend.finance import available_to_approve, confirmed_totals


def test_dashboard_totals_are_only_database_confirmed_figures():
    """The dashboard SQL already removes pending/rejected records."""
    campaigns = [
        {'raised': Decimal('1000000'), 'spent': Decimal('300000'), 'contribution_count': 2},
        {'raised': 500000, 'spent': 0, 'contribution_count': 1},
    ]
    assert confirmed_totals(campaigns) == {
        'raised': 1500000, 'spent': 300000, 'contribution_count': 3
    }
    assert confirmed_totals([]) == {'raised': 0, 'spent': 0, 'contribution_count': 0}


class RecordingCursor:
    def __init__(self, value):
        self.value = value

    def fetchone(self):
        return (self.value,)


class RecordingDatabase:
    def __init__(self, value):
        self.value = value
        self.statements = []

    def execute(self, sql, params):
        self.statements.append((sql, params))
        return RecordingCursor(self.value)


def test_approver_balance_query_uses_bound_campaign_id():
    """A fake database confirms that campaign ID is passed as parameters."""
    db = RecordingDatabase(700000)
    campaign_id = 'campaign-123'
    assert available_to_approve(db, campaign_id) == 700000
    sql, parameters = db.statements[0]
    assert parameters == (campaign_id, campaign_id)
    assert campaign_id not in sql
    assert sql.count('?') == 2
    assert "status='confirmed'" in sql
    assert "status='approved'" in sql


@pytest.mark.parametrize('amount', [0, -10, 1.5, '5000', 1_000_000_000_001])
def test_invalid_donation_amount_is_rejected(amount):
    with pytest.raises(ValidationError):
        DonationInput(amount=amount, reference='REF-OK')


def test_valid_donation_requires_no_bank_connection():
    data = DonationInput(amount=250000, reference='REF-TEST')
    assert data.amount == 250000


def test_campaign_and_expense_fields_have_validation():
    with pytest.raises(ValidationError):
        CampaignInput(title='abc', description='Mô tả đủ dài', location='HN', target=1000)
    with pytest.raises(ValidationError):
        ExpenseInput(amount=50000, purpose='Chi', vendor='Cửa hàng')


def test_approver_cannot_choose_an_unknown_status():
    with pytest.raises(ValidationError):
        Decision(status='paid_out', reason='Đã xem chứng từ')
    assert Decision(status='rejected', reason='Chứng từ chưa hợp lệ').status == 'rejected'
