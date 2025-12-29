from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os
import requests
import json
from datetime import datetime
import logging

load_dotenv()

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

WHATSAPP_API_URL = "https://graph.instagram.com/v18.0"
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
WEBHOOK_VERIFY_TOKEN = os.getenv("WEBHOOK_VERIFY_TOKEN", "abs_webhook_token_123")
@app.route('/')
def home():
    return "✅ ABS Commerce Bot LIVE!"

ROADMAPS = {
    '1': {
        'title': '📊 CHARTERED ACCOUNTANCY (CA)',
        'duration': '4.5 years',
        'path': '12th → Foundation → Intermediate → Final',
        'skills': 'Accounting, Auditing, Taxation, GST, Financial Management',
        'salary': '₹3-50L',
        'companies': 'Big 4 (Deloitte, KPMG, EY, PwC), CA Firms'
    },
    '2': {
        'title': '📋 COMPANY SECRETARY (CS)',
        'duration': '4.5 years',
        'path': '12th → Foundation → Executive → Professional',
        'skills': 'Corporate Law, Compliance, Governance, Risk Management',
        'salary': '₹2.5-40L',
        'companies': 'Corporate, Law Firms, Banks'
    },
    '3': {
        'title': '💰 COST ACCOUNTANCY (CMA)',
        'duration': '4.5 years',
        'path': '12th → Foundation → Intermediate → Final',
        'skills': 'Cost Accounting, Management Accounting, Budgeting',
        'salary': '₹2-35L',
        'companies': 'Manufacturing, Hospitals, Banks'
    },
    '4': {
        'title': '🏦 BANKING & FINANCE',
        'duration': '3-4 years',
        'path': 'Degree → Exams → Bank → Specialization',
        'skills': 'Banking Ops, Credit Analysis, Risk Management',
        'salary': '₹2.5-25L',
        'companies': 'SBI, ICICI, HDFC, Axis, Private Banks'
    },
    '5': {
        'title': '👔 MBA (Business Admin)',
        'duration': '2 years',
        'path': 'Degree → CAT/XAT → MBA → Corporate',
        'skills': 'Strategy, Finance, Marketing, Leadership',
        'salary': '₹8-50L',
        'companies': 'Top B-Schools, MNCs, Consulting, Tech'
    }
}

user_states = {}

@app.route('/webhook', methods=['GET'])
def webhook_get():
    challenge = request.args.get('hub.challenge')
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    
    if mode == 'subscribe' and token == WEBHOOK_VERIFY_TOKEN:
        logger.info("✅ Webhook verified!")
        return challenge
    
    return 'Forbidden', 403

@app.route('/webhook', methods=['POST'])
def webhook_post():
    try:
        data = request.get_json()
        
        if data['object'] == 'whatsapp_business_account':
            for entry in data['entry']:
                for change in entry['changes']:
                    if change['field'] == 'messages':
                        message_data = change['value']
                        
                        if 'messages' in message_data:
                            for message in message_data['messages']:
                                sender_id = message['from']
                                message_text = message['text']['body'] if 'text' in message else ''
                                process_message(sender_id, message_text)
                        
                        if 'messages' in message_data:
                            message_id = message_data['messages'][0]['id']
                            mark_as_read(message_id)
        
        return 'ok', 200
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return 'ok', 200

def process_message(sender_id, message_text):
    message_text = message_text.strip()
    logger.info(f"Message from {sender_id}: {message_text}")
    
    if sender_id not in user_states:
        user_states[sender_id] = {
            'state': 'START',
            'data': {'phone': sender_id},
            'timestamp': datetime.now().isoformat()
        }
        send_message(sender_id, '🎓 *Welcome to ABS Commerce Guidance!*\n\nDiscover YOUR perfect path in 5 mins.\n\n👉 Reply your *NAME*')
        return
    
    state = user_states[sender_id]['state']
    
    if state == 'START':
        user_states[sender_id]['data']['name'] = message_text
        user_states[sender_id]['state'] = 'NAME_COLLECTED'
        send_message(sender_id, f"Nice to meet you, {message_text}! 👋\n\nWhat's your *AGE*?")
    
    elif state == 'NAME_COLLECTED':
        user_states[sender_id]['data']['age'] = message_text
        user_states[sender_id]['state'] = 'AGE_COLLECTED'
        send_message(sender_id, 'Perfect! Which commerce field interests you?\n\n1️⃣ CA\n2️⃣ CS\n3️⃣ CMA\n4️⃣ Banking\n5️⃣ MBA\n6️⃣ All\n\nReply (1-6)')
    
    elif state == 'AGE_COLLECTED':
        if message_text not in ['1', '2', '3', '4', '5', '6']:
            send_message(sender_id, '❌ Invalid! Reply 1-6')
            return
        
        user_states[sender_id]['data']['interest'] = message_text
        user_states[sender_id]['state'] = 'INTEREST_COLLECTED'
        send_message(sender_id, 'What\'s your goal?\n\n1️⃣ Career\n2️⃣ Exam Prep\n3️⃣ Courses\n4️⃣ Skills\n5️⃣ All\n\nReply (1-5)')
    
    elif state == 'INTEREST_COLLECTED':
        if message_text not in ['1', '2', '3', '4', '5']:
            send_message(sender_id, '❌ Invalid! Reply 1-5')
            return
        
        user_states[sender_id]['data']['goal'] = message_text
        user_states[sender_id]['state'] = 'GOAL_COLLECTED'
        send_message(sender_id, '⏳ Generating roadmap...')
        
        generate_roadmap(sender_id, message_text)
    
    elif state == 'ROADMAP_SENT':
        if message_text == '1':
            user_states[sender_id]['data']['interested_in_call'] = True
            save_lead(sender_id, user_states[sender_id]['data'])
            send_message(sender_id, '✅ Saved! Counselor calling in 2 hours! 📞')
            user_states[sender_id]['state'] = 'FINISHED'
        elif message_text == '2':
            user_states[sender_id]['data']['interested_in_call'] = False
            save_lead(sender_id, user_states[sender_id]['data'])
            send_message(sender_id, 'Thanks! Good luck! 🚀')
            user_states[sender_id]['state'] = 'FINISHED'

def generate_roadmap(sender_id, interest_choice):
    try:
        if interest_choice == '6':
            for key in ['1', '2', '3', '4', '5']:
                roadmap = ROADMAPS[key]
                msg = f"*{roadmap['title']}*\n⏱️ {roadmap['duration']}\n🛤️ {roadmap['path']}\n📚 {roadmap['skills']}\n💰 {roadmap['salary']}\n🏢 {roadmap['companies']}"
                send_message(sender_id, msg)
        else:
            roadmap = ROADMAPS.get(interest_choice)
            if roadmap:
                user_states[sender_id]['data']['roadmap'] = roadmap['title']
                msg = f"*{roadmap['title']}*\n⏱️ {roadmap['duration']}\n🛤️ {roadmap['path']}\n📚 {roadmap['skills']}\n💰 {roadmap['salary']}\n🏢 {roadmap['companies']}"
                send_message(sender_id, msg)
        
        user_states[sender_id]['state'] = 'ROADMAP_SENT'
        send_message(sender_id, '✨ Ready! Counselor call?\n\n1️⃣ YES\n2️⃣ No\n\nReply (1-2)')
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        send_message(sender_id, '❌ Error. Try again.')

def send_message(recipient_id, message_text):
    try:
        headers = {
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        
        data = {
            "messaging_product": "whatsapp",
            "to": recipient_id,
            "type": "text",
            "text": {"body": message_text}
        }
        
        url = f"{WHATSAPP_API_URL}/{PHONE_NUMBER_ID}/messages"
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code == 200:
            logger.info(f"✅ Sent to {recipient_id}")
            return True
        else:
            logger.error(f"❌ Failed: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return False

def mark_as_read(message_id):
    try:
        headers = {
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        
        data = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id
        }
        
        url = f"{WHATSAPP_API_URL}/{PHONE_NUMBER_ID}/messages"
        requests.post(url, json=data, headers=headers)
    except Exception as e:
        logger.error(f"Error: {str(e)}")

def save_lead(sender_id, student_data):
    try:
        lead_data = {
            'phone': sender_id,
            'timestamp': datetime.now().isoformat(),
            **student_data
        }
        
        logger.info(f"✅ Lead saved: {json.dumps(lead_data, indent=2)}")
    except Exception as e:
        logger.error(f"Error: {str(e)}")

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': '✅ ABS Commerce Bot running!'}), 200

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
