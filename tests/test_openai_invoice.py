"""Contract tests for real OpenAI Responses payloads; no paid calls in CI."""
import base64
import io

import httpx
import pytest
from fastapi import HTTPException
from PIL import Image

from backend import evidence


def picture():
    buf=io.BytesIO()
    Image.new('RGB',(90,50),'white').save(buf,format='PNG')
    return buf.getvalue()


def test_openai_missing_key_does_not_fake_extraction(monkeypatch):
    monkeypatch.delenv('OPENAI_API_KEY',raising=False)
    with pytest.raises(HTTPException) as error:
        evidence.extract_invoice(picture(),'image/png')
    assert error.value.status_code==503


@pytest.mark.parametrize('mime,raw',[
    ('image/png',picture()),
    ('application/pdf',b'%PDF-1.4\nunit test only')
])
def test_openai_invoice_payload_is_actual_binary_and_strict_json(monkeypatch,mime,raw):
    monkeypatch.setenv('OPENAI_API_KEY','unit-test-secret')
    monkeypatch.setenv('OPENAI_MODEL','gpt-5-mini')
    captures=[]
    class MockResponse:
        status_code=200
        def json(self):
            return {
                'status':'completed',
                'output':[{'type':'message','content':[{
                    'type':'output_text','text':'{"vendor":"Nha A","invoice_number":"HD-01","date":"2026-10-20","currency":"VND","total":450000,"readable":true,"notes":"Đã đọc rõ"}'
                }]}]
            }
    def mock_post(url,*,headers,json,timeout):
        captures.append({'url':url,'headers':headers,'json':json,'timeout':timeout})
        return MockResponse()
    monkeypatch.setattr(evidence.httpx,'post',mock_post)
    fields,model=evidence.extract_invoice(raw,mime)
    assert model=='gpt-5-mini'
    assert fields['total']==450000 and fields['readable']
    assert len(captures)==1
    p=captures[0]
    assert p['url']=='https://api.openai.com/v1/responses'
    assert p['json']['model']=='gpt-5-mini'
    assert p['json']['store'] is False
    assert p['json']['text']['format']['strict'] is True
    assert p['json']['text']['format']['schema']['additionalProperties'] is False
    parts=p['json']['input'][0]['content']
    assert parts[0]['type']=='input_text'
    data=parts[1]['file_data'] if mime=='application/pdf' else parts[1]['image_url']
    assert data.startswith('data:'+mime+';base64,')
    assert base64.b64decode(data.split(',',1)[1])==raw
    assert parts[1]['type']==('input_file' if mime=='application/pdf' else 'input_image')
    assert p['headers']['Authorization']=='Bearer unit-test-secret'


def test_openai_api_failure_and_invalid_output(monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY','unit-test-secret')
    class ErrorResponse:
        status_code=429
        def json(self):
            return {'error':{'message':'sensitive secret'}}
    monkeypatch.setattr(evidence.httpx,'post',lambda *a,**k:ErrorResponse())
    with pytest.raises(HTTPException) as error:
        evidence.extract_invoice(picture(),'image/png')
    assert error.value.status_code==502
    assert 'sensitive secret' not in error.value.detail
    class InvalidResponse:
        status_code=200
        def json(self):
            return {'status':'completed','output':[{'type':'message','content':[{'type':'output_text','text':'invalid'}]}]}
    monkeypatch.setattr(evidence.httpx,'post',lambda *a,**k:InvalidResponse())
    with pytest.raises(HTTPException) as error:
        evidence.extract_invoice(picture(),'image/png')
    assert error.value.status_code==502


def test_openai_api_timeout_is_safe(monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY','unit-test-secret')
    def timeout(*args,**kwargs):
        raise httpx.ReadTimeout('request body is private')
    monkeypatch.setattr(evidence.httpx,'post',timeout)
    with pytest.raises(HTTPException) as error:
        evidence.extract_invoice(picture(),'image/png')
    assert error.value.status_code==502
    assert 'private' not in error.value.detail
