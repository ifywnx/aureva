"""Contract-bound MetaMask attestation checks; never use real private keys or RPC in CI."""
import json
from pathlib import Path
from types import SimpleNamespace
from web3 import Web3
from web3.exceptions import TransactionNotFound

from tests.test_flows import env,client,campaign
from backend import chain

OWNER='0x4f1D550E4c63a5F81422caDa06aEC0452bcE2ef1'
CONTRACT='0x3789555776368073f111e0ba9b20ee7a627b457e'
TX='0x'+'a'*64


class FakeFunctions:
    def recordedAt(self,digest):
        return SimpleNamespace(call=lambda:0)


class FakeEth:
    def __init__(self, tx=None, receipt=None):
        self.tx=tx
        self.receipt=receipt
        self.block_number=100
    def get_transaction(self,hash):
        if not self.tx:raise TransactionNotFound(hash)
        return self.tx
    def get_transaction_receipt(self,hash):
        if self.receipt is None:raise TransactionNotFound(hash)
        return self.receipt


def fake_chain(digest,from_address=OWNER,tx_to=CONTRACT):
    artifact=json.loads((Path(__file__).resolve().parents[1]/'blockchain/artifact.json').read_text())
    real=Web3().eth.contract(address=Web3.to_checksum_address(CONTRACT),abi=artifact['abi'])
    data=real.encode_abi('record',args=[bytes.fromhex(digest)])
    contract=SimpleNamespace(address=CONTRACT,encode_abi=real.encode_abi,
                             decode_function_input=real.decode_function_input,
                             functions=FakeFunctions())
    transaction={'to':tx_to,'from':from_address,'input':data,'chainId':11155111,'value':0}
    return SimpleNamespace(eth=FakeEth(transaction)),contract,OWNER


def sample_report(manager):
    cid=campaign(manager)
    r=manager.post(f'/api/campaigns/{cid}/reports',json={})
    assert r.status_code==201,r.text
    return r.json()['id']


def test_wallet_prepare_requires_role_and_digest_integrity(env,monkeypatch):
    m,d=client('manager'),client('donor')
    rid=sample_report(m)
    att=m.get('/api/public/attestations/'+rid).json()
    monkeypatch.setattr(chain,'read_client',lambda:fake_chain(att['digest']))
    assert d.post('/api/attestations/'+rid+'/prepare-wallet',json={}).status_code==403
    prepared=m.post('/api/attestations/'+rid+'/prepare-wallet',json={})
    assert prepared.status_code==200,prepared.text
    data=prepared.json()
    assert data['owner']==OWNER and data['contract']==CONTRACT
    assert data['chain_id']==11155111
    assert data['data'].startswith('0x')
    assert data['digest']==att['digest']


def test_wallet_rejects_wrong_signer_or_digest_and_accepts_valid_receipt(env,monkeypatch):
    m=client('manager')
    rid=sample_report(m)
    digest=m.get('/api/public/attestations/'+rid).json()['digest']
    fake=fake_chain(digest,from_address='0x'+'0'*40)
    monkeypatch.setattr(chain,'read_client',lambda:fake)
    wrong=m.post('/api/attestations/'+rid+'/submit-wallet',json={'tx_hash':TX})
    assert wrong.status_code==409,wrong.text
    fake=fake_chain(digest)
    monkeypatch.setattr(chain,'read_client',lambda:fake)
    good=m.post('/api/attestations/'+rid+'/submit-wallet',json={'tx_hash':TX})
    assert good.status_code==200,good.text
    assert good.json()['status']=='submitted'
    # A tx hash cannot be switched to a different transaction once stored.
    assert m.post('/api/attestations/'+rid+'/submit-wallet',
                  json={'tx_hash':'0x'+'b'*64}).status_code==409
    # After enough blocks and the digest actually on chain: confirmed.
    fake[0].eth.receipt=SimpleNamespace(status=1,blockNumber=96)
    fake[1].functions.recordedAt=lambda h:SimpleNamespace(call=lambda:17200000)
    confirmed=m.post('/api/attestations/'+rid+'/submit-wallet',json={'tx_hash':TX})
    assert confirmed.status_code==200,confirmed.text
    assert confirmed.json()['status']=='confirmed'
    public=m.get('/api/public/attestations/'+rid).json()
    assert public['status']=='confirmed' and public['tx_hash']==TX


def test_wallet_rejects_fake_tx_hash_and_wrong_contract(env,monkeypatch):
    m=client('manager')
    rid=sample_report(m)
    digest=m.get('/api/public/attestations/'+rid).json()['digest']
    fake=fake_chain(digest,tx_to='0x'+'1'*40)
    monkeypatch.setattr(chain,'read_client',lambda:fake)
    assert m.post('/api/attestations/'+rid+'/submit-wallet',
                  json={'tx_hash':'garbage'}).status_code==422
    assert m.post('/api/attestations/'+rid+'/submit-wallet',
                  json={'tx_hash':TX}).status_code==409
