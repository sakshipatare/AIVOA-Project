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
def log_interaction_tool(hcp_id: Union[int, str], interaction_type: str, raw_text: str):
    """
    Groups and summarizes the interaction details from raw input and saves it to the database.
    Input: hcp_id, interaction_type (Meeting/Call/Email), raw_text (the content of the interaction).
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
def edit_interaction_tool(interaction_id: Union[int, str], field: str, value: str):
    """
    Modifies an existing interaction log.
    Input: interaction_id, field (e.g., summary, sentiment, outcomes), value.
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
def generate_followup_tool(interaction_id: Union[int, str]):
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
    
    system_msg = (
        "You are an AI-First CRM Assistant for life sciences field reps. "
        f"The current HCP ID in context is the INTEGER: {hcp_id}. "
        f"The current date and time is: {datetime.now().strftime('%Y-%m-%d %H:%M')}. "
        "When logging an interaction, you MUST pass the hcp_id as a literal integer. "
        "When a user describes an interaction, use the log_interaction_tool EXACTLY ONCE. "
        "If you see the tool output in the history, DO NOT call it again for the same description. "
        "Instead, provide a natural language confirmation to the user. "
        "Ensure the final response (the confirmation) contains the UI_UPDATE_DATA: {json} marker from the tool output."
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
