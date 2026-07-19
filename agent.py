import os
from dotenv import load_dotenv

load_dotenv()

from google.adk import Agent

from tools import (
    run_build_command,
    read_file_content,
    write_file_content,
    replace_in_file,
    find_files,
    grep_codebase
)

SYSTEM_PROMPT = """You are the Autonomous Codebase Healer, an AI developer assistant specialized in Next.js, TypeScript, and Node.js applications.

YOUR GOAL:
Given a build failure (or error logs), investigate the codebase, identify the broken file(s), apply surgical fixes using `replace_in_file`, and verify that `npm run build` (or the configured build command) passes.

OPERATION WORKFLOW:
1. Analyze the build error log provided or run `run_build_command` to get fresh error logs.
2. Extract error location (filenames, line numbers, missing imports, syntax errors, type errors).
3. Use `find_files`, `grep_codebase`, or `read_file_content` to locate and examine the problematic code.
4. Use `replace_in_file` to surgically fix the exact code error (or `write_file_content` for large rewrites).
5. ALWAYS execute `run_build_command` after editing code to verify if the build succeeds.
6. If the build fails again, repeat the cycle until the build PASSED.
7. Once the build succeeds, summarize the exact root cause and the fix applied.
"""

# Official Google ADK Agent Instance
root_agent = Agent(
    name="healer_agent",
    model=os.environ.get("HEALER_MODEL", "gemini-2.5-flash"),
    description="Self-healing terminal and web agent for Next.js & Node.js development.",
    instruction=SYSTEM_PROMPT,
    tools=[
        run_build_command,
        read_file_content,
        replace_in_file,
        write_file_content,
        find_files,
        grep_codebase
    ]
)
