"""Sepolia-only durable transaction outbox. No mocked transaction identifiers."""
import json,os
from pathlib import Path
from fastapi import Depends,HTTPException
CHAIN_ID=11155111

def configured():return all(os.getenv(k) for k in ('SEPOLIA_RPC_URL','BLOCKCHAIN_PRIVATE_KEY','AUREVA_CONTRACT_ADDRESS'))
def client():
    if not configured():raise HTTPException(503,'Chưa cấu hình RPC, ví testnet và hợp đồng AUREVA.')
    from web3 import Web3
    w3=Web3(Web3.HTTPProvider(os.environ['SEPOLIA_RPC_URL'],request_kwargs={'timeout':15}))
    if w3.eth.chain_id!=CHAIN_ID:raise HTTPException(503,'Chỉ cho phép mạng Ethereum Sepolia testnet.')
    address=w3.to_checksum_address(os.environ['AUREVA_CONTRACT_ADDRESS'])
    if not w3.eth.get_code(address):raise HTTPException(503,'Không tìm thấy hợp đồng tại địa chỉ cấu hình.')
    artifact=json.loads((Path(__file__).resolve().parents[1]/'blockchain/artifact.json').read_text())
    contract=w3.eth.contract(address=address,abi=artifact['abi'])
    account=w3.eth.account.from_key(os.environ['BLOCKCHAIN_PRIVATE_KEY'])
    if contract.functions.owner().call()!=account.address:raise HTTPException(503,'Ví ký không phải chủ hợp đồng AUREVA.')
    return w3,contract,account

def register(app):
    from backend.app import current_user,require,connect,campaign_access
    from backend.evidence import sha
    def permission(db,row,user):
        if row['entity_type']=='decision':
            campaign=db.execute('SELECT campaign_id FROM expenses WHERE id=?',(row['entity_id'],)).fetchone()
        else:campaign=db.execute('SELECT campaign_id FROM reports WHERE id=?',(row['entity_id'],)).fetchone()
        if not campaign:raise HTTPException(404,'Không tìm thấy đối tượng.')
        campaign_access(db,campaign['campaign_id'],user)

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
            w3,contract,account=client()
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
                correct=(tx['to']==contract.address and tx['from']==account.address and fn.fn_name=='record' and bytes(args['digest']).hex()==row['digest'] and contract.functions.recordedAt(bytes.fromhex(row['digest'])).call()>0)
                if correct:status='confirmed' if w3.eth.block_number-receipt.blockNumber>=2 else 'submitted'
            with connect(write=True) as db:db.execute('UPDATE attestations SET status=?,block_number=? WHERE entity_id=?',(status,receipt.blockNumber,entity_id))
            return {'status':status,'tx_hash':row['tx_hash']}
        except HTTPException:raise
        except Exception:raise HTTPException(502,'Chưa kiểm tra được receipt trên Sepolia.')

    @app.get('/api/public/attestations/{entity_id}/verify-chain')
    def verify(entity_id:str):
        try:
            w3,contract,account=client()
            with connect() as db:row=db.execute('SELECT * FROM attestations WHERE entity_id=?',(entity_id,)).fetchone()
            if not row:raise HTTPException(404,'Không tìm thấy bản ghi.')
            return {'chain_id':CHAIN_ID,'contract':contract.address,'digest':row['digest'],'payload_valid':sha(row['payload'].encode())==row['digest'],'recorded_at':contract.functions.recordedAt(bytes.fromhex(row['digest'])).call()}
        except HTTPException:raise
        except Exception:raise HTTPException(502,'Không đọc được dữ liệu từ chuỗi.')
