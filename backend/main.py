from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from models import HCP, Interaction, engine, Base, get_db, SessionLocal
from agent import agent
from langchain_core.messages import HumanMessage, AIMessage

import uvicorn
import json

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
    date: Optional[str] = None
    time: Optional[str] = None
    attendees: Optional[str] = None
    topics_discussed: Optional[str] = None
    summary: Optional[str] = None
    sentiment: Optional[str] = None
    materials_shared: Optional[List[str]] = None
    samples_distributed: Optional[List[str]] = None
    outcomes: Optional[str] = None
    next_steps: Optional[str] = None
    raw_transcript: Optional[str] = None


class InteractionCreate(InteractionBase):
    pass

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    hcp_id: Optional[int] = None
    history: Optional[List[ChatMessage]] = None

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
        # Map history to langchain messages
        past_messages = []
        if request.history:
            for msg in request.history:
                if msg.role == 'user':
                    past_messages.append(HumanMessage(content=msg.content))
                else:
                    past_messages.append(AIMessage(content=msg.content))

        # Extract last interaction_id from history to maintain context
        interaction_id = 0
        if request.history:
            for msg in reversed(request.history):
                if msg.role == 'ai' and "Interaction logged successfully with ID" in msg.content:
                    try:
                        interaction_id = int(msg.content.split("ID")[1].split(".")[0].strip())
                        break
                    except:
                        pass

        # Invoke LangGraph agent
        input_state = {
            "messages": past_messages + [HumanMessage(content=request.message)],
            "hcp_id": request.hcp_id or 0,
            "interaction_id": interaction_id
        }
        result = agent.invoke(input_state)
        
        # Extract the text response and check for UI_UPDATE_DATA
        ai_message = ""
        all_ui_updates = {}
        
        # Look through all messages in the result to find tool outputs or agent markers
        for msg in result['messages']:
            content = msg.content if hasattr(msg, 'content') else str(msg)
            
            if "UI_UPDATE_DATA:" in content:
                try:
                    json_str = content.split("UI_UPDATE_DATA:")[1].strip()
                    # Clean markdown if present
                    json_str = json_str.replace('```json', '').replace('```', '').strip()
                    update_data = json.loads(json_str)
                    if isinstance(update_data, dict):
                        all_ui_updates.update(update_data)
                except Exception as e:
                    print(f"Error parsing UI_UPDATE_DATA: {e}")

            # Use the last AIMessage as the actual text response
            if isinstance(msg, (AIMessage, str)) or (hasattr(msg, 'role') and msg.role == 'ai'):
               if content and "UI_UPDATE_DATA:" not in content[:50]: # Avoid tool-only messages
                   ai_message = content.split("UI_UPDATE_DATA:")[0].strip()

        # Fallback if no clean AI message found
        if not ai_message:
            last_msg = result['messages'][-1]
            ai_message = last_msg.content.split("UI_UPDATE_DATA:")[0].strip() if hasattr(last_msg, 'content') else str(last_msg)

        # If we found update data, ensure it's in the final response
        final_response = ai_message
        if all_ui_updates:
            final_response += f"\n\nUI_UPDATE_DATA: {json.dumps(all_ui_updates)}"

        return {"response": final_response}

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
