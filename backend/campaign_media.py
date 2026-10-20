"""Persisted campaign cover images. Images are normalized and stored in the database.

No local disk or external image host is used for uploaded covers; this works on
stateless Vercel/Railway workers, and restart persistence follows PostgreSQL/SQLite.
"""
import hashlib
import io
import sqlite3

from fastapi import Depends, File, HTTPException, UploadFile
from fastapi.responses import Response
from PIL import Image, ImageOps, UnidentifiedImageError

MAX_UPLOAD = 2_000_000
MAX_PIXELS = 14_000_000
MAX_COVER = 900_000


def init_sqlite(db):
    db.execute('''
        CREATE TABLE IF NOT EXISTS campaign_covers(
          campaign_id TEXT PRIMARY KEY REFERENCES campaigns(id) ON DELETE CASCADE,
          content BLOB NOT NULL,
          sha256 TEXT NOT NULL,
          updated TEXT NOT NULL
        )
    ''')


def normalize_cover(raw: bytes) -> bytes:
    if len(raw) > MAX_UPLOAD:
        raise HTTPException(413, 'Ảnh quá lớn. Vui lòng chọn ảnh không quá 2 MB.')
    if not raw:
        raise HTTPException(422, 'Vui lòng chọn ảnh bìa hợp lệ.')
    try:
        with Image.open(io.BytesIO(raw)) as input_image:
            if input_image.format not in ('JPEG', 'PNG', 'WEBP'):
                raise HTTPException(422, 'Chỉ hỗ trợ ảnh JPG, PNG hoặc WebP.')
            if input_image.width * input_image.height > MAX_PIXELS:
                raise HTTPException(413, 'Độ phân giải ảnh quá lớn.')
            image = ImageOps.exif_transpose(input_image)
            image.thumbnail((1600, 1200), Image.Resampling.LANCZOS)
            image = image.convert('RGB')
            output = io.BytesIO()
            image.save(output, format='WEBP', quality=82, method=5)
            data = output.getvalue()
            if len(data) > MAX_COVER:
                raise HTTPException(413, 'Ảnh sau tối ưu vẫn quá lớn, vui lòng chọn ảnh khác.')
            return data
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
        raise HTTPException(422, 'File không phải ảnh hợp lệ hoặc đã bị hỏng.')


def register(app):
    from backend.app import campaign_access, connect, current_user, require, audit, now

    @app.post('/api/campaigns/{campaign_id}/cover', status_code=200)
    async def upload_campaign_cover(campaign_id: str, file: UploadFile = File(...), user=Depends(current_user)):
        require(user, 'manager')
        with connect() as db:
            campaign_access(db, campaign_id, user)
        if file.content_type not in ('image/jpeg', 'image/png', 'image/webp'):
            raise HTTPException(422, 'Định dạng phải là JPG, PNG hoặc WebP.')
        raw = await file.read(MAX_UPLOAD + 1)
        content = normalize_cover(raw)
        sha256 = hashlib.sha256(content).hexdigest()
        with connect(write=True) as db:
            campaign_access(db, campaign_id, user)
            db.execute('''
                INSERT INTO campaign_covers(campaign_id,content,sha256,updated) VALUES(?,?,?,?)
                ON CONFLICT(campaign_id) DO UPDATE SET
                    content=excluded.content,sha256=excluded.sha256,updated=excluded.updated
            ''', (campaign_id, content, sha256, now()))
            audit(db, user, 'campaign.cover.updated', campaign_id, {'sha256': sha256})
        return {'ok': True, 'cover_url': f'/api/public/campaigns/{campaign_id}/cover?v={sha256[:12]}', 'sha256': sha256}

    @app.get('/api/public/campaigns/{campaign_id}/cover')
    def campaign_cover(campaign_id: str):
        with connect() as db:
            cover = db.execute('SELECT content,sha256 FROM campaign_covers WHERE campaign_id=?', (campaign_id,)).fetchone()
        if not cover:
            raise HTTPException(404, 'Chiến dịch chưa có ảnh bìa.')
        return Response(bytes(cover['content']), media_type='image/webp',
                        headers={'ETag': '"' + cover['sha256'] + '"', 'X-Content-Type-Options': 'nosniff'})
