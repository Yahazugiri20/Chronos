import os
import time
from web3 import Web3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# 1. Network Configuration (Base Sepolia)
RPC_URL = os.getenv("RPC_URL")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")

w3 = Web3(Web3.HTTPProvider(RPC_URL))
account = w3.eth.account.from_key(PRIVATE_KEY)

# 2. Smart Contract ABI (Minimalist for verification)
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

def run_chronos_agent(claim):
    print(f"\n[Chronos AI Agent] Initializing verification process...")
    print(f"[Chronos AI Agent] Analyzing claim: \"{claim}\"")
    
    # Simulating AI deep-research process
    time.sleep(2) 
    
    # Mocking AI result (In production, this comes from an LLM API)
    confidence_score = 98 
    proof_reference = "ipfs://chronos-v1-verified-record"
    
    print(f"[Chronos AI Agent] Analysis complete. Confidence Score: {confidence_score}%")
    print(f"[Chronos AI Agent] Broadcasting attestation to Base Sepolia...")

    try:
        # Building the transaction
        nonce = w3.eth.get_transaction_count(account.address)
        
        # Setting gas parameters
        tx = contract.functions.verifyClaim(claim, confidence_score, proof_reference).build_transaction({
            'from': account.address,
            'nonce': nonce,
            'gas': 250000,
            'gasPrice': w3.to_wei('0.05', 'gwei') # Low gas fee on Base
        })

        # Signing and sending
        signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        print("-" * 50)
        print(f"✅ SUCCESS: Historical Truth Secured On-Chain")
        print(f"🔗 Transaction Hash: {w3.to_hex(tx_hash)}")
        print(f"🌍 Explorer: https://sepolia.basescan.org/tx/{w3.to_hex(tx_hash)}")
        print("-" * 50)
        
    except Exception as e:
        print(f"❌ Transaction failed: {str(e)}")

if __name__ == "__main__":
    print("=" * 40)
    print("      CHRONOS AI AGENT TERMINAL      ")
    print("=" * 40)
    
    claim_input = input("Enter historical claim to archive: ")
    if claim_input:
        run_chronos_agent(claim_input)
    else:
        print("Input cannot be empty.")
