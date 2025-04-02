from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import json
from dotenv import load_dotenv
from web3 import Web3
import qrcode
from io import BytesIO
import base64
import logging

# Setup basic logging
logging.basicConfig(level=logging.INFO)

# Load environment variables from .env file
load_dotenv()

app = FastAPI(title="Charity Tracker API")

# Environment variables
SEPOLIA_RPC_URL = os.getenv("SEPOLIA_RPC_URL")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
if not SEPOLIA_RPC_URL or not PRIVATE_KEY:
    raise Exception("Please set SEPOLIA_RPC_URL and PRIVATE_KEY in your .env file")

# Setup Web3 provider
w3 = Web3(Web3.HTTPProvider(SEPOLIA_RPC_URL))
if not w3.is_connected():
    raise Exception("Could not connect to the Sepolia network")

# Derive owner's account from private key
account = w3.eth.account.from_key(PRIVATE_KEY)
owner_address = account.address

# Deployed contract address (update if needed)
contract_address = Web3.to_checksum_address( os.getenv("CHARITY_DEPLOYED_ADDRS"))

# Load contract ABI from JSON artifact (adjust the path as needed)
abi_path = os.path.join("artifacts", "contracts", "CharityTracker.sol", "CharityTracker.json")
try:
    with open(abi_path) as f:
        artifact = json.load(f)
        if "abi" in artifact:
            contract_abi = artifact["abi"]
        else:
            raise Exception("ABI not found in the artifact JSON")
except Exception as e:
    raise Exception(f"Error loading contract ABI: {str(e)}")

# Create the contract instance
contract = w3.eth.contract(address=contract_address, abi=contract_abi)
chain_id = w3.eth.chain_id

# Pydantic models for request bodies
class Charity(BaseModel):
    donation_address: str
    name: str
    description: str
    website_url: str = ""  # Optional
    payment_url: str = ""  # Optional

class VerifyCharity(BaseModel):
    donation_address: str

def to_checksum(address: str) -> str:
    """Convert an Ethereum address to its checksum format."""
    try:
        return Web3.to_checksum_address(address)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid address format: {e}")

def send_transaction(txn_function):
    """
    Helper function to build, sign, and send a transaction.
    Returns the transaction hash and receipt status.
    """
    try:
        nonce = w3.eth.get_transaction_count(owner_address)
        txn = txn_function.build_transaction({
            'chainId': chain_id,
            'gas': 300000,
            'gasPrice': w3.eth.gas_price,
            'nonce': nonce,
        })
        signed_txn = w3.eth.account.sign_transaction(txn, PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        return tx_hash.hex(), receipt.status
    except Exception as e:
        logging.error(f"Transaction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ---------------------------
# Endpoint: Get Charity Data
# ---------------------------
@app.get("/charity/{donation_address}")
def get_charity(donation_address: str):
    """
    Retrieve charity details by donation address.
    Returns name, description, website URL, payment URL, and verification status.
    """
    checksum_addr = to_checksum(donation_address)
    try:
        result = contract.functions.getCharity(checksum_addr).call()
        if result[3]!="":
            img = qrcode.make(result[3])
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
        return {
            "name": result[0],
            "description": result[1],
            "website_url": result[2],
            "payment_url": result[3],
            "verified": result[4],
            "qr_code": img_base64 if result[3]!="" else None
        }
    except Exception as e:
        logging.error(f"Error fetching charity data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ---------------------------
# Endpoint: Add a Charity
# ---------------------------
@app.post("/charity")
def add_charity(charity: Charity):
    """
    Add a new charity.
    Expects donation_address, name, description, website_url (optional), and payment_url (optional).
    """
    checksum_addr = to_checksum(charity.donation_address)
    try:
        tx_hash, status = send_transaction(
            contract.functions.addCharity(
                checksum_addr,
                charity.name,
                charity.description,
                charity.website_url,
                charity.payment_url
            )
        )
        return {"tx_hash": tx_hash, "status": status}
    except Exception as e:
        logging.error(f"Error adding charity: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ---------------------------
# Endpoint: Verify a Charity
# ---------------------------
@app.post("/charity/verify")
def verify_charity(verify: VerifyCharity):
    """
    Verify a charity by its donation address.
    Only the contract owner can verify a charity.
    """
    checksum_addr = to_checksum(verify.donation_address)
    try:
        tx_hash, status = send_transaction(
            contract.functions.verifyCharity(checksum_addr)
        )
        return {"tx_hash": tx_hash, "status": status}
    except Exception as e:
        logging.error(f"Error verifying charity: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ---------------------------
# Endpoint: Generate Donation QR Code
# ---------------------------
# @app.get("/qr")
# def generate_qr(address: str):
#     """
#     Generate a QR code for the provided Ethereum donation address.
#     Returns a Base64-encoded PNG image.
#     """
#     checksum_addr = to_checksum(address)
#     try:
#         payment_uri = f"ethereum:{checksum_addr}"
#         img = qrcode.make(payment_uri)
#         buffered = BytesIO()
#         img.save(buffered, format="PNG")
#         img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
#         return {"qr_code": img_base64}
#     except Exception as e:
#         logging.error(f"Error generating QR code: {e}")
#         raise HTTPException(status_code=500, detail=str(e))
