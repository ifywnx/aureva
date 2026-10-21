import io
import json

import pytest
from fastapi import HTTPException
from pypdf import PdfWriter

from backend import assistant, evidence


class FakeResponse:
    def __init__(self, data, status_code=200):
        self._data = data
        self.status_code = status_code

    def json(self):
        return self._data


def mirai_env(monkeypatch):
    monkeypatch.setenv('AI_BASE_URL', 'https://api.miraiapi.com/v1')
    monkeypatch.setenv('OPENAI_MODEL', 'claude-opus-4.8')
    monkeypatch.setenv('OPENAI_API_KEY', 'sk-test-only-not-a-real-key')


def test_mirai_chat_uses_completions_and_public_data_only(monkeypatch):
    mirai_env(monkeypatch)
    calls = []

    def respond(url, **kwargs):
        calls.append((url, kwargs))
        return FakeResponse({'choices': [{'message': {'content': 'Xin chào từ AUREVA'}}]})

    monkeypatch.setattr(assistant.httpx, 'post', respond)
    text, model = assistant.call_openai('Chào bạn', [], {'count': 0, 'campaigns': []})
    assert text == 'Xin chào từ AUREVA'
    assert model == 'claude-opus-4.8'
    url, options = calls[0]
    assert url == 'https://api.miraiapi.com/v1/chat/completions'
    assert options['json']['messages'][0]['role'] == 'system'
    assert json.loads(options['json']['messages'][1]['content'])['PUBLIC_SNAPSHOT']['count'] == 0
    assert 'store' not in options['json']
    assert 'sk-test-only-not-a-real-key' not in json.dumps(options['json'])


def test_mirai_chat_rejects_provider_auth_failure(monkeypatch):
    mirai_env(monkeypatch)
    monkeypatch.setattr(assistant.httpx, 'post',
                        lambda url, **kw: FakeResponse({}, 401))
    with pytest.raises(HTTPException) as exc:
        assistant.call_openai('Chào', [], {'count': 0})
    assert exc.value.status_code == 503
    assert 'nhà cung cấp' in exc.value.detail.lower()


def test_mirai_image_invoice_strictly_validated(monkeypatch):
    mirai_env(monkeypatch)
    answer = {'vendor': 'Hiệu gạo', 'invoice_number': 'A-1', 'date': None,
              'currency': 'VND', 'total': 100000, 'readable': True,
              'notes': 'Ảnh tương đối rõ'}
    calls = []

    def respond(url, **kwargs):
        calls.append((url, kwargs))
        return FakeResponse({'choices': [{'message': {'content': json.dumps(answer)}}]})

    monkeypatch.setattr(evidence.httpx, 'post', respond)
    data, model = evidence.extract_invoice(b'fake-test-image', 'image/png')
    assert data == answer
    assert model == 'claude-opus-4.8'
    url, kw = calls[0]
    assert url == 'https://api.miraiapi.com/v1/chat/completions'
    content = kw['json']['messages'][0]['content']
    assert content[0]['type'] == 'text'
    assert content[1]['type'] == 'image_url'
    assert content[1]['image_url']['url'].startswith('data:image/png;base64,')

    answer['total'] = -100
    with pytest.raises(HTTPException):
        evidence.extract_invoice(b'fake-test-image', 'image/png')


def test_mirai_scanned_pdf_is_rejected_without_fabrication(monkeypatch):
    mirai_env(monkeypatch)
    writer = PdfWriter()
    writer.add_blank_page(width=180, height=180)
    output = io.BytesIO()
    writer.write(output)
    with pytest.raises(HTTPException) as exc:
        evidence.extract_invoice(output.getvalue(), 'application/pdf')
    assert exc.value.status_code == 422


def test_invalid_base_url_is_rejected_without_network(monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY', 'sk-test-only-not-a-real-key')
    monkeypatch.setenv('AI_BASE_URL', 'http://127.0.0.1:9999')
    with pytest.raises(HTTPException) as exc:
        assistant.call_openai('Chào', [], {})
    assert exc.value.status_code == 503
    with pytest.raises(HTTPException) as exc:
        evidence.extract_invoice(b'anything', 'image/png')
    assert exc.value.status_code == 503


def test_openai_default_responses_is_unchanged(monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY', 'sk-test-only-not-a-real-key')
    monkeypatch.delenv('AI_BASE_URL', raising=False)
    monkeypatch.delenv('OPENAI_MODEL', raising=False)

    def respond(url, **kw):
        assert url == 'https://api.openai.com/v1/responses'
        assert kw['json']['store'] is False
        return FakeResponse({'status': 'completed', 'output': [
            {'type': 'message', 'content': [
                {'type': 'output_text', 'text': 'Xin chào'}
            ]}
        ]})

    monkeypatch.setattr(assistant.httpx, 'post', respond)
    text, model = assistant.call_openai('Chào bạn', [], {'count': 0})
    assert (text, model) == ('Xin chào', 'gpt-5-mini')
