"""Public audit timeline and financial trend; only confirmed/approved audit events.

Never exposes donor personal data, references, rejected reasons, actor IDs or
document content. Amounts are joined from canonical persisted records.
"""
from fastapi import HTTPException, Query


def register(app):
    from backend.app import connect

    @app.get('/api/public/activity')
    def public_activity(campaign_id: str | None = Query(default=None, max_length=64)):
        with connect() as db:
            if campaign_id and not db.execute('SELECT id FROM campaigns WHERE id=?', (campaign_id,)).fetchone():
                raise HTTPException(404, 'Không tìm thấy chiến dịch.')
            joins = '''FROM audit a
                LEFT JOIN donations d ON d.id=a.entity_id AND a.action='donation.confirmed'
                LEFT JOIN expenses e ON e.id=a.entity_id
                     AND a.action IN ('expense.approved','expense.rejected')
                JOIN campaigns c ON c.id=COALESCE(d.campaign_id,e.campaign_id)
                WHERE a.action IN ('donation.confirmed','expense.approved','expense.rejected')'''
            args = (campaign_id,) if campaign_id else ()
            if campaign_id:
                joins += ' AND c.id=?'
            events = [dict(r) for r in db.execute('''
                SELECT a.id,a.action,a.created AS occurred_at,c.id AS campaign_id,
                       c.title AS campaign_title,COALESCE(d.amount,e.amount) AS amount
                ''' + joins + ' ORDER BY a.created DESC,a.id DESC LIMIT 25', args)]
            trends = [dict(r) for r in db.execute('''
                SELECT substr(a.created,1,10) AS day,
                    COALESCE(SUM(CASE WHEN a.action='donation.confirmed' THEN d.amount ELSE 0 END),0) AS confirmed,
                    COALESCE(SUM(CASE WHEN a.action='expense.approved' THEN e.amount ELSE 0 END),0) AS approved
                ''' + joins + '''
                GROUP BY substr(a.created,1,10)
                ORDER BY day DESC LIMIT 14''',args)]
        return {'events':events, 'trend':list(reversed(trends)),
                'scope':'campaign' if campaign_id else 'all',
                'description':'Tổng hợp theo thời gian ghi nhận quyết định trong nhật ký hệ thống, không phải thời điểm chuyển tiền ngân hàng.'}
