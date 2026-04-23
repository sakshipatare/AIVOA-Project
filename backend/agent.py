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
llm = ChatGroq(model="llama-3.3-70b-versatile", groq_api_key=os.getenv("GROQ_API_KEY"))

# State definition
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], lambda x, y: x + y]
    hcp_id: int
    interaction_id: int

# --- Tools ---

@tool
def log_interaction_tool(hcp_id: int, type: str, raw_text: str):
    """
    Groups and summarizes the interaction details from raw input and saves it to the database.
    Input: hcp_id, type (Meeting/Call/Email), raw_text (the content of the interaction).
    """
    db = SessionLocal()
    try:
        # Ensure hcp_id is an integer
        hcp_id = int(hcp_id)
        
        # Check if HCP exists
        hcp = db.query(HCP).filter(HCP.id == hcp_id).first()
        if not hcp:
            return f"Error: HCP with ID {hcp_id} not found. Please ask the user to select an HCP first."
            
        # Use LLM to extract entities and summarize
        extraction_prompt = f"Extract structured data from this CRM interaction log:\n\n{raw_text}\n\n" \
                            "Return JSON with: summary, sentiment (Positive/Neutral/Negative), outcomes, next_steps, materials_shared."
        response = llm.invoke([HumanMessage(content=extraction_prompt)])
        # In a real app, I'd parse the JSON. For this demo, we'll simulate the extraction.
        # Let's assume the LLM returns a well-formatted response.
        
        # Mocking extraction for simplicity in this implementation
        summary = response.content[:200] # Use part of response as summary
        
        new_interaction = Interaction(
            hcp_id=hcp_id,
            type=type,
            summary=summary,
            sentiment="Neutral", # Default
            raw_transcript=raw_text,
            date=datetime.utcnow()
        )
        db.add(new_interaction)
        db.commit()
        db.refresh(new_interaction)
        return f"Interaction logged successfully with ID {new_interaction.id}"
    finally:
        db.close()

@tool
def edit_interaction_tool(interaction_id: int, field: str, value: str):
    """
    Modifies an existing interaction log.
    Input: interaction_id, field (e.g., summary, sentiment, outcomes), value.
    """
    db = SessionLocal()
    try:
        interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
        if interaction:
            setattr(interaction, field, value)
            db.commit()
            return f"Updated {field} for interaction {interaction_id}"
        return "Interaction not found"
    finally:
        db.close()

@tool
def get_hcp_info_tool(hcp_name: str):
    """
    Retrieves profile and history for a specific HCP.
    """
    db = SessionLocal()
    try:
        hcp = db.query(HCP).filter(HCP.name.ilike(f"%{hcp_name}%")).first()
        if hcp:
            history = db.query(Interaction).filter(Interaction.hcp_id == hcp.id).all()
            return {
                "id": hcp.id,
                "name": hcp.name,
                "specialty": hcp.specialty,
                "history_count": len(history)
            }
        return "HCP not found"
    finally:
        db.close()

@tool
def generate_followup_tool(interaction_id: int):
    """
    Generates a personalized follow-up email/task based on the interaction.
    """
    db = SessionLocal()
    try:
        interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
        if not interaction:
            return "Interaction not found"
        
        prompt = f"Based on this interaction: '{interaction.summary}', generate a professional follow-up email for the HCP."
        response = llm.invoke([HumanMessage(content=prompt)])
        return response.content
    finally:
        db.close()

@tool
def search_materials_tool(query: str):
    """
    Searches for relevant product brochures or scientific papers.
    """
    # Simulated search
    materials = [
        "OncoBoost Phase III Clinical Trial Summary.pdf",
        "Efficacy of Product X in Post-Op Recovery.docx",
        "HCP Presentation - Q4 2025.pptx"
    ]
    return [m for m in materials if query.lower() in m.lower()]

from langgraph.prebuilt import ToolNode, tools_condition

# --- Agent Flow ---

tools = [log_interaction_tool, edit_interaction_tool, get_hcp_info_tool, generate_followup_tool, search_materials_tool]
llm_with_tools = llm.bind_tools(tools)

def call_model(state: AgentState):
    messages = state['messages']
    hcp_id = state['hcp_id']
    
    system_msg = f"You are an AI-First CRM Assistant for life sciences field reps. " \
                 f"The current HCP ID in context is the INTEGER: {hcp_id}. " \
                 "When logging interactions, ALWAYS use this as an INTEGER. If you need info on an HCP, use the get_hcp_info tool."
    
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
