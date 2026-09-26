from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import auth, health_records, medical_reports, medications, ai_screening

app = FastAPI(title="MEDI-TRACK AI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8081", 
        "http://127.0.0.1:8081", 
        "http://172.19.134.129:8081"
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "MEDI-TRACK AI backend is running"}

app.include_router(auth.router)
app.include_router(health_records.router)
app.include_router(medical_reports.router)
app.include_router(medications.router)
app.include_router(ai_screening.router)