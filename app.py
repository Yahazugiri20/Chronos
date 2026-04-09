from flask import Flask, render_template_string, request, jsonify
import os, requests
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

# --- CONFIG ---
RPC_URL = os.getenv("RPC_URL")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")
PINATA_JWT = os.getenv("PINATA_JWT")

w3 = Web3(Web3.HTTPProvider(RPC_URL))
account = w3.eth.account.from_key(PRIVATE_KEY)

ABI = [
    {"inputs": [{"internalType": "string", "name": "_claim", "type": "string"},{"internalType": "uint256", "name": "_score", "type": "uint256"},{"internalType": "string", "name": "_hash", "type": "string"}],"name": "verifyClaim","outputs": [],"stateMutability": "nonpayable","type": "function"}
]
contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=ABI)

# --- LOGIC IPFS ---
def upload_to_ipfs(file_obj):
    url = "https://api.pinata.cloud/pinning/pinFileToIPFS"
    headers = {"Authorization": f"Bearer {PINATA_JWT}"}
    files = {"file": (file_obj.filename, file_obj.read())}
    try:
        r = requests.post(url, headers=headers, files=files)
        return f"https://gateway.pinata.cloud/ipfs/{r.json()['IpfsHash']}"
    except:
        return "ipfs://failed"

# --- UI (Disesuaikan agar ada tombol File) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Chronos AI | Archive</title>
    <style>
        body { font-family: sans-serif; background: #000; color: white; text-align: center; padding: 50px; }
        .card { background: #111; padding: 30px; border-radius: 20px; border: 1px solid #333; display: inline-block; width: 90%; max-width: 450px; }
        textarea { width: 100%; height: 100px; background: #000; color: white; border: 1px solid #333; padding: 10px; margin-top: 10px; border-radius: 10px; }
        input[type="file"] { margin-top: 20px; color: #888; font-size: 0.8em; }
        button { background: #0052ff; color: white; border: none; padding: 15px; width: 100%; margin-top: 20px; cursor: pointer; border-radius: 10px; font-weight: bold; }
        #status { margin-top: 20px; font-size: 0.9em; color: #888; }
    </style>
</head>
<body>
    <div class="card">
        <h1>🏛️ Chronos AI</h1>
        <p>Archive History with Visual Evidence</p>
        <textarea id="claim" placeholder="Enter historical claim..."></textarea>
        <input type="file" id="imageFile" accept="image/*">
        <button onclick="verify()">Verify & Upload to Base</button>
        <div id="status"></div>
    </div>

    <script>
        async function verify() {
            const claim = document.getElementById('claim').value;
            const fileInput = document.getElementById('imageFile');
            const statusDiv = document.getElementById('status');
            
            if(!claim || !fileInput.files[0]) return alert("Please enter claim AND select an image!");
            
            statusDiv.innerHTML = "⏳ Phase 1: Uploading image to IPFS...";
            
            const formData = new FormData();
            formData.append('claim', claim);
            formData.append('file', fileInput.files[0]);

            const res = await fetch('/verify', { method: 'POST', body: formData });
            const data = await res.json();
            
            if(data.success) {
                statusDiv.innerHTML = `✅ <b>Success!</b><br>IPFS: <a href="${data.ipfs_url}" target="_blank" style="color:#0052ff">View Image</a><br>Tx: <a href="https://sepolia.basescan.org/tx/${data.tx_hash}" target="_blank" style="color:#0052ff">View Tx</a>`;
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
    return render_template_string(HTML_TEMPLATE)

@app.route('/verify', methods=['POST'])
def verify():
    try:
        claim = request.form.get('claim')
        file = request.files.get('file')

        # 1. Upload ke IPFS
        ipfs_link = upload_to_ipfs(file)

        # 2. Blockchain
        nonce = w3.eth.get_transaction_count(account.address)
        tx = contract.functions.verifyClaim(claim, 98, ipfs_link).build_transaction({
            'from': account.address,
            'nonce': nonce,
            'gas': 300000,
            'gasPrice': w3.to_wei('0.05', 'gwei')
        })
        signed = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        
        return jsonify({"success": True, "tx_hash": w3.to_hex(tx_hash), "ipfs_url": ipfs_link})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    app.run()
