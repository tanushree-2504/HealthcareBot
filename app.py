from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from symptom_checker import predict_disease, extract_symptoms

app = Flask(__name__)
CORS(app)

conversation_store = {}

GREETINGS = ["hi", "hello", "hey", "good morning", "good evening", "hii", "helo", "namaste", "hiya"]
THANKS = ["thank you", "thanks", "thank u", "thnks", "ty", "thankyou", "thx"]
EMERGENCY_KEYWORDS = [
    "chest pain", "cant breathe", "not breathing", "unconscious",
    "loss of consciousness", "heart attack", "stroke", "severe bleeding",
    "paralysis", "seizure", "fitting", "fainted", "collapsed"
]

def is_emergency(text):
    t = text.lower()
    return any(kw in t for kw in EMERGENCY_KEYWORDS)

def build_result_message(result, name):
    sev_emoji = {"mild": "🟡", "moderate": "🟠", "high": "🔴"}.get(result["severity"], "⚪")
    meds = "\n".join([f"• {m}" for m in result["medicines"]])
    
    top3_text = ""
    if result.get("top3") and len(result["top3"]) > 1:
        top3_text = "\n\n🔎 Other possible conditions (lower probability):\n"
        for item in result["top3"][1:]:
            top3_text += f"• {item['disease']} — {item['confidence']}%\n"
            
    # FIXED: Using a safe native f-string without the trailing % operator to avoid the 500 crash
    return f"""🩺 AI Health Analysis for {name}

━━━━━━━━━━━━━━━━━━━━━
Symptoms analyzed: {', '.join(result.get('symptoms', []))}
━━━━━━━━━━━━━━━━━━━━━

🔬 ML Model Prediction
Most likely condition: {result['disease']}
Confidence score: {result['confidence']}%
Severity level: {sev_emoji} {result['severity'].capitalize()}{top3_text}

━━━━━━━━━━━━━━━━━━━━━

💊 Suggested Medications:
{meds}

━━━━━━━━━━━━━━━━━━━━━

📋 Health Advice:
{result['advice']}

━━━━━━━━━━━━━━━━━━━━━

⚠ This is an AI-based preliminary assessment using a Random Forest classifier. Please consult a certified doctor before taking any medication.

Type restart to begin a new consultation."""

def get_response(message, session_id):
    msg = message.lower().strip()

    if session_id not in conversation_store:
        conversation_store[session_id] = {"symptoms": [], "stage": "start", "name": ""}

    state = conversation_store[session_id]

    if is_emergency(message) and state["stage"] not in ["start"]:
        return {
            "message": "🚨 EMERGENCY ALERT\n\nYour symptoms suggest a potentially serious condition.\n\nPlease call 112 (emergency services) or go to the nearest hospital IMMEDIATELY.\n\nDo NOT wait. Do NOT self-medicate.",
            "type": "emergency"
        }

    if any(w in msg for w in ["restart", "start over", "new consultation", "reset", "new chat"]):
        conversation_store[session_id] = {"symptoms": [], "stage": "start", "name": ""}
        return {
            "message": "🔄 Restarted! Hello again! I am MediBot, your AI healthcare assistant.\n\nMay I know your name?",
            "type": "restart"
        }

    if any(t in msg for t in THANKS):
        return {
            "message": "You are welcome! 😊 Take care of yourself and please visit a doctor if your symptoms persist or worsen.\n\nType restart to begin a new consultation.",
            "type": "thanks"
        }

    if any(g in msg for g in GREETINGS) or state["stage"] == "start":
        state["stage"] = "ask_name"
        return {
            "message": "👋 Hello! I am MediBot, your AI-powered healthcare assistant.\n\nI use a Random Forest machine learning model trained on symptom-disease data to analyze your condition and provide preliminary health guidance.\n\n⚠ I am NOT a replacement for a real doctor. Always consult a certified medical professional.\n\nMay I know your name?",
            "type": "greeting"
        }

    if state["stage"] == "ask_name":
        name = message.strip().split()[0].capitalize()
        state["name"] = name
        state["stage"] = "ask_symptoms"
        return {
            "message": f"Nice to meet you, {name}! 😊\n\nPlease describe your symptoms in detail. You can type naturally.\n\nFor example: I have a headache, high fever, and feel very tired\n\nWhat symptoms are you experiencing?",
            "type": "ask_symptoms"
        }

    if state["stage"] in ["ask_symptoms", "collecting"]:
        if any(w in msg for w in ["done", "check", "analyze", "diagnose", "result", "predict", "thats all", "that is all", "nothing else"]):
            state["stage"] = "force_done"
        else:
            extracted = extract_symptoms(message)
            if extracted:
                state["symptoms"].extend(extracted)
                state["symptoms"] = list(set(state["symptoms"]))
                state["stage"] = "collecting"
                return {
                    "message": f"✅ I noted: {', '.join(extracted)}\n\nTotal symptoms recorded: {', '.join(state['symptoms'])}\n\nDo you have any other symptoms? Or type done to get your full AI health analysis.",
                    "type": "collecting",
                    "symptoms_found": extracted
                }
            else:
                return {
                    "message": "I could not detect specific symptoms from that. Please use words like: fever, headache, cough, nausea, fatigue, dizziness, rash, chills, vomiting, etc.\n\nWhat are you feeling?",
                    "type": "clarify"
                }

    if state["stage"] in ["collecting", "force_done"] or any(w in msg for w in ["done", "check", "analyze", "diagnose", "result"]):
        extra = extract_symptoms(message)
        if extra:
            state["symptoms"].extend(extra)
            state["symptoms"] = list(set(state["symptoms"]))

        if not state["symptoms"]:
            return {
                "message": "I do not have any symptoms recorded yet. Please tell me what you are feeling first.",
                "type": "error"
            }

        result = predict_disease(state["symptoms"])
        name = state.get("name", "you")
        state["stage"] = "done"
        
        # FIXED: Added fallback checking so if the model doesn't find a match, it won't crash
        if result and isinstance(result, dict):
            result["symptoms"] = state["symptoms"]
            return {
                "message": build_result_message(result, name),
                "type": "result",
                "severity": result.get("severity", "mild")
            }
        else:
            return {
                "message": f"Based on your symptoms ({', '.join(state['symptoms'])}), the ML model could not confidently identify a specific condition.\n\n🏥 Please visit a doctor for a proper physical examination. Some conditions require tests that AI cannot replace.\n\nType restart to try again with different symptoms.",
                "type": "no_match",
                "severity": "mild"
            }

    return {
        "message": "I am not sure I understood that. Could you describe your symptoms more clearly?\n\nFor example: I have fever, headache, and body ache",
        "type": "fallback"
    }

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"message": "Invalid request.", "type": "error"}), 400
        user_message = data.get("message", "").strip()
        session_id = data.get("session_id", "default")
        if not user_message:
            return jsonify({"message": "Please type something.", "type": "error"}), 400
        response = get_response(user_message, session_id)
        return jsonify(response)
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"message": "Something went wrong. Please refresh and try again.", "type": "error"}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)