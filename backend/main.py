from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from models import HCP, Interaction, engine, Base, get_db, SessionLocal
from agent import agent
from langchain_core.messages import HumanMessage
import uvicorn

# Initialize and Seed Database
try:
    Base.metadata.create_all(bind=engine)
    def seed_db():
        db = SessionLocal()
        if db.query(HCP).count() == 0:
            hcps = [
                HCP(name="Dr. Sarah Miller", specialty="Oncology", location="New York", email="sarah.miller@hospital.com"),
                HCP(name="Dr. James Wilson", specialty="Cardiology", location="Chicago", email="james.wilson@clinic.org"),
                HCP(name="Dr. Emily Chen", specialty="Neurology", location="San Francisco", email="emily.chen@health.edu")
            ]
            db.add_all(hcps)
            db.commit()
            print("Database seeded successfully.")
        db.close()
    seed_db()
except Exception as e:
    print(f"Warning: Database initialization failed: {e}")
    print("The app will continue but non-AI features and persistence may be limited.")

app = FastAPI(title="AI-First CRM API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Schemas ---

class HCPBase(BaseModel):
    name: str
    specialty: str
    location: str
    email: str

class HCPCreate(HCPBase):
    pass

class HCPResponse(HCPBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class InteractionBase(BaseModel):
    hcp_id: int
    type: str
    summary: Optional[str]
    sentiment: Optional[str]
    raw_transcript: Optional[str]

class InteractionCreate(InteractionBase):
    pass

class ChatRequest(BaseModel):
    message: str
    hcp_id: Optional[int] = None

# --- Endpoints ---

@app.get("/hcps", response_model=List[HCPResponse])
def get_hcps(db: Session = Depends(get_db)):
    return db.query(HCP).all()

@app.post("/hcps", response_model=HCPResponse)
def create_hcp(hcp: HCPCreate, db: Session = Depends(get_db)):
    db_hcp = HCP(**hcp.dict())
    db.add(db_hcp)
    db.commit()
    db.refresh(db_hcp)
    return db_hcp

@app.get("/interactions/{hcp_id}")
def get_interactions(hcp_id: int, db: Session = Depends(get_db)):
    return db.query(Interaction).filter(Interaction.hcp_id == hcp_id).all()

@app.post("/chat")
async def chat_with_agent(request: ChatRequest, db: Session = Depends(get_db)):
    try:
        # Invoke LangGraph agent
        input_state = {
            "messages": [HumanMessage(content=request.message)],
            "hcp_id": request.hcp_id or 0,
            "interaction_id": 0
        }
        result = agent.invoke(input_state)
        # get the last message from the agent
        ai_message = result['messages'][-1].content
        return {"response": ai_message}
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        error_msg = str(e)
        if "API_KEY" in error_msg or "401" in error_msg:
            error_msg = "Invalid or missing GROQ_API_KEY. Please update your backend/.env file."
        raise HTTPException(status_code=500, detail=error_msg)

@app.post("/interactions")
def log_interaction(interaction: InteractionCreate, db: Session = Depends(get_db)):
    db_interaction = Interaction(**interaction.dict())
    db.add(db_interaction)
    db.commit()
    db.refresh(db_interaction)
    return db_interaction

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
