"""Deploy the reviewed registry to Sepolia using the locally configured test wallet."""
import sys,json,os
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend.app import ROOT
from web3 import Web3
rpc=os.getenv('SEPOLIA_RPC_URL');key=os.getenv('BLOCKCHAIN_PRIVATE_KEY')
if not rpc or not key:raise SystemExit('Cần SEPOLIA_RPC_URL và BLOCKCHAIN_PRIVATE_KEY trong .env')
w3=Web3(Web3.HTTPProvider(rpc,request_kwargs={'timeout':20}))
assert w3.eth.chain_id==11155111,'Only Sepolia is permitted'
account=w3.eth.account.from_key(key)
artifact=json.loads((ROOT/'blockchain/artifact.json').read_text())
contract=w3.eth.contract(abi=artifact['abi'],bytecode=artifact['bytecode'])
tx=contract.constructor().build_transaction({'from':account.address,'nonce':w3.eth.get_transaction_count(account.address,'pending'),'chainId':11155111})
signed=account.sign_transaction(tx)
tx_hash=w3.eth.send_raw_transaction(signed.raw_transaction)
print('Deployment transaction: https://sepolia.etherscan.io/tx/'+tx_hash.hex())
receipt=w3.eth.wait_for_transaction_receipt(tx_hash,timeout=180)
assert receipt.status==1,'Deployment reverted'
print('AUREVA_CONTRACT_ADDRESS='+receipt.contractAddress)
(ROOT/'blockchain/deployment.json').write_text(json.dumps({'chain_id':11155111,'contract':receipt.contractAddress,'tx_hash':tx_hash.hex()},indent=2))
