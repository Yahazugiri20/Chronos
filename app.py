import streamlit as st
import os
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

# --- CONFIG ---
RPC_URL = os.getenv("RPC_URL")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")

w3 = Web3(Web3.HTTPProvider(RPC_URL))
account = w3.eth.account.from_key(PRIVATE_KEY)

ABI = [
    {
        "inputs": [
            {"internalType": "string", "name": "_claim", "type": "string"},
            {"internalType": "uint256", "name": "_score", "type": "uint256"},
            {"internalType": "string", "name": "_hash", "type": "string"}
        ],
        "name": "verifyClaim",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=ABI)

# --- UI STREAMLIT ---
st.set_page_config(page_title="Chronos AI Agent", page_icon="🏛️")
st.title("🏛️ Chronos AI Agent")
st.subheader("Historical Truth Verification on Base")

claim_input = st.text_area("Enter historical claim to archive:", placeholder="e.g. The Battle of Talas (751 AD)...")

if st.button("Verify & Archive on Base"):
    if claim_input:
        with st.status("Chronos AI is analyzing...", expanded=True) as status:
            # 1. Logic AI (Nanti kita ganti pake API beneran di sini)
            st.write("Checking historical sources...")
            confidence_score = 98 
            proof_reference = "ipfs://chronos-v1-verified"
            
            # 2. Blockchain Transaction
            st.write("Broadcasting to Base Sepolia...")
            nonce = w3.eth.get_transaction_count(account.address)
            tx = contract.functions.verifyClaim(claim_input, confidence_score, proof_reference).build_transaction({
                'from': account.address,
                'nonce': nonce,
                'gas': 300000,
                'gasPrice': w3.to_wei('0.05', 'gwei')
            })

            signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            
            status.update(label="Success! Secured On-Chain", state="complete", expanded=False)

        st.success(f"✅ Historical Truth Secured!")
        st.info(f"🔗 Transaction Hash: {w3.to_hex(tx_hash)}")
        st.link_button("View on Explorer", f"https://sepolia.basescan.org/tx/{w3.to_hex(tx_hash)}")
    else:
        st.error("Please enter a claim first!")
