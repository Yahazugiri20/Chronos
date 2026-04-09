from flask import Flask, render_template_with_string, request, jsonify
import os
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__) # Ini yang dicari Vercel!

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

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Chronos AI Agent</title>
    <style>
        body { font-family: sans-serif; background: #121212; color: white; text-align: center; padding: 50px; }
        .card { background: #1e1e1e; padding: 30px; border-radius: 15px; display: inline-block; width: 80%; max-width: 500px; border: 1px solid #333; }
        textarea { width: 100%; height: 100px; background: #222; color: white; border: 1px solid #444; padding: 10px; margin-top: 10px; }
        button { background: #0052ff; color: white; border: none; padding: 15px 30px; margin-top: 20px; cursor: pointer; border-radius: 5px; font-weight: bold; }
        button:hover { background: #0042cc; }
        #status { margin-top: 20px; color: #aaa; }
    </style>
</head>
<body>
    <div class="card">
        <h1>🏛️ Chronos AI</h1>
        <p>Verify Historical Truth on Base</p>
        <textarea id="claim" placeholder="Enter historical claim..."></textarea><br>
        <button onclick="verify()">Verify & Archive</button>
        <div id="status"></div>
    </div>

    <script>
        async function verify() {
            const claim = document.getElementById('claim').value;
            const statusDiv = document.getElementById('status');
            if(!claim) return alert("Enter a claim!");
            
            statusDiv.innerHTML = "⏳ Chronos is analyzing & broadcasting...";
            
            const res = await fetch('/verify', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({claim})
            });
            const data = await res.json();
            
            if(data.success) {
                statusDiv.innerHTML = `✅ <b>Success!</b><br><br>Tx: <a href="https://sepolia.basescan.org/tx/${data.tx_hash}" target="_blank" style="color:#0052ff">${data.tx_hash}</a>`;
            } else {
                statusDiv.innerHTML = "❌ Error: " + data.error;
            }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    from flask import render_template_string
    return render_template_string(HTML_TEMPLATE)

@app.route('/verify', methods=['POST'])
def verify():
    try:
        data = request.json
        claim = data.get('claim')
        
        # Logic AI Simulasi
        confidence_score = 98
        proof_hash = "ipfs://verified_chronos"

        nonce = w3.eth.get_transaction_count(account.address)
        tx = contract.functions.verifyClaim(claim, confidence_score, proof_hash).build_transaction({
            'from': account.address,
            'nonce': nonce,
            'gas': 300000,
            'gasPrice': w3.to_wei('0.05', 'gwei')
        })

        signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        return jsonify({"success": True, "tx_hash": w3.to_hex(tx_hash)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    app.run(debug=True)
