import json
from pathlib import Path

from web3 import Web3

from app.core.config import settings


BASE_DIR = Path(__file__).resolve().parent

with open(BASE_DIR / "contract_abi.json", "r") as f:
    CONTRACT_ABI = json.load(f)


w3 = Web3(Web3.HTTPProvider(settings.SEPOLIA_RPC_URL))

contract = w3.eth.contract(
    address=Web3.to_checksum_address(settings.CONTRACT_ADDRESS),
    abi=CONTRACT_ABI
)


def register_document(document_id: str, document_hash: str):

    account = w3.eth.account.from_key(
        settings.BLOCKCHAIN_PRIVATE_KEY
    )

    nonce = w3.eth.get_transaction_count(
        account.address
    )

    transaction = contract.functions.registerDocument(
        document_id,
        bytes.fromhex(document_hash)
    ).build_transaction({
        "from": account.address,
        "nonce": nonce,
        "gas": 300000,
        "gasPrice": w3.eth.gas_price,
        "chainId": 11155111
    })

    signed_transaction = w3.eth.account.sign_transaction(
        transaction,
        settings.BLOCKCHAIN_PRIVATE_KEY
    )

    tx_hash = w3.eth.send_raw_transaction(
        signed_transaction.raw_transaction
    )

    receipt = w3.eth.wait_for_transaction_receipt(
        tx_hash
    )

    return {
        "transaction_hash": tx_hash.hex(),
        "block_number": receipt.blockNumber,
        "contract_address": settings.CONTRACT_ADDRESS
    }


def verify_document(document_id: str, document_hash: str):

    result = contract.functions.verifyDocument(
        document_id,
        bytes.fromhex(document_hash)
    ).call()

    return result