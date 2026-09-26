import os
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel
from typing import List

from .auth import get_current_user
from database import get_db
import models

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

router = APIRouter(
    prefix="/ai-screening",
    tags=["AI Screening"]
)

if not api_key:
    client = None
else:
    client = genai.Client(api_key=api_key)

# --- Pydantic Models for JSON Validation ---
class Reason(BaseModel):
    factor: str
    detail: str

class RiskAssessmentSchema(BaseModel):
    flagged: bool
    summary: str
    reasons: List[Reason]

# --- 1. Daily Quick Insight Endpoint ---
@router.get("/")
def generate_health_insight(
    current_user=Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    if not client:
        raise HTTPException(status_code=500, detail="AI Client is not configured. Check GEMINI_API_KEY in .env")
        
    latest_record = db.query(models.HealthRecord).filter(
        models.HealthRecord.user_id == current_user.id
    ).order_by(models.HealthRecord.recorded_at.desc()).first()
    
    if latest_record:
        vitals = []
        if latest_record.heart_rate:
            vitals.append(f"Heart Rate: {latest_record.heart_rate} bpm")
        if latest_record.systolic_bp and latest_record.diastolic_bp:
            vitals.append(f"Blood Pressure: {latest_record.systolic_bp}/{latest_record.diastolic_bp}")
        if latest_record.sleep_hours:
            vitals.append(f"Sleep: {latest_record.sleep_hours} hours")
            
        vitals_str = ", ".join(vitals)
        
        prompt = (
            f"Provide a brief, one-sentence encouraging health tip for {current_user.full_name}. "
            f"Base your advice specifically on these recent vitals: {vitals_str}. "
            "Keep the tone warm and supportive, but make sure to address the specific metrics. "
            "Do not refuse to answer; provide general wellness advice if the metrics are abnormal."
        )
    else:
        prompt = f"Provide a brief, one-sentence encouraging health tip for {current_user.full_name}, reminding them to start tracking their daily health metrics."
    
    try:
        response = client.models.generate_content(
            model='gemini-3.5-flash-lite',
            contents=prompt,
            config={"safety_settings": [{"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}]}
        )
        if not response.text:
            raise ValueError("Empty response from AI")
            
        return {"insight": response.text}
    except Exception as e:
        print(f"\n=== GEMINI ERROR ===: {e}\n")
        return {"insight": f"{current_user.full_name}, your vitals indicate you should take it easy today. Please consult a doctor if you are feeling unwell."}

# --- 2. Long-Term Risk Assessment Endpoint ---
@router.get("/risk", response_model=RiskAssessmentSchema)
def analyze_health_risk(
    current_user=Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    if not client:
        raise HTTPException(status_code=500, detail="AI Client is not configured.")

    records = db.query(models.HealthRecord).filter(
        models.HealthRecord.user_id == current_user.id
    ).order_by(models.HealthRecord.recorded_at.desc()).limit(30).all()

    if not records:
        return {
            "flagged": False, 
            "summary": "Not enough health records logged yet to detect a pattern.", 
            "reasons": []
        }

    history_text = "\n".join([
        f"Date: {str(r.recorded_at).split(' ')[0]}, "
        f"Heart Rate: {r.heart_rate or 'N/A'} bpm, "
        f"Blood Pressure: {r.systolic_bp or 'N/A'}/{r.diastolic_bp or 'N/A'}, "
        f"Sleep: {r.sleep_hours or 'N/A'} hours"
        for r in records
    ])

    prompt = f"""
    You are an AI health assistant. Analyze the following 30-day health record history for {current_user.full_name}.
    Identify any concerning long-term patterns (e.g., consistently elevated heart rate, chronic low sleep, or hypertension trends).
    
    Respond ONLY with a valid JSON object matching this exact schema:
    {{
        "flagged": true/false (true if a concerning pattern is found across multiple days),
        "summary": "A 1-2 sentence summary of the risk assessment.",
        "reasons": [
            {{"factor": "Name of the metric (e.g., Sleep, Blood Pressure)", "detail": "Explanation of the trend."}}
        ]
    }}
    
    Health History:
    {history_text}
    """

    try:
        response = client.models.generate_content(
            model='gemini-3.5-flash-lite',
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "safety_settings": [{"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}]
            }
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"\n=== GEMINI RISK ERROR ===: {e}\n")
        return {
            "flagged": True,
            "summary": "We detected potentially abnormal readings in your recent records, but detailed AI analysis is temporarily unavailable.",
            "reasons": [{"factor": "Vitals", "detail": "Please review your recent logs or consult a doctor."}]
        }