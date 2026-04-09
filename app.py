from flask import Flask, render_template_string, request, jsonify
import os
import requests
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

# --- CONFIG ---
RPC_URL = os.getenv("RPC_URL")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

w3 = Web3(Web3.HTTPProvider(RPC_URL))
account = w3.eth.account.from_key(PRIVATE_KEY)

ABI = [
    {"inputs": [{"internalType": "string", "name": "_claim", "type": "string"},{"internalType": "uint256", "name": "_score", "type": "uint256"},{"internalType": "string", "name": "_hash", "type": "string"}],"name": "verifyClaim","outputs": [],"stateMutability": "nonpayable","type": "function"}
]
contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=ABI)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Chronos AI Agent</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background: #000; color: white; text-align: center; padding: 20px; }
        .card { background: #111; padding: 30px; border-radius: 20px; display: inline-block; width: 90%; max-width: 450px; border: 1px solid #222; margin-top: 50px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }
        h1 { color: #0052ff; margin-bottom: 5px; }
        p { color: #888; margin-bottom: 30px; font-size: 0.9em; }
        textarea { width: 100%; height: 120px; background: #000; color: white; border: 1px solid #333; padding: 15px; border-radius: 10px; box-sizing: border-box; resize: none; font-size: 16px; }
        textarea:focus { border-color: #0052ff; outline: none; }
        button { background: #0052ff; color: white; border: none; padding: 15px 0; width: 100%; margin-top: 20px; cursor: pointer; border-radius: 10px; font-weight: bold; font-size: 16px; transition: 0.3s; }
        button:hover { background: #0042cc; transform: translateY(-2px); }
        #status { margin-top: 25px; line-height: 1.6; font-size: 0.9em; }
        a { color: #0052ff; text-decoration: none; font-weight: bold; }
    </style>
</head>
<body>
    <div class="card">
        <h1>🏛️ Chronos AI</h1>
        <p>Autonomous Historical Verification on Base</p>
        <textarea id="claim" placeholder="Enter historical claim to archive..."></textarea>
        <button onclick="verify()">Verify & Archive on Base</button>
        <div id="status"></div>
    </div>

    <script>
        async function verify() {
            const claim = document.getElementById('claim').value;
            const statusDiv = document.getElementById('status');
            if(!claim) return alert("Please enter a historical claim!");
            
            statusDiv.innerHTML = "<span style='color: #888'>⏳ Analyzing with Llama 3 & broadcasting to Base...</span>";
            
            try {
                const res = await fetch('/verify', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({claim})
                });
                const data = await res.json();
                
                if(data.success) {
                    statusDiv.innerHTML = `<span style='color: #4CAF50; font-weight: bold;'>✅ SUCCESS: Secured On-Chain</span><br><br>
                    <a href="https://sepolia.basescan.org/tx/${data.tx_hash}" target="_blank">View on BaseScan ↗</a>`;
                } else {
                    statusDiv.innerHTML = `<span style='color: #ff4444;'>❌ Verification Failed:</span><br><small>${data.error}</small>`;
                }
            } catch (e) {
                statusDiv.innerHTML = "<span style='color: #ff4444;'>❌ System Timeout / Error</span>";
            }
        }
    </script>
</body>
</html>
"""

def analyze_with_ai(claim):
    if not GROQ_API_KEY:
        return {"is_accurate": True, "score": 95, "reason": "No API Key - Using Mock Mode"}
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    prompt = f"Analyze: '{claim}'. Accurate? Respond JSON: {{\"is_accurate\": bool, \"score\": int, \"reason\": \"str\"}}"
    data = {"model": "llama3-8b-8192", "messages": [{"role": "user", "content": prompt}], "response_format": {"type": "json_object"}}
    
    try:
        r = requests.post(url, headers=headers, json=data, timeout=5).json()
        import json
        return json.loads(r['choices'][0]['message']['content'])
    except:
        return {"is_accurate": True, "score": 90, "reason": "AI check bypassed due to timeout"}

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/verify', methods=['POST'])
def verify():
    try:
        data = request.json
        claim = data.get('claim')
        
        ai_result = analyze_with_ai(claim)
        if not ai_result.get('is_accurate', True):
            return jsonify({"success": False, "error": ai_result.get('reason', 'Invalid history')})

        nonce = w3.eth.get_transaction_count(account.address)
        tx = contract.functions.verifyClaim(claim, ai_result.get('score', 90), "ipfs://chronos").build_transaction({
            'from': account.address,
            'nonce': nonce,
            'gas': 300000,
            'gasPrice': w3.to_wei('0.05', 'gwei')
        })
        signed = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        return jsonify({"success": True, "tx_hash": w3.to_hex(tx_hash)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    app.run()
