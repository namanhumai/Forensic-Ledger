# Forensic-Ledger
An AI financial crimes investigator that traces money laundering patterns, shell company networks, and suspicious transaction velocities across mock banking ledgers
---

### 2. Forensic Ledger (AML Investigator)

**GitHub "About" (Description):**
> An autonomous multi-agent system that investigates financial crimes and money laundering (AML). Uses LangGraph cyclic routing to query a secure MCP banking server and synthesize Suspicious Activity Reports (SARs).

**`README.md`**

```markdown
# 🛡️ ForensicLedger

Manual AML (Anti-Money Laundering) compliance is incredibly slow. Investigators spend hours tracing transactions across shell companies just to find out if someone is sanctioned. 

I built ForensicLedger to automate this. It doesn't just generate text; it acts as a forensic investigator. You give it a target company, and it uses a strict Model Context Protocol (MCP) server to query simulated bank ledgers, trace Ultimate Beneficial Owners (UBOs), and check global sanction lists. 

If it misses a step, a "Compliance Reviewer" agent catches the error, rejects the draft, and forces the investigator agent to go back and dig deeper (cyclic routing).

## ⚙️ The Flow

1. **Investigator Node:** Analyzes the current evidence log and decides which MCP API to call next (`get_transactions`, `get_corporate_registry`, `check_sanctions`).
2. **MCP Sandbox:** A secure FastMCP 2.0 server running a mock SQLite database. The LLM cannot write arbitrary SQL; it can only use the predefined tools.
3. **Reviewer Node (The Critic):** Checks the final evidence. Did we find the UBO? Are they sanctioned? If no, it routes the graph backward.
4. **SAR Generator:** Once approved, compiles the evidence into a Markdown-formatted Suspicious Activity Report.
5. **QA Auditor:** A final LLM-as-a-judge runs over the SAR to ensure zero hallucination (it compares the report strictly against the raw database logs).

## 🛠️ Built With
* **Python**
* **LangGraph** (For stateful, cyclic agent workflows)
* **FastMCP / langchain-mcp-adapters** (To securely expose the SQLite database)
* **SQLite3** (Mock banking ledger)
* **Rich** (For the beautiful terminal UI)
