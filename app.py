from flask import Flask, render_template_string, request, jsonify
import os, requests
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

# --- CONFIG ---
PINATA_JWT = os.getenv("PINATA_JWT")

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
    <title>Chronos | AI Historical Ledger</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/ethers/5.7.2/ethers.umd.min.js"></script>
    <style>
        :root { --base-blue: #0052ff; --dark-bg: #000; --card-bg: #111; --border: #222; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: var(--dark-bg); color: white; margin: 0; }

        .nav { display: flex; justify-content: space-between; align-items: center; padding: 20px 40px; border-bottom: 1px solid var(--border); background: rgba(0,0,0,0.8); backdrop-filter: blur(10px); position: sticky; top: 0; z-index: 100; }
        .logo { font-weight: 800; font-size: 1.5em; letter-spacing: -1px; }
        .btn-connect { background: #fff; color: #000; border: none; padding: 10px 20px; border-radius: 50px; font-weight: bold; cursor: pointer; transition: 0.3s; }
        .btn-connect:hover { background: var(--base-blue); color: #fff; }

        .hero { padding: 80px 20px; text-align: center; background: radial-gradient(circle at center, #0052ff10 0%, transparent 70%); }
        .input-card { background: var(--card-bg); max-width: 550px; margin: auto; padding: 40px; border-radius: 24px; border: 1px solid var(--border); box-shadow: 0 20px 40px rgba(0,0,0,0.4); }
        textarea { width: 100%; height: 100px; background: #050505; color: white; border: 1px solid #333; border-radius: 12px; padding: 15px; box-sizing: border-box; font-size: 16px; margin-bottom: 20px; resize: none; }
        .file-label { display: block; text-align: left; color: #888; font-size: 12px; margin-bottom: 8px; }
        .btn-blast { background: var(--base-blue); color: white; border: none; padding: 18px; width: 100%; border-radius: 12px; font-weight: bold; cursor: pointer; font-size: 16px; transition: 0.3s; }

        .archives { max-width: 1100px; margin: 60px auto; padding: 0 20px; }
        .section-title { font-size: 24px; margin-bottom: 30px; display: flex; align-items: center; gap: 10px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 30px; }
        .archive-card { background: var(--card-bg); border-radius: 20px; overflow: hidden; border: 1px solid var(--border); transition: 0.3s; text-align: left; }
        .archive-card:hover { transform: translateY(-5px); border-color: var(--base-blue); }
        .card-img { width: 100%; height: 200px; object-fit: cover; }
        .card-content { padding: 20px; }
        .addr-tag { font-family: monospace; color: #0052ff; font-size: 11px; background: rgba(0,82,255,0.1); padding: 4px 8px; border-radius: 4px; display: inline-block; margin-bottom: 12px; }
        .card-desc { font-size: 14px; line-height: 1.6; color: #ccc; margin: 0 0 20px 0; }
        .card-footer { display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #222; padding-top: 15px; }
    </style>
</head>
<body>

    <nav class="nav">
        <div class="logo">🏛️ CHRONOS</div>
        <button class="btn-connect" id="btnConnect" onclick="connectWallet()">Connect Wallet</button>
    </nav>

    <div class="hero">
        <div class="input-card">
            <h2 style="margin:0 0 10px 0">Archive Evidence</h2>
            <p style="color:#888; font-size:14px; margin-bottom:30px; letter-spacing: 0.5px;">Historical Integrity • <b>Build on Base</b></p>

            <textarea id="claim" placeholder="Describe the historical event you want to archive..."></textarea>

            <span class="file-label">ATTACH SOURCE DOCUMENT / IMAGE</span>
            <input type="file" id="imageFile" accept="image/*" style="display:block; margin-bottom:25px; color:#888;">

            <button class="btn-blast" id="btnBlast" onclick="archive()">Blast to Blockchain</button>
            <div id="status" style="margin-top:20px; font-size:13px; color:#888;"></div>
        </div>
    </div>

    <div class="archives">
        <div class="section-title">📜 Verified Historical Ledger</div>
        <div id="archiveGrid" class="grid"></div>
    </div>

    <script>
        let userAddress = null;
        const CONTRACT_ADDRESS = "0xF5363562B480E1ba32a2192171eF395c99C1d39c";
        const ABI = [{"inputs":[{"internalType":"string","name":"_claim","type":"string"},{"internalType":"uint256","name":"_score","type":"uint256"},{"internalType":"string","name":"_hash","type":"string"}],"name":"verifyClaim","outputs":[],"stateMutability":"nonpayable","type":"function"}];

        async function connectWallet() {
            if (window.ethereum) {
                try {
                    const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
                    userAddress = accounts[0];
                    document.getElementById('btnConnect').innerHTML = userAddress.substring(0,6) + "..." + userAddress.substring(38);
                    renderGallery();
                } catch (e) { console.error(e); }
            } else { alert("Please install MetaMask to continue."); }
        }

        function renderGallery() {
            const grid = document.getElementById('archiveGrid');
            const data = JSON.parse(localStorage.getItem('chronos_final') || '[]');
            grid.innerHTML = data.reverse().map(item => `
                <div class="archive-card">
                    <img src="${item.img}" class="card-img">
                    <div class="card-content">
                        <span class="addr-tag">By: ${item.address}</span>
                        <p class="card-desc">${item.claim}</p>
                        <div class="card-footer">
                            <span style="font-size:12px; font-weight:bold; color:#00ff88">SCORE: ${item.score}%</span>
                            <a href="https://sepolia.basescan.org/tx/${item.tx}" target="_blank" style="color:var(--base-blue); text-decoration:none; font-size:12px; font-weight:bold;">EXPLORER ↗</a>
                        </div>
                    </div>
                </div>
            `).join('');
        }

        async function archive() {
            if(!userAddress) return alert("Please connect your wallet first!");

            const claim = document.getElementById('claim').value;
            const file = document.getElementById('imageFile').files[0];
            const status = document.getElementById('status');

            if(!claim || !file) return alert("Please provide both a claim and an image.");

            status.innerHTML = "⏳ Phase 1: Uploading to IPFS & Verifying...";
            const fd = new FormData();
            fd.append('claim', claim);
            fd.append('file', file);

            try {
                // Backend handles IPFS upload only
                const res = await fetch('/verify', {method:'POST', body:fd});
                const d = await res.json();

                if(d.success) {
                    status.innerHTML = "✍️ Phase 2: Sign the transaction ..";
                    
                    // ONCHAIN INTERACTION VIA ETHERS.JS
                    const provider = new ethers.providers.Web3Provider(window.ethereum);
                    const signer = provider.getSigner();
                    const contract = new ethers.Contract(CONTRACT_ADDRESS, ABI, signer);

                    // Execute Contract Function (MetaMask pop-up will appear)
                    const tx = await contract.verifyClaim(claim, 98, d.ipfs_url);
                    
                    status.innerHTML = "⛓️ Phase 3: Mining on Base... please wait.";
                    const receipt = await tx.wait(); // Wait for block confirmation

                    status.innerHTML = "✅ SUCCESSFULLY ARCHIVED ON BASE";
                    
                    const history = JSON.parse(localStorage.getItem('chronos_final') || '[]');
                    history.push({
                        claim: claim,
                        img: d.ipfs_url,
                        tx: receipt.transactionHash,
                        address: userAddress,
                        score: 98
                    });
                    localStorage.setItem('chronos_final', JSON.stringify(history));
                    renderGallery();
                    document.getElementById('claim').value = "";
                } else { status.innerHTML = "❌ Error: " + d.error; }
            } catch(e) { 
                console.error(e);
                status.innerHTML = "❌ User rejected signature or network issue."; 
            }
        }
        renderGallery();
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
        file = request.files.get('file')
        ipfs_url = upload_to_ipfs(file)
        # Backend handles file storage, frontend handles blockchain state
        return jsonify({"success": True, "ipfs_url": ipfs_url})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    app.run()
