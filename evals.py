from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

class EvalResult(BaseModel):
    score: int = Field(description="Score from 1 to 5 (5 is factually perfect compliance)")
    hallucination_detected: bool = Field(description="True if ANY names, amounts, or facts outside the raw log were introduced")
    reasoning: str = Field(description="Detailed explanation of the score")

async def evaluate_sar(investigation_log: str, sar_report: str) -> EvalResult:
    # Use a stronger model for evaluating truthfulness
    llm = ChatGoogleGenerativeAI(model="gemini-3-flash-preview", temperature=0)
    
    prompt = ChatPromptTemplate.from_template(
        "You are an elite QA Compliance Auditor.\n\n"
        "Ground Truth Evidence Log (The ONLY facts allowed):\n{log}\n\n"
        "Generated SAR Report to evaluate:\n{report}\n\n"
        "Assess if the SAR accurately captured the money laundering flow, AND check if it hallucinated "
        "any data, transaction amounts, or entity names not present in the Ground Truth log."
    )
    
    chain = prompt | llm.with_structured_output(EvalResult)
    return await chain.ainvoke({
        "log": investigation_log,
        "report": sar_report
    })