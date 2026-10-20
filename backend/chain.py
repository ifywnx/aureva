"""Sepolia-only durable transaction outbox. No mocked transaction identifiers."""
import json,os
from pathlib import Path
from fastapi import Depends,HTTPException
CHAIN_ID=11155111

def configured():
    return all(os.getenv(k) for k in ('SEPOLIA_RPC_URL','AUREVA_CONTRACT_ADDRESS'))

def read_client():
    if not configured():
        raise HTTPException(503,'Chưa cấu hình RPC và địa chỉ hợp đồng AUREVA.')
    from web3 import Web3
    w3=Web3(Web3.HTTPProvider(os.environ['SEPOLIA_RPC_URL'],request_kwargs={'timeout':15}))
    if w3.eth.chain_id!=CHAIN_ID:
        raise HTTPException(503,'Chỉ cho phép mạng Ethereum Sepolia.')
    address=w3.to_checksum_address(os.environ['AUREVA_CONTRACT_ADDRESS'])
    if not w3.eth.get_code(address):
        raise HTTPException(503,'Không tìm thấy bytecode hợp đồng Sepolia.')
    artifact=json.loads((Path(__file__).resolve().parents[1]/'blockchain/artifact.json').read_text())
    contract=w3.eth.contract(address=address,abi=artifact['abi'])
    owner=contract.functions.owner().call()
    return w3,contract,owner

def client():
    """Legacy server signing, only available with an explicit test wallet secret."""
    if not os.getenv('BLOCKCHAIN_PRIVATE_KEY'):
        raise HTTPException(503,'Không có ví ký trên server. Hãy ký bằng MetaMask.')
    w3,contract,owner=read_client()
    account=w3.eth.account.from_key(os.environ['BLOCKCHAIN_PRIVATE_KEY'])
    if owner.lower()!=account.address.lower():
        raise HTTPException(503,'Ví ký không phải chủ hợp đồng AUREVA.')
    return w3,contract,account

from pydantic import BaseModel, Field
class WalletTransaction(BaseModel):
    tx_hash: str = Field(pattern=r'^0x[0-9a-fA-F]{64}$')

def register(app):
    from backend.app import current_user,require,connect,campaign_access
    from backend.evidence import sha
    def permission(db,row,user):
        if row['entity_type']=='decision':
            campaign=db.execute('SELECT campaign_id FROM expenses WHERE id=?',(row['entity_id'],)).fetchone()
        else:campaign=db.execute('SELECT campaign_id FROM reports WHERE id=?',(row['entity_id'],)).fetchone()
        if not campaign:raise HTTPException(404,'Không tìm thấy đối tượng.')
        campaign_access(db,campaign['campaign_id'],user)

    def validate_wallet_transaction(w3,contract,owner,digest,tx_hash):
        tx=w3.eth.get_transaction(tx_hash)
        fn,params=contract.decode_function_input(tx['input'])
        if not (
            (tx['to'] or '').lower()==contract.address.lower()
            and tx['from'].lower()==owner.lower()
            and fn.fn_name=='record'
            and bytes(params['digest']).hex()==digest
            and int(tx.get('chainId',CHAIN_ID))==CHAIN_ID
            and int(tx['value'])==0
        ):
            raise HTTPException(409,'TX không ghi đúng mã băm bằng ví chủ hợp đồng AUREVA.')
        return tx

    @app.get('/api/public/chain/status')
    def onchain_status():
        """Contract-only health check, works before the Preview database is connected."""
        try:
            w3,contract,owner=read_client()
            contract.functions.recordedAt(bytes(32)).call()
            return {'status':'connected','chain_id':CHAIN_ID,'contract':contract.address,
                    'owner':owner,'contract_code_bytes':len(w3.eth.get_code(contract.address))}
        except HTTPException:raise
        except Exception:raise HTTPException(502,'Không xác minh được hợp đồng Sepolia qua RPC.')

    @app.post('/api/attestations/{entity_id}/prepare-wallet')
    def prepare_wallet(entity_id:str,user=Depends(current_user)):
        require(user,'manager','approver')
        try:
            w3,contract,owner=read_client()
            with connect() as db:
                row=db.execute('SELECT * FROM attestations WHERE entity_id=?',(entity_id,)).fetchone()
                if not row:raise HTTPException(404,'Chưa có bản ghi xác thực.')
                permission(db,row,user)
                if sha(row['payload'].encode())!=row['digest']:
                    raise HTTPException(409,'Nội dung không khớp mã băm, không thể ký.')
                if row['status']=='confirmed':
                    raise HTTPException(409,'Đã xác thực trên Sepolia.')
                if row['tx_hash']:
                    raise HTTPException(409,'Đã có TX hash; hãy kiểm tra xác nhận trước.')
            if contract.functions.recordedAt(bytes.fromhex(row['digest'])).call():
                raise HTTPException(409,'Mã băm đã có trên Sepolia; không ghi trùng.')
            return {'chain_id':CHAIN_ID,'contract':contract.address,'owner':owner,
                    'digest':row['digest'],'data':contract.encode_abi('record',args=[bytes.fromhex(row['digest'])])}
        except HTTPException:raise
        except Exception:raise HTTPException(502,'Không chuẩn bị được giao dịch MetaMask; kiểm tra hợp đồng và RPC.')

    @app.post('/api/attestations/{entity_id}/submit-wallet')
    def submit_wallet(entity_id:str,payload:WalletTransaction,user=Depends(current_user)):
        require(user,'manager','approver')
        try:
            w3,contract,owner=read_client()
            with connect(write=True) as db:
                row=db.execute('SELECT * FROM attestations WHERE entity_id=?',(entity_id,)).fetchone()
                if not row:raise HTTPException(404,'Chưa có bản ghi xác thực.')
                permission(db,row,user)
                if sha(row['payload'].encode())!=row['digest']:
                    raise HTTPException(409,'Nội dung không còn khớp mã băm.')
                if row['tx_hash'] and row['tx_hash'].lower()!=payload.tx_hash.lower():
                    raise HTTPException(409,'Bản ghi đã có giao dịch khác; không ghi đè.')
                validate_wallet_transaction(w3,contract,owner,row['digest'],payload.tx_hash)
                from web3.exceptions import TransactionNotFound
                try:receipt=w3.eth.get_transaction_receipt(payload.tx_hash)
                except TransactionNotFound:receipt=None
                state='submitted'
                if receipt and receipt.status==0:state='failed'
                if receipt and receipt.status==1:
                    present=contract.functions.recordedAt(bytes.fromhex(row['digest'])).call()>0
                    if present and w3.eth.block_number-receipt.blockNumber>=2:state='confirmed'
                db.execute('UPDATE attestations SET status=?,tx_hash=?,raw_tx=NULL,chain_id=?,contract=?,block_number=?,error=NULL WHERE entity_id=?',
                           (state,payload.tx_hash,CHAIN_ID,contract.address,receipt.blockNumber if receipt else None,entity_id))
            return {'status':state,'tx_hash':payload.tx_hash}
        except HTTPException:raise
        except Exception:raise HTTPException(502,'Không xác minh được TX trên Sepolia. Dùng Etherscan kiểm tra trước khi gửi lại.')

    @app.post('/api/attestations/{entity_id}/anchor')
    def anchor(entity_id:str,user=Depends(current_user)):
        require(user,'manager','approver')
        try:
            w3,contract,account=client()
            with connect(write=True) as db:
                row=db.execute('SELECT * FROM attestations WHERE entity_id=?',(entity_id,)).fetchone()
                if not row:raise HTTPException(404,'Chưa có bản ghi xác thực.')
                permission(db,row,user)
                if sha(row['payload'].encode())!=row['digest']:raise HTTPException(409,'Bản ghi không còn khớp mã băm. Không được ghi chuỗi.')
                if row['status']=='confirmed':return {'status':'confirmed','tx_hash':row['tx_hash']}
                if row['status']=='failed':raise HTTPException(409,'Giao dịch đã thất bại trên chuỗi. Cần người quản trị kiểm tra trước khi gửi lại.')
                if row['raw_tx']:
                    raw=bytes.fromhex(row['raw_tx']);tx_hash=row['tx_hash']
                    if row['contract']!=contract.address:raise HTTPException(409,'Hợp đồng cấu hình đã thay đổi; cần đối soát giao dịch cũ.')
                else:
                    # Serialized DB write lock protects nonce reservations across workers.
                    reserved=db.execute("SELECT MAX(nonce) FROM attestations WHERE chain_id=? AND contract=? AND status IN ('signed','submitted')",(CHAIN_ID,contract.address)).fetchone()[0]
                    nonce=max(w3.eth.get_transaction_count(account.address,'pending'),(reserved+1) if reserved is not None else 0)
                    tx=contract.functions.record(bytes.fromhex(row['digest'])).build_transaction({'from':account.address,'nonce':nonce,'chainId':CHAIN_ID})
                    signed=account.sign_transaction(tx)
                    raw=bytes(signed.raw_transaction);tx_hash='0x'+bytes(signed.hash).hex()
                    db.execute("UPDATE attestations SET status='signed',tx_hash=?,raw_tx=?,nonce=?,chain_id=?,contract=?,error=NULL WHERE entity_id=?",(tx_hash,raw.hex(),nonce,CHAIN_ID,contract.address,entity_id))
            # Persist signed tx BEFORE sending. Retries rebroadcast the identical bytes/hash.
            try:w3.eth.send_raw_transaction(raw)
            except Exception:
                try:w3.eth.get_transaction(tx_hash)
                except Exception:raise HTTPException(502,'Chưa xác nhận được việc gửi. Có thể thử lại cùng giao dịch; không tạo giao dịch giả.')
            with connect(write=True) as db:db.execute("UPDATE attestations SET status='submitted',error=NULL WHERE entity_id=? AND status='signed'",(entity_id,))
            return {'status':'submitted','tx_hash':tx_hash}
        except HTTPException:raise
        except Exception:raise HTTPException(502,'Không thể kết nối hoặc ký giao dịch Sepolia. Kiểm tra RPC, địa chỉ hợp đồng và số dư test ETH.')

    @app.post('/api/attestations/{entity_id}/refresh')
    def refresh(entity_id:str,user=Depends(current_user)):
        require(user,'manager','approver')
        from web3.exceptions import TransactionNotFound
        try:
            w3,contract,owner=read_client()
            with connect() as db:
                row=db.execute('SELECT * FROM attestations WHERE entity_id=?',(entity_id,)).fetchone()
                if not row:raise HTTPException(404,'Không tìm thấy bản ghi.')
                permission(db,row,user)
            if not row['tx_hash']:raise HTTPException(409,'Chưa gửi giao dịch.')
            if row['contract']!=contract.address:raise HTTPException(409,'Địa chỉ hợp đồng hiện tại khác giao dịch đã lưu.')
            try:receipt=w3.eth.get_transaction_receipt(row['tx_hash'])
            except TransactionNotFound:return {'status':'submitted','tx_hash':row['tx_hash']}
            status='failed'
            if receipt.status==1:
                tx=w3.eth.get_transaction(row['tx_hash'])
                fn,args=contract.decode_function_input(tx['input'])
                correct=(tx['to']==contract.address and tx['from'].lower()==owner.lower() and fn.fn_name=='record' and bytes(args['digest']).hex()==row['digest'] and contract.functions.recordedAt(bytes.fromhex(row['digest'])).call()>0)
                if correct:status='confirmed' if w3.eth.block_number-receipt.blockNumber>=2 else 'submitted'
            with connect(write=True) as db:db.execute('UPDATE attestations SET status=?,block_number=? WHERE entity_id=?',(status,receipt.blockNumber,entity_id))
            return {'status':status,'tx_hash':row['tx_hash']}
        except HTTPException:raise
        except Exception:raise HTTPException(502,'Chưa kiểm tra được receipt trên Sepolia.')

    @app.get('/api/public/attestations/{entity_id}/verify-chain')
    def verify(entity_id:str):
        try:
            w3,contract,owner=read_client()
            with connect() as db:row=db.execute('SELECT * FROM attestations WHERE entity_id=?',(entity_id,)).fetchone()
            if not row:raise HTTPException(404,'Không tìm thấy bản ghi.')
            return {'chain_id':CHAIN_ID,'contract':contract.address,'digest':row['digest'],'payload_valid':sha(row['payload'].encode())==row['digest'],'recorded_at':contract.functions.recordedAt(bytes.fromhex(row['digest'])).call()}
        except HTTPException:raise
        except Exception:raise HTTPException(502,'Không đọc được dữ liệu từ chuỗi.')
