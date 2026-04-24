import os
from typing import TypedDict, Annotated, List, Union
from langchain_groq import ChatGroq
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langchain_core.tools import tool
from sqlalchemy.orm import Session
from models import HCP, Interaction, SessionLocal
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# LLM setup
llm = ChatGroq(model="llama-3.1-8b-instant", groq_api_key=os.getenv("GROQ_API_KEY"))


# State definition
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], lambda x, y: x + y]
    hcp_id: int
    interaction_id: int

# --- Tools ---

@tool
def log_interaction(hcp_id: Union[int, str], interaction_type: str, raw_text: str):
    """
    Saves a new interaction log to the database.
    Inputs: hcp_id, interaction_type (Meeting/Call/Email), raw_text (details).
    """
    db = SessionLocal()
    try:
        try:
            hcp_id = int(hcp_id)
        except:
            return f"Error: Invalid hcp_id '{hcp_id}'. Must be an integer."
            
        hcp = db.query(HCP).filter(HCP.id == hcp_id).first()
        if not hcp:
            return f"Error: HCP with ID {hcp_id} not found."
            
        extraction_prompt = (
            f"Extract structured data from this CRM interaction log:\n\n{raw_text}\n\n"
            "Return ONLY a valid, plain JSON object (no markdown, no extra text) with double-quoted keys and values. "
            "Fields: date (YYYY-MM-DD), time (HH:mm), attendees, topics_discussed, summary, sentiment (Positive/Neutral/Negative), "
            "materials_shared (list), samples_distributed (list), outcomes, next_steps. "
            "IMPORTANT: If 'outcomes' is null or missing in the text, GENERATE a brief professional outcome based on the discussion and sentiment. "
            "If unknown, use null."
        )

        response = llm.invoke([HumanMessage(content=extraction_prompt)])
        # We will wrap the response in a special tag so the frontend can catch it.
        
        new_interaction = Interaction(
            hcp_id=hcp_id,
            type=interaction_type,
            raw_transcript=raw_text,
            sentiment="Neutral", # Default
            date=datetime.utcnow()
        )
        db.add(new_interaction)
        db.commit()
        db.refresh(new_interaction)
        return f"Interaction logged successfully with ID {new_interaction.id}. UI_UPDATE_DATA: {response.content}"
    finally:
        db.close()

@tool
def edit_interaction(interaction_id: Union[int, str], field: str, value: str):
    """
    Updates a specific field in an existing interaction log.
    Fields: date, time, attendees, topics_discussed, sentiment, outcomes, next_steps.
    """
    db = SessionLocal()
    try:
        try:
            interaction_id = int(interaction_id)
        except:
            return f"Error: Invalid interaction_id '{interaction_id}'. Must be an integer."
            
        interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
        if interaction:
            setattr(interaction, field, value)
            db.commit()
            return f"Updated {field} for interaction {interaction_id}. UI_UPDATE_DATA: {{\"{field}\": \"{value}\"}}"
        return "Interaction not found"
    finally:
        db.close()

@tool
def get_hcp_info(hcp_name: str):
    """
    Retrieves profile and history for a specific HCP.
    """
    db = SessionLocal()
    try:
        hcp = db.query(HCP).filter(HCP.name.ilike(f"%{hcp_name}%")).first()
        if hcp:
            history = db.query(Interaction).filter(Interaction.hcp_id == hcp.id).all()
        if hcp:
            history = db.query(Interaction).filter(Interaction.hcp_id == hcp.id).all()
            return f"HCP Profile: Name={hcp.name}, Specialty={hcp.specialty}, History Count={len(history)}"
        return "HCP not found"
    finally:
        db.close()

@tool
def generate_followup(interaction_id: Union[int, str]):
    """
    Generates a personalized follow-up email/task based on the interaction.
    """
    db = SessionLocal()
    try:
        try:
            interaction_id = int(interaction_id)
        except:
            return f"Error: Invalid interaction_id '{interaction_id}'. Must be an integer."
            
        interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
        if not interaction:
            return "Interaction not found"
        
        prompt = f"Based on this interaction: '{interaction.summary}', generate a professional follow-up email for the HCP."
        response = llm.invoke([HumanMessage(content=prompt)])
        return response.content
    finally:
        db.close()

@tool
def search_materials(query: str):
    """
    Searches for relevant product brochures or scientific papers.
    """
    # Simulated search
    materials = [
        "OncoBoost Phase III Clinical Trial Summary.pdf",
        "Efficacy of Product X in Post-Op Recovery.docx",
        "HCP Presentation - Q4 2025.pptx"
    ]
    results = [m for m in materials if query.lower() in m.lower()]
    return ", ".join(results) if results else "No matching materials found."

from langgraph.prebuilt import ToolNode, tools_condition

# --- Agent Flow ---

tools = [log_interaction, edit_interaction, get_hcp_info, generate_followup, search_materials]
llm_with_tools = llm.bind_tools(tools)

def call_model(state: AgentState):
    messages = state['messages']
    hcp_id = state['hcp_id']
    interaction_id = state.get('interaction_id', 0)
    
    system_msg = (
        "You are an AI-First CRM Assistant. "
        f"Context: HCP ID={hcp_id}, Interaction ID={interaction_id}. Time: {datetime.now().strftime('%H:%M %Y-%m-%d')}. "
        "PRIORITY: When a user describes a conversation or meeting, ALWAYS use 'log_interaction' FIRST. "
        "1. To log new details, use 'log_interaction'. It will auto-generate an 'outcome' if you don't provide one. "
        "2. To update specific fields of the current interaction, use 'edit_interaction' with the context Interaction ID. "
        "3. Supported fields for edit: date, time, attendees, topics_discussed, sentiment, outcomes, next_steps. "
        "4. DO NOT include raw JSON in your natural language text. Keep your text response clean and conversational."
    )

    
    full_messages = [HumanMessage(content=system_msg)] + messages
    response = llm_with_tools.invoke(full_messages)
    return {"messages": [response]}

workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("agent", call_model)
workflow.add_node("tools", ToolNode(tools))

# Set entry point
workflow.set_entry_point("agent")

# Add conditional edges
workflow.add_conditional_edges(
    "agent",
    tools_condition,
)

# Add edge from tools back to agent
workflow.add_edge("tools", "agent")

agent = workflow.compile()
