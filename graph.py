from typing import TypedDict
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field

# 1. State Definition 
class GraphState(TypedDict):
    target: str
    investigation_log: str
    next_action: str
    action_arg: str
    review_status: str
    feedback: str
    sar_report: str
    iterations: int

# 2. Pydantic Models 
class InvestigatorAction(BaseModel):
    tool_name: str = Field(description="One of: 'get_transactions', 'get_corporate_registry', 'check_sanctions', or 'submit_for_review'")
    argument: str = Field(description="The entity or person name to query. If submitting, summarize findings.")

class ReviewDecision(BaseModel):
    status: str = Field(description="'APPROVED' if evidence is complete, 'REJECTED' if missing links.")
    feedback: str = Field(description="Explanation of what the investigator needs to look up next.")

# 3. Graph Builder Function
async def create_workflow(mcp_tools: dict):
    llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite", temperature=0)

    # NODE: Investigator ---
    async def investigator_node(state: GraphState):
        prompt = ChatPromptTemplate.from_template(
            "You are an elite Financial Crimes Investigator.\n"
            "Target: {target}\n"
            "Current Evidence Log:\n{log}\n"
            "Reviewer Feedback: {feedback}\n\n"
            "Decide the next logical step. You must trace the money, find the Ultimate Beneficial Owner (UBO), "
            "and check if the UBO is sanctioned. If you have all this proof, choose 'submit_for_review'."
        )
        chain = prompt | llm.with_structured_output(InvestigatorAction)
        decision = await chain.ainvoke({
            "target": state["target"],
            "log": state["investigation_log"],
            "feedback": state["feedback"]
        })
        return {
            "next_action": decision.tool_name, 
            "action_arg": decision.argument,
            "iterations": state["iterations"] + 1
        }

    # NODE: Tool Executor (MCP Tools) ---
    async def tool_executor_node(state: GraphState):
        tool_name = state["next_action"]
        query = state["action_arg"]
        log_entry = f"\n[Action] Ran {tool_name} on '{query}'\n"
        
        try:
            if tool_name == "get_transactions":
                result = await mcp_tools["get_transactions"].ainvoke({"entity_name": query})
            elif tool_name == "get_corporate_registry":
                result = await mcp_tools["get_corporate_registry"].ainvoke({"company_name": query})
            elif tool_name == "check_sanctions":
                result = await mcp_tools["check_sanctions"].ainvoke({"person_name": query})
            else:
                result = "Unknown tool requested."
            
            log_entry += f"[Result] {result}\n"
        except Exception as e:
            log_entry += f"[Error] {str(e)}\n"
            
        return {"investigation_log": state["investigation_log"] + log_entry}

    # NODE: Reviewer ---
    async def reviewer_node(state: GraphState):
        prompt = ChatPromptTemplate.from_template(
            "You are an AML Compliance Officer reviewing an investigation.\n"
            "Evidence Log:\n{log}\n\n"
            "Criteria for Approval:\n"
            "1. Did we identify suspicious transaction flows?\n"
            "2. Did we identify the Ultimate Beneficial Owner (UBO) of the receiving shell company?\n"
            "3. Did we check the UBO against the sanctions list?\n"
            "If ALL three are met, output APPROVED. If any are missing, output REJECTED and tell the investigator what to do."
        )
        chain = prompt | llm.with_structured_output(ReviewDecision)
        review = await chain.ainvoke({"log": state["investigation_log"]})
        return {"review_status": review.status, "feedback": review.feedback}

    # NODE: SAR Writer (With Robust Text Unwrapping) ---  , SAR:Suspecious activity report
    async def sar_writer_node(state: GraphState):
        prompt = ChatPromptTemplate.from_template(
            "Write a highly professional Suspicious Activity Report (SAR) in Markdown based strictly on this evidence log:\n{log}"
        )
        chain = prompt | llm
        response = await chain.ainvoke({"log": state["investigation_log"]})
        
        # Unwrap structured responses if returned as a list of dicts
        raw_content = response.content
        if isinstance(raw_content, list):
            clean_text = "".join(
                item.get("text", "") if isinstance(item, dict) else str(item)
                for item in raw_content
            )
        else:
            clean_text = str(raw_content)
            
        return {"sar_report": clean_text.strip()}

    # ROUTING LOGIC ---
    def route_investigator(state: GraphState):
        if state["next_action"] == "submit_for_review":
            return "reviewer_node"
        if state["iterations"] >= 8:
            return "reviewer_node" 
        return "tool_executor_node"

    def route_reviewer(state: GraphState):
        if state["review_status"] == "APPROVED":
            return "sar_writer_node"
        return "investigator_node"

    # Compiling the Graph
    workflow = StateGraph(GraphState)
    workflow.add_node("investigator_node", investigator_node)
    workflow.add_node("tool_executor_node", tool_executor_node)
    workflow.add_node("reviewer_node", reviewer_node)
    workflow.add_node("sar_writer_node", sar_writer_node)

    workflow.set_entry_point("investigator_node")
    workflow.add_conditional_edges("investigator_node", route_investigator)
    workflow.add_edge("tool_executor_node", "investigator_node")
    workflow.add_conditional_edges("reviewer_node", route_reviewer)
    workflow.add_edge("sar_writer_node", END)

    return workflow.compile()