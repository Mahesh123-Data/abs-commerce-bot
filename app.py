from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
import logging

load_dotenv()
app = Flask(__name__)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PHONE_NUMBER_ID = os.getenv('PHONE_NUMBER_ID')
WEBHOOK_VERIFY_TOKEN = os.getenv('WEBHOOK_VERIFY_TOKEN')
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')

@app.route('/', methods=['GET'])
def home():
    return "WhatsApp Bot LIVE! 🚀"

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        # Verification
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        
        logger.info(f"Verification: mode={mode}, token={token}")
        
        if mode == 'subscribe' and token == WEBHOOK_VERIFY_TOKEN:
            logger.info("✅ Webhook verified!")
            return challenge  # ← EXACT YEHI!
        
        return 'Forbidden', 403
    
    if request.method == 'POST':
        # Message received
        data = request.get_json()
        logger.info(f"📨 Message received: {data}")
        return jsonify({"status": "success"}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=True)
