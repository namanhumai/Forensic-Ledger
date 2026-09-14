from fastmcp import FastMCP
import sqlite3

# Initialize MCP Server
mcp = FastMCP("ForensicLedgerServer")
DB_PATH = "aml_database.db"

@mcp.tool()
def get_transactions(entity_name: str) -> str:
    """Get all financial transactions (sent and received) for a given company or person."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT sender, receiver, amount, date FROM transactions WHERE sender = ? OR receiver = ?", (entity_name, entity_name))
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return f"No transactions found for {entity_name}."
    
    result = f"Transactions for {entity_name}:\n"
    for r in rows:
        result += f"- {r[0]} sent ${r[2]} to {r[1]} on {r[3]}\n"
    return result

@mcp.tool()
def get_corporate_registry(company_name: str) -> str:
    """Find the Ultimate Beneficial Owner (UBO) and registration country of a company."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT ultimate_beneficial_owner, registration_country FROM corporate_registry WHERE company_name = ?", (company_name,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return f"No registry data found for {company_name}."
    return f"Company: {company_name} | Ultimate Beneficial Owner: {row[0]} | Registered in: {row[1]}"

@mcp.tool()
def check_sanctions(person_name: str) -> str:
    """Check if a person is on an international sanctions or terrorist watchlist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT reason FROM sanctions WHERE person_name = ?", (person_name,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return f"CLEAR: {person_name} is not on any sanctions list."
    return f"FLAGGED! {person_name} is sanctioned for: {row[0]}"

if __name__ == "__main__":
    # Running server using standard input/output 
    mcp.run(transport="stdio")