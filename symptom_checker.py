import joblib
import numpy as np
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

try:
    model = joblib.load(os.path.join(BASE_DIR, "model.pkl"))
    all_symptoms = joblib.load(os.path.join(BASE_DIR, "symptoms_list.pkl"))
    ML_AVAILABLE = True
    print("ML model loaded successfully!")
except Exception as e:
    print(f"ML model not found, using fallback: {e}")
    ML_AVAILABLE = False
    all_symptoms = [
        "fever", "high fever", "mild fever", "cough", "dry cough", "runny nose",
        "sneezing", "sore throat", "body ache", "muscle pain", "fatigue",
        "weakness", "headache", "severe headache", "chills", "loss of taste",
        "loss of smell", "breathlessness", "shortness of breath", "nausea",
        "vomiting", "diarrhea", "stomach pain", "cramps", "bloating",
        "dizziness", "blurred vision", "chest pain", "high blood pressure",
        "frequent urination", "excessive thirst", "weight loss", "slow healing",
        "itching", "rash", "hives", "swelling", "watery eyes", "burning urination",
        "pelvic pain", "cloudy urine", "lower back pain", "pale skin",
        "cold hands", "brittle nails", "light sensitivity", "sound sensitivity",
        "throbbing pain", "congestion"
    ]
    model = None

DISEASE_INFO = {
    "Common Cold": {
        "medicines": ["Paracetamol 500mg", "Cetirizine 10mg", "Vitamin C supplements"],
        "advice": "Rest well, drink warm fluids, and avoid cold drinks. See a doctor if fever exceeds 102 degrees F.",
        "severity": "mild"
    },
    "Influenza": {
        "medicines": ["Oseltamivir (Tamiflu)", "Paracetamol 650mg", "ORS for hydration"],
        "advice": "Take complete bed rest. Stay hydrated. Consult a doctor immediately if breathing difficulty occurs.",
        "severity": "moderate"
    },
    "COVID-19": {
        "medicines": ["Paracetamol 650mg", "Vitamin D and Zinc supplements", "ORS"],
        "advice": "Isolate yourself. Monitor oxygen levels with a pulse oximeter. Consult a doctor. Get tested immediately.",
        "severity": "high"
    },
    "Migraine": {
        "medicines": ["Sumatriptan", "Ibuprofen 400mg", "Domperidone for nausea"],
        "advice": "Rest in a dark quiet room. Avoid screens. Stay hydrated. See a neurologist if migraines are recurring.",
        "severity": "moderate"
    },
    "Gastroenteritis": {
        "medicines": ["ORS (Oral Rehydration Salts)", "Ondansetron for vomiting", "Metronidazole"],
        "advice": "Drink plenty of fluids. Eat light foods like rice and bananas. Avoid dairy. Visit a doctor if diarrhea lasts more than 2 days.",
        "severity": "moderate"
    },
    "Hypertension": {
        "medicines": ["Amlodipine", "Losartan", "Metoprolol (only as prescribed by doctor)"],
        "advice": "CONSULT A DOCTOR IMMEDIATELY. Reduce salt intake. Do not self-medicate blood pressure drugs.",
        "severity": "high"
    },
    "Diabetes": {
        "medicines": ["Metformin (as prescribed by doctor)", "Insulin if needed", "Vitamin D supplements"],
        "advice": "Monitor blood sugar regularly. Follow a low-sugar diet. Exercise daily. Consult an endocrinologist.",
        "severity": "high"
    },
    "Allergic Reaction": {
        "medicines": ["Cetirizine 10mg", "Loratadine", "Hydrocortisone cream for skin rash"],
        "advice": "Identify and avoid the allergen. If throat swells or breathing becomes difficult, go to emergency immediately.",
        "severity": "moderate"
    },
    "UTI": {
        "medicines": ["Nitrofurantoin", "Trimethoprim", "Increase water intake significantly"],
        "advice": "Drink lots of water. Avoid holding urine. A urine culture test is recommended. See a doctor for antibiotics.",
        "severity": "moderate"
    },
    "Anemia": {
        "medicines": ["Iron supplements (Ferrous Sulfate)", "Vitamin B12", "Folic Acid"],
        "advice": "Eat iron-rich foods like spinach, meat, and lentils. Get a CBC blood test done. Consult a doctor.",
        "severity": "moderate"
    }
}

def extract_symptoms(text):
    text_lower = text.lower()
    found = []
    for symptom in all_symptoms:
        if symptom in text_lower:
            found.append(symptom)
    shortcuts = {
        "temp": "fever", "temperature": "fever",
        "throwing up": "vomiting", "throw up": "vomiting",
        "loose motion": "diarrhea", "loose motions": "diarrhea",
        "loose stool": "diarrhea",
        "cant smell": "loss of smell", "no smell": "loss of smell", "lost smell": "loss of smell",
        "cant taste": "loss of taste", "no taste": "loss of taste", "lost taste": "loss of taste",
        "bp high": "high blood pressure", "high bp": "high blood pressure",
        "tired": "fatigue", "very tired": "fatigue", "exhausted": "fatigue",
        "burning pee": "burning urination", "pain while urinating": "burning urination",
        "frequent pee": "frequent urination", "peeing a lot": "frequent urination",
        "heavy head": "headache", "head pain": "headache", "head ache": "headache",
        "chest tight": "chest pain", "tightness in chest": "chest pain",
        "short of breath": "shortness of breath", "hard to breathe": "breathlessness",
        "cant breathe": "breathlessness", "difficulty breathing": "breathlessness",
        "stomach ache": "stomach pain", "tummy ache": "stomach pain",
        "feeling cold": "chills", "shivering": "chills",
        "feeling weak": "weakness", "no energy": "fatigue",
        "throat pain": "sore throat", "throat ache": "sore throat"
    }
    for phrase, mapped in shortcuts.items():
        if phrase in text_lower and mapped not in found:
            found.append(mapped)
    return list(set(found))

def predict_disease(user_symptoms):
    if not user_symptoms:
        return None
    if not ML_AVAILABLE:
        return _fallback_predict(user_symptoms)
    vector = [0] * len(all_symptoms)
    matched = 0
    for sym in user_symptoms:
        if sym in all_symptoms:
            vector[all_symptoms.index(sym)] = 1
            matched += 1
    if matched == 0:
        return _fallback_predict(user_symptoms)
    vector = np.array(vector).reshape(1, -1)
    prediction = model.predict(vector)[0]
    probabilities = model.predict_proba(vector)[0]
    classes = model.classes_
    prob_dict = dict(zip(classes, probabilities))
    sorted_preds = sorted(prob_dict.items(), key=lambda x: x[1], reverse=True)
    top_disease = sorted_preds[0][0]
    top_confidence = round(sorted_preds[0][1] * 100, 1)
    if top_confidence < 20:
        return None
    info = DISEASE_INFO.get(top_disease, {
        "medicines": ["Please consult a doctor"],
        "advice": "Your symptoms need professional evaluation.",
        "severity": "moderate"
    })
    top3 = []
    for disease, prob in sorted_preds[:3]:
        if prob > 0.05:
            top3.append({"disease": disease, "confidence": round(prob * 100, 1)})
    return {
        "disease": top_disease,
        "confidence": top_confidence,
        "medicines": info["medicines"],
        "advice": info["advice"],
        "severity": info["severity"],
        "top3": top3
    }

def _fallback_predict(user_symptoms):
    FALLBACK_MAP = {
        "Common Cold": ["runny nose", "sneezing", "sore throat", "cough", "mild fever", "congestion"],
        "Influenza": ["high fever", "body ache", "fatigue", "chills", "muscle pain"],
        "COVID-19": ["dry cough", "loss of taste", "loss of smell", "breathlessness", "fever"],
        "Migraine": ["severe headache", "nausea", "light sensitivity", "throbbing pain"],
        "Gastroenteritis": ["diarrhea", "vomiting", "stomach pain", "cramps", "nausea"],
        "Hypertension": ["high blood pressure", "blurred vision", "chest pain", "dizziness"],
        "Diabetes": ["frequent urination", "excessive thirst", "slow healing", "fatigue"],
        "Allergic Reaction": ["itching", "rash", "hives", "swelling", "watery eyes"],
        "UTI": ["burning urination", "pelvic pain", "cloudy urine", "frequent urination"],
        "Anemia": ["pale skin", "cold hands", "brittle nails", "weakness", "fatigue"]
    }
    scores = {}
    for disease, syms in FALLBACK_MAP.items():
        count = sum(1 for s in user_symptoms if s in syms)
        if count > 0:
            scores[disease] = count / len(syms)
    if not scores:
        return None
    best = max(scores, key=scores.get)
    conf = round(scores[best] * 100, 1)
    if conf < 15:
        return None
    info = DISEASE_INFO[best]
    return {
        "disease": best,
        "confidence": conf,
        "medicines": info["medicines"],
        "advice": info["advice"],
        "severity": info["severity"],
        "top3": [{"disease": best, "confidence": conf}]
    }