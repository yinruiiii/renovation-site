from flask import Flask, render_template, request, jsonify
from anthropic import Anthropic
from dotenv import load_dotenv
import os, csv, datetime, re

load_dotenv()

app = Flask(__name__)
client = Anthropic()

SYSTEM_PROMPT = """You are a friendly assistant for WL Building Solutions, 
a residential and commercial renovation company based in Melbourne, Australia.

Your two jobs are:
1. Answer questions about the company's services (kitchens, bathrooms, extensions, 
   commercial fitouts, decking, carpentry)
2. Collect leads by getting the visitor's name, phone number, and project details

Services offered:
- Kitchen renovations
- Bathroom renovations  
- Home extensions
- Commercial fitouts
- Decking and pergolas
- General carpentry

Location: Melbourne, VIC — servicing all suburbs
Phone: (+61) 422 335 986
Email: willbuildingsolution@gmail.com
Hours: Mon-Fri 7am-6pm, Sat 8am-2pm

When collecting leads:
- Ask for their name naturally in conversation
- Ask for their phone number or email
- Ask what type of project they have in mind
- Once you have these details, tell them the team will be in touch soon
- Always be warm, professional and helpful

Never make up prices — say "we'd love to give you a free quote based on your specific project"
"""

conversation_history = []

def save_to_csv(filename, row):
    file_exists = os.path.exists(filename)
    with open(filename, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Timestamp", "Name", "Phone", "Email", "Project Type", "Message"])
        writer.writerow(row)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/services")
def services():
    return render_template("services.html")

@app.route("/gallery")
def gallery():
    return render_template("gallery.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/submit-contact", methods=["POST"])
def submit_contact():
    data = request.json
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    save_to_csv("leads.csv", [
        timestamp,
        data.get("name", ""),
        data.get("phone", ""),
        data.get("email", ""),
        data.get("project_type", ""),
        data.get("message", "")
    ])
    return jsonify({"status": "ok"})

@app.route("/chat", methods=["POST"])
def chat():
    global conversation_history
    
    data = request.json
    user_message = data.get("message", "")
    
    conversation_history.append({
        "role": "user",
        "content": user_message
    })
    
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=500,
        system=SYSTEM_PROMPT,
        messages=conversation_history
    )
    
    assistant_message = response.content[0].text
    
    conversation_history.append({
        "role": "assistant", 
        "content": assistant_message
    })

    # Save lead if phone number detected
    phone_pattern = r'04\d{2}\s?\d{3}\s?\d{3}|04\d{8}'
    if re.search(phone_pattern, user_message):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        save_to_csv("leads.csv", [
            timestamp, "via chat", user_message, "", "", ""
        ])
    
    return jsonify({"reply": assistant_message})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)