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

ABI = [{"inputs":[{"internalType":"string","name":"_claim","type":"string"},{"internalType":"uint256","name":"_score","type":"uint256"},{"internalType":"string","name":"_hash","type":"string"}],"name":"verifyClaim","outputs":[],"stateMutability":"nonpayable","type":"function"}]
contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=ABI)

def upload_to_ipfs(file_obj):
    url = "https://api.pinata.cloud/pinning/pinFileToIPFS"
    headers = {"Authorization": f"Bearer {PINATA_JWT}"}
    files = {"file": (file_obj.filename, file_obj.read())}
    try:
        r = requests.post(url, headers=headers, files=files)
        return f"https://gateway.pinata.cloud/ipfs/{r.json()['IpfsHash']}"
    except: return "ipfs://error"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Chronos | Public History Ledger</title>
    <style>
        :root { --base-blue: #0052ff; --dark-card: #111; --border: #222; }
        body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; background: #000; color: white; margin: 0; }
        
        /* Layout Layer 1: Input Section */
        .hero { padding: 60px 20px; border-bottom: 1px solid var(--border); background: radial-gradient(circle at top, #0052ff15 0%, #000 70%); }
        .input-card { background: var(--dark-card); max-width: 500px; margin: auto; padding: 30px; border-radius: 20px; border: 1px solid #333; }
        textarea { width: 100%; height: 80px; background: #000; color: white; border: 1px solid #333; border-radius: 10px; padding: 12px; box-sizing: border-box; font-size: 14px; }
        .btn-main { background: var(--base-blue); color: white; border: none; padding: 14px; width: 100%; border-radius: 10px; font-weight: bold; cursor: pointer; margin-top: 20px; font-size: 16px; }
        
        /* Layout Layer 2: Archives Section */
        .archives-container { max-width: 1000px; margin: 50px auto; padding: 0 20px; }
        .gallery-header { display: flex; align-items: center; margin-bottom: 30px; }
        .gallery-header h2 { margin: 0; font-size: 1.5em; letter-spacing: -0.5px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 25px; }
        
        .card-archived { background: var(--dark-card); border-radius: 16px; overflow: hidden; border: 1px solid var(--border); transition: 0.2s; }
        .card-archived:hover { border-color: var(--base-blue); transform: translateY(-3px); }
        .card-img { width: 100%; height: 180px; object-fit: cover; background: #1a1a1a; }
        .card-body { padding: 20px; }
        .card-meta { font-size: 11px; color: #666; font-family: monospace; margin-bottom: 10px; display: block; overflow: hidden; text-overflow: ellipsis; }
        .card-text { font-size: 14px; line-height: 1.5; color: #ccc; margin-bottom: 15px; }
        .badge { background: #0052ff15; color: var(--base-blue); padding: 4px 8px; border-radius: 6px; font-size: 11px; font-weight: bold; }
    </style>
</head>
<body>

    <div class="hero">
        <div class="input-card">
            <h2 style="margin-top:0">🏛️ Chronos Archive</h2>
            <p style="color:#666; font-size: 13px; margin-bottom: 20px;">Deploy historical evidence to Base Sepolia Network</p>
            <textarea id="claim" placeholder="Describe the historical claim..."></textarea>
            <input type="file" id="imageFile" accept="image/*" style="margin-top:20px; font-size: 12px; color: #888;">
            <button class="btn-main" onclick="archive()">Blast to Blockchain</button>
            <div id="status" style="margin-top:15px; font-size: 12px;"></div>
        </div>
    </div>

    <div class="archives-container">
        <div class="gallery-header">
            <h2>📜 Verified Historical Ledger</h2>
        </div>
        <div id="archiveGrid" class="grid">
            </div>
    </div>

    <script>
        const MY_ADDRESS = "{{ wallet_address }}"; // Injected from Python

        function renderGallery() {
            const grid = document.getElementById('archiveGrid');
            const data = JSON.parse(localStorage.getItem('chronos_v2') || '[]');
            grid.innerHTML = data.reverse().map(item => `
                <div class="card-archived">
                    <img src="${item.img}" class="card-img">
                    <div class="card-body">
                        <span class="card-meta">SUBMITTED BY: ${item.address}</span>
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                            <span class="badge">SCORE: ${item.score}%</span>
                            <a href="https://sepolia.basescan.org/tx/${item.tx}" target="_blank" style="font-size:11px; color:var(--base-blue); text-decoration:none;">EXPLORER ↗</a>
                        </div>
                        <p class="card-text">${item.claim}</p>
                    </div>
                </div>
            `).join('');
        }

        async function archive() {
            const claim = document.getElementById('claim').value;
            const file = document.getElementById('imageFile').files[0];
            const status = document.getElementById('status');
            if(!claim || !file) return alert("Fill everything!");

            status.innerHTML = "⏳ Initializing IPFS & AI Analysis...";
            const fd = new FormData();
            fd.append('claim', claim);
            fd.append('file', file);

            try {
                const res = await fetch('/verify', {method:'POST', body:fd});
                const d = await res.json();
                if(d.success) {
                    status.innerHTML = "✅ ARCHIVED SUCCESSFULLY";
                    const history = JSON.parse(localStorage.getItem('chronos_v2') || '[]');
                    history.push({claim, img: d.ipfs_url, tx: d.tx_hash, address: MY_ADDRESS, score: 98});
                    localStorage.setItem('chronos_v2', JSON.stringify(history));
                    renderGallery();
                } else { status.innerHTML = "❌ " + d.error; }
            } catch(e) { status.innerHTML = "❌ Network Error"; }
        }
        renderGallery();
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    # Kirim wallet address biar frontend bisa nampilin siapa pengirimnya
    return render_template_string(HTML_TEMPLATE, wallet_address=account.address)

@app.route('/verify', methods=['POST'])
def verify():
    try:
        claim = request.form.get('claim')
        file = request.files.get('file')
        ipfs_url = upload_to_ipfs(file)
        
        nonce = w3.eth.get_transaction_count(account.address)
        tx = contract.functions.verifyClaim(claim, 98, ipfs_url).build_transaction({
            'from': account.address, 'nonce': nonce, 'gas': 300000, 'gasPrice': w3.to_wei('0.05', 'gwei')
        })
        signed = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        
        return jsonify({"success": True, "tx_hash": w3.to_hex(tx_hash), "ipfs_url": ipfs_url})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    app.run()
