import asyncio
import sys
import os
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from graph import create_workflow
from evals import evaluate_sar

load_dotenv()
console = Console()

async def main():
    console.print(Panel.fit(
        "[bold cyan]🛡️ FORENSIC LEDGER: AUTONOMOUS AML INVESTIGATOR[/bold cyan]\n"
        "[dim]LangGraph • Model Context Protocol • FastMCP • LLM-as-a-Judge[/dim]",
        border_style="cyan"
    ))

    console.print("[yellow]1. Connecting to Secure Banking MCP Server...[/yellow]")
    client = MultiServerMCPClient({
        "banking_server": {
            "transport": "stdio",
            "command": sys.executable, 
            "args": ["mcp_server.py"]
        }
    })

    tools = await client.get_tools()
    mcp_tools = {tool.name: tool for tool in tools}
    console.print(f"[green]✔ Secure Tools Loaded:[/green] {list(mcp_tools.keys())}\n")

    console.print("[yellow]2. Compiling Multi-Agent LangGraph Workflow...[/yellow]")
    app = await create_workflow(mcp_tools)

    target_company = input("Enter company to investigate (e.g., Global Traders LLC): ").strip()
    if not target_company:
        target_company = "Global Traders LLC"
    state = {
        "target": target_company,
        "investigation_log": f"INITIATING AML INVESTIGATION ON: {target_company}\n",
        "next_action": "",
        "action_arg": "",
        "review_status": "",
        "feedback": "None yet. Start by getting transactions for the target.",
        "sar_report": "",
        "iterations": 0
    }

    console.print(f"[bold white on blue] 🕵️ TARGET UNDER SURVEILLANCE: {target_company} [/bold white on blue]\n")
    console.print("[bold yellow]--- LIVE AGENTIC INVESTIGATION STREAM ---[/bold yellow]")

    # Run the streaming workflow
    async for event in app.astream(state):
        for node_name, node_state in event.items():
            if node_name == "investigator_node":
                action = node_state.get('next_action')
                arg = node_state.get('action_arg')
                console.print(f"  [cyan]▸ INVESTIGATOR:[/cyan] Decided to call [bold]{action}[/bold] with argument [italic]'{arg}'[/italic]")
            elif node_name == "reviewer_node":
                status = node_state.get('review_status')
                color = "green" if status == "APPROVED" else "red"
                console.print(f"  [{color}]▸ COMPLIANCE REVIEW: {status}[/{color}] | Feedback: {node_state.get('feedback')}")
            elif node_name == "sar_writer_node":
                console.print("  [magenta]▸ SAR WRITER:[/magenta] Synthesizing final formal regulatory documentation...")

    console.print("[bold yellow]--- INVESTIGATION COMPLETE ---[/bold yellow]\n")

    # Retrieving final execution output
    final_state = await app.ainvoke(state)
    report_text = final_state["sar_report"]

    # Defensive fallback in case it's still wrapped in a list
    if isinstance(report_text, list):
        report_text = "".join(item.get("text", "") if isinstance(item, dict) else str(item) for item in report_text)

    # 1. Pretty-print to terminal as rendered Markdown
    console.print(Panel(
        Markdown(report_text),
        title="[bold red]CONFIDENTIAL // SUSPICIOUS ACTIVITY REPORT (SAR)[/bold red]",
        subtitle="[dim]Generated via LangGraph State Machine[/dim]",
        border_style="red",
        padding=(1, 2)
    ))

    # 2. Saving directly to a markdown file for easy previewing
    output_filename = "SAR_Report.md"
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(report_text)
    console.print(f"\n[bold green]✔ Report saved to disk:[/bold green] [underline]{output_filename}[/underline]")
    console.print("[dim](Tip: In VS Code, open SAR_Report.md and press 'Ctrl + Shift + V' to view it formatted.)[/dim]\n")

    # 3. Run LLM Evaluation
    console.print("[yellow]3. Running LLM-as-a-Judge Evaluation...[/yellow]")
    eval_result = await evaluate_sar(
        investigation_log=final_state["investigation_log"],
        sar_report=report_text
    )

    # Presenting Evaluation metrics in structured table
    eval_table = Table(title="Compliance & Truthfulness Audit (LLM-as-a-Judge)", border_style="blue")
    eval_table.add_column("Metric", style="bold white")
    eval_table.add_column("Result", style="cyan")

    score_color = "green" if eval_result.score >= 4 else "red"
    hallucination_color = "red" if eval_result.hallucination_detected else "green"

    eval_table.add_row("Compliance Score", f"[{score_color}]{eval_result.score} / 5[/{score_color}]")
    eval_table.add_row("Hallucination Detected", f"[{hallucination_color}]{eval_result.hallucination_detected}[/{hallucination_color}]")
    eval_table.add_row("Auditor Reasoning", eval_result.reasoning)

    console.print(eval_table)
    console.print()

if __name__ == "__main__":
    asyncio.run(main())