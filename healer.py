import os
import sys
import argparse
import difflib
from dotenv import load_dotenv

# Ensure UTF-8 output encoding for Windows terminals
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Load environment variables
load_dotenv()

from google import genai
from google.genai import types

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from tools import (
    run_build_command,
    read_file_content,
    write_file_content,
    replace_in_file,
    find_files,
    grep_codebase
)

console = Console()

SYSTEM_PROMPT = """You are the Autonomous Codebase Healer, an AI developer assistant specialized in Next.js, TypeScript, and Node.js applications.

YOUR GOAL:
Given a build failure (or error logs), investigate the codebase, identify the broken file(s), apply surgical fixes, and verify that `npm run build` (or the configured build command) passes.

AVAILABLE TOOLS:
1. `run_build_command`: Runs `npm run build` or custom build command in the target project.
2. `find_files`: Searches for files by pattern or extension (e.g. '*.tsx', '*.ts', 'package.json').
3. `grep_codebase`: Searches for symbols, variables, or error text across files.
4. `read_file_content`: Reads line-numbered file content.
5. `replace_in_file`: Surgically replaces an exact target substring with a replacement string in a file (PREFERRED for bug fixes!).
6. `write_file_content`: Overwrites complete file content.

OPERATION WORKFLOW:
1. Analyze the build error log provided or run `run_build_command` to get fresh error logs.
2. Extract error location (filenames, line numbers, missing imports, syntax errors, type errors).
3. Use `find_files`, `grep_codebase`, or `read_file_content` to locate and examine the problematic code.
4. Use `replace_in_file` to surgically fix the exact code error (or `write_file_content` for large rewrites).
5. ALWAYS execute `run_build_command` after editing code to verify if the build succeeds.
6. If the build fails again, repeat the cycle until the build PASSED.
7. Once the build succeeds, summarize the exact root cause and the fix applied.

BE SURGICAL AND ACCURATE:
- Do not remove existing features unless they are corrupt.
- Fix imports, missing modules, type annotations, syntax errors, and missing exports.
- Always verify with `run_build_command` before concluding!
"""

def print_banner():
    banner_text = Text()
    banner_text.append("⚡ AUTONOMOUS CODEBASE HEALER ⚡\n", style="bold cyan")
    banner_text.append("Track: Developer Tools | Powered by Google GenAI & Gemini\n", style="bold yellow")
    banner_text.append("Self-Healing Terminal Utility for Next.js & Node.js", style="italic gray")
    console.print(Panel(banner_text, border_style="cyan", expand=False))

def resolve_target_path(fpath: str, target_dir: str) -> str:
    """Helper to resolve file path robustly regardless of whether agent used relative or absolute path."""
    if not fpath:
        return fpath
    if os.path.isabs(fpath):
        return fpath
        
    abs_target = os.path.abspath(target_dir)
    norm_fpath = os.path.normpath(fpath)
    
    target_basename = os.path.basename(abs_target)
    parts = norm_fpath.split(os.sep)
    if parts and parts[0] == target_basename:
        norm_fpath = os.sep.join(parts[1:])
        
    return os.path.abspath(os.path.join(abs_target, norm_fpath))

def execute_tool(name: str, args: dict, target_dir: str, default_cmd: str):
    """Executes local python tools requested by Gemini and formats responses."""
    if name == "run_build_command":
        wdir = args.get("working_directory", target_dir)
        cmd = args.get("build_command", default_cmd)
        console.print(f"[bold yellow]⚙️ Running terminal command:[/bold yellow] [bold white]{cmd}[/bold white] in [cyan]{wdir}[/cyan]")
        output = run_build_command(working_directory=wdir, build_command=cmd)
        if "PASSED" in output:
            console.print("[bold green]✔ Build Succeeded![/bold green]")
        else:
            console.print("[bold red]✖ Build Failed![/bold red]")
        return output

    elif name == "read_file_content":
        raw_path = args.get("file_path", "")
        fpath = resolve_target_path(raw_path, target_dir)
        start_line = int(args.get("start_line", 1))
        end_line = int(args.get("end_line", 500))
        console.print(f"[bold blue]📖 Reading File:[/bold blue] [cyan]{fpath}[/cyan] (Lines {start_line}-{end_line})")
        return read_file_content(file_path=fpath, start_line=start_line, end_line=end_line)

    elif name == "write_file_content":
        raw_path = args.get("file_path", "")
        fpath = resolve_target_path(raw_path, target_dir)
        content = args.get("content", "")
        
        # Read old content if exists for diff display
        old_content = ""
        if os.path.isfile(fpath):
            with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                old_content = f.read()

        console.print(Panel(f"[bold green]🛠️ Patching File:[/bold green] [yellow]{fpath}[/yellow]", border_style="green"))
        
        # Display diff snippet if old content existed
        if old_content:
            diff = list(difflib.unified_diff(
                old_content.splitlines(),
                content.splitlines(),
                fromfile="a/" + os.path.basename(fpath),
                tofile="b/" + os.path.basename(fpath),
                lineterm=""
            ))
            if diff:
                diff_text = "\n".join(diff[:30])
                console.print(Syntax(diff_text, "diff", theme="monokai", line_numbers=False))

        res = write_file_content(file_path=fpath, content=content)
        console.print(f"[bold green]✔ Saved patch to {fpath}[/bold green]")
        return res

    elif name == "replace_in_file":
        raw_path = args.get("file_path", "")
        fpath = resolve_target_path(raw_path, target_dir)
        target_str = args.get("target_string", "")
        replace_str = args.get("replacement_string", "")
        
        console.print(Panel(f"[bold green]🛠️ Surgically Patching File:[/bold green] [yellow]{fpath}[/yellow]\nReplacing: [red]{target_str}[/red] -> [green]{replace_str}[/green]", border_style="green"))
        res = replace_in_file(file_path=fpath, target_string=target_str, replacement_string=replace_str)
        console.print(f"[bold green]✔ {res}[/bold green]")
        return res

    elif name == "find_files":
        wdir = args.get("working_directory", target_dir)
        pat = args.get("pattern", "*")
        console.print(f"[bold magenta]🔍 Searching Directory:[/bold magenta] pattern='[yellow]{pat}[/yellow]' in [cyan]{wdir}[/cyan]")
        return find_files(working_directory=wdir, pattern=pat)

    elif name == "grep_codebase":
        wdir = args.get("working_directory", target_dir)
        query = args.get("query", "")
        console.print(f"[bold magenta]🔎 Searching Codebase for:[/bold magenta] '[yellow]{query}[/yellow]'")
        return grep_codebase(working_directory=wdir, query=query)

    else:
        return f"Error: Tool '{name}' not found."

def run_healer(target_dir: str, build_cmd: str, auto_detect: bool, pasted_error: str, model_name: str):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        console.print("[bold red]Error: GEMINI_API_KEY environment variable is not set.[/bold red]")
        console.print("Please set your GEMINI_API_KEY in the environment or in a .env file.")
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    # Initial problem statement
    initial_user_msg = f"Project Directory: {os.path.abspath(target_dir)}\nBuild Command: {build_cmd}\n\n"
    
    if pasted_error:
        console.print("[bold yellow]Pasted Error Output Received.[/bold yellow]")
        initial_user_msg += f"Pasted Error Output:\n{pasted_error}"
    elif auto_detect:
        console.print(f"[bold yellow]Running initial build check in {target_dir}...[/bold yellow]")
        initial_build = run_build_command(working_directory=target_dir, build_command=build_cmd)
        if "PASSED" in initial_build:
            console.print("[bold green]✨ The build is ALREADY passing! No healing needed.[/bold green]")
            return
        initial_user_msg += f"Initial Build Output:\n{initial_build}"
    else:
        console.print("[bold yellow]Starting build diagnosis...[/bold yellow]")
        initial_build = run_build_command(working_directory=target_dir, build_command=build_cmd)
        initial_user_msg += f"Initial Build Output:\n{initial_build}"

    # Declare functions for Gemini SDK
    tools_list = [
        run_build_command,
        read_file_content,
        replace_in_file,
        write_file_content,
        find_files,
        grep_codebase
    ]

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        tools=tools_list,
        temperature=0.2
    )

    contents = [
        types.Content(role="user", parts=[types.Part.from_text(text=initial_user_msg)])
    ]

    max_steps = 15
    step = 0

    console.print(f"\n[bold cyan]🚀 Initializing Autonomous Agent ({model_name})...[/bold cyan]\n")

    while step < max_steps:
        step += 1
        console.print(f"[dim]--- Agent Turn {step}/{max_steps} ---[/dim]")

        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True
            ) as progress:
                progress.add_task(description=f"Gemini thinking (Turn {step})...", total=None)
                
                # Retry loop for rate limits (429)
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        response = client.models.generate_content(
                            model=model_name,
                            contents=contents,
                            config=config
                        )
                        break
                    except Exception as err:
                        if "429" in str(err) or "RESOURCE_EXHAUSTED" in str(err):
                            if attempt < max_retries - 1:
                                wait_sec = 15 * (attempt + 1)
                                console.print(f"[yellow]⚠️ Rate limit reached. Waiting {wait_sec}s before retry (Attempt {attempt+1}/{max_retries})...[/yellow]")
                                import time
                                time.sleep(wait_sec)
                            else:
                                raise err
                        else:
                            raise err
        except Exception as e:
            console.print(f"[bold red]API Error:[/bold red] {e}")
            break

        # Append model response to conversation history
        model_parts = []
        if response.text:
            console.print(Panel(response.text, title="🤖 Agent Thinking & Strategy", border_style="cyan"))
            model_parts.append(types.Part.from_text(text=response.text))

        if response.function_calls:
            for call in response.function_calls:
                model_parts.append(
                    types.Part.from_function_call(
                        name=call.name,
                        args=call.args
                    )
                )

        contents.append(types.Content(role="model", parts=model_parts))

        # Check if function calls were requested
        if response.function_calls:
            tool_response_parts = []
            for call in response.function_calls:
                fn_name = call.name
                fn_args = dict(call.args) if call.args else {}
                
                # Execute function locally
                tool_output = execute_tool(fn_name, fn_args, target_dir, build_cmd)
                
                tool_response_parts.append(
                    types.Part.from_function_response(
                        name=fn_name,
                        response={"result": tool_output}
                    )
                )
            
            # Send tool responses back to Gemini
            contents.append(types.Content(role="user", parts=tool_response_parts))
        else:
            # No function calls means agent finished its turn/summary
            console.print("\n[bold green]════════════════════════════════════════════════════════════════[/bold green]")
            console.print("[bold green]🎉 HEALER WORKFLOW COMPLETE![/bold green]")
            console.print("[bold green]════════════════════════════════════════════════════════════════[/bold green]\n")
            break

def main():
    print_banner()

    parser = argparse.ArgumentParser(description="Autonomous Codebase Healer for Next.js & Node.js")
    parser.add_argument("--path", default=".", help="Path to target project directory (default: .)")
    parser.add_argument("--cmd", default="npm run build", help="Build command to execute & verify (default: 'npm run build')")
    parser.add_argument("--auto", action="store_true", help="Auto-detect build errors by running build command immediately")
    parser.add_argument("--paste", help="Paste error message/stack trace directly")
    parser.add_argument("--model", default=os.environ.get("HEALER_MODEL", "gemini-2.5-flash"), help="Gemini Model ID")

    args = parser.parse_args()

    # Interactive prompt if no flags specified
    target_path = args.path
    build_cmd = args.cmd
    pasted_err = args.paste
    auto_detect = args.auto

    if not auto_detect and not pasted_err and len(sys.argv) == 1:
        console.print("[yellow]No execution flags specified. Defaulting to auto-detection in current folder...[/yellow]")
        auto_detect = True

    run_healer(
        target_dir=target_path,
        build_cmd=build_cmd,
        auto_detect=auto_detect,
        pasted_error=pasted_err,
        model_name=args.model
    )

if __name__ == "__main__":
    main()
