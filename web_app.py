import os
import sys
import asyncio
import json
import difflib
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel

from google import genai
from google.genai import types

from tools import (
    run_build_command,
    read_file_content,
    write_file_content,
    replace_in_file,
    find_files,
    grep_codebase
)

# Initialize FastAPI App
app = FastAPI(title="Autonomous Codebase Healer - ADK Web Dashboard")

# Global Agent State
agent_state = {
    "status": "IDLE",  # IDLE, RUNNING_BUILD, THINKING, INSPECTING, PATCHING, VERIFYING, PASSED, FAILED
    "target_dir": "./demo-app",
    "build_cmd": "npm run build",
    "logs": [],
    "timeline": [],
    "last_diff": None,
    "last_patch": None,
    "current_step": 0,
    "total_steps": 15,
    "build_passed": False
}

# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        # Send current state on connection
        await websocket.send_json({"type": "STATE_UPDATE", "data": agent_state})

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

manager = ConnectionManager()

def broadcast_log(log_type: str, message: str, meta: Optional[dict] = None):
    log_entry = {
        "type": log_type,
        "message": message,
        "meta": meta or {}
    }
    agent_state["logs"].append(log_entry)
    asyncio.create_task(manager.broadcast({"type": "LOG_ENTRY", "data": log_entry}))
    asyncio.create_task(manager.broadcast({"type": "STATE_UPDATE", "data": agent_state}))

def update_agent_status(status: str, step_info: Optional[str] = None):
    agent_state["status"] = status
    if step_info:
        agent_state["timeline"].append({"status": status, "info": step_info})
    asyncio.create_task(manager.broadcast({"type": "STATE_UPDATE", "data": agent_state}))

def resolve_target_path(fpath: str, target_dir: str) -> str:
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

def web_execute_tool(name: str, args: dict, target_dir: str, default_cmd: str) -> str:
    if name == "run_build_command":
        wdir = args.get("working_directory", target_dir)
        cmd = args.get("build_command", default_cmd)
        broadcast_log("BUILD_START", f"⚙️ Running terminal build: '{cmd}' in '{wdir}'")
        update_agent_status("RUNNING_BUILD", f"Executing: {cmd}")
        
        output = run_build_command(working_directory=wdir, build_command=cmd)
        
        if "PASSED" in output:
            broadcast_log("BUILD_SUCCESS", f"✔ Build PASSED successfully!", {"output": output})
            agent_state["build_passed"] = True
        else:
            broadcast_log("BUILD_FAIL", f"✖ Build FAILED", {"output": output})
        return output

    elif name == "read_file_content":
        raw_path = args.get("file_path", "")
        fpath = resolve_target_path(raw_path, target_dir)
        start_line = int(args.get("start_line", 1))
        end_line = int(args.get("end_line", 500))
        broadcast_log("READ_FILE", f"📖 Reading file: '{os.path.basename(fpath)}' (Lines {start_line}-{end_line})")
        update_agent_status("INSPECTING", f"Reading: {os.path.basename(fpath)}")
        return read_file_content(file_path=fpath, start_line=start_line, end_line=end_line)

    elif name == "replace_in_file":
        raw_path = args.get("file_path", "")
        fpath = resolve_target_path(raw_path, target_dir)
        target_str = args.get("target_string", "")
        replace_str = args.get("replacement_string", "")
        
        broadcast_log("PATCH_START", f"🛠️ Surgically patching '{os.path.basename(fpath)}'", {
            "file": fpath,
            "target": target_str,
            "replacement": replace_str
        })
        update_agent_status("PATCHING", f"Patching: {os.path.basename(fpath)}")
        
        res = replace_in_file(file_path=fpath, target_string=target_str, replacement_string=replace_str)
        
        agent_state["last_diff"] = {
            "file": os.path.basename(fpath),
            "target": target_str,
            "replacement": replace_str
        }
        broadcast_log("PATCH_SUCCESS", f"✔ {res}")
        return res

    elif name == "write_file_content":
        raw_path = args.get("file_path", "")
        fpath = resolve_target_path(raw_path, target_dir)
        content = args.get("content", "")
        broadcast_log("WRITE_FILE", f"📝 Rewriting content of file '{os.path.basename(fpath)}'")
        update_agent_status("PATCHING", f"Overwriting: {os.path.basename(fpath)}")
        res = write_file_content(file_path=fpath, content=content)
        agent_state["last_diff"] = {
            "file": os.path.basename(fpath),
            "target": "Original broken file content",
            "replacement": f"Patched file content ({len(content)} bytes)"
        }
        return res

    elif name == "find_files":
        wdir = args.get("working_directory", target_dir)
        pat = args.get("pattern", "*")
        broadcast_log("FIND_FILES", f"🔍 Searching files: pattern='{pat}'")
        return find_files(working_directory=wdir, pattern=pat)

    elif name == "grep_codebase":
        wdir = args.get("working_directory", target_dir)
        query = args.get("query", "")
        broadcast_log("GREP", f"🔎 Searching codebase for: '{query}'")
        return grep_codebase(working_directory=wdir, query=query)

    return f"Error: Tool '{name}' not found."

async def run_healer_task(target_dir: str, build_cmd: str, auto_detect: bool, pasted_error: str, model_name: str):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        broadcast_log("ERROR", "GEMINI_API_KEY environment variable is missing!")
        update_agent_status("FAILED", "Missing API Key")
        return

    # Reset agent state
    agent_state["status"] = "INITIALIZING"
    agent_state["target_dir"] = target_dir
    agent_state["build_cmd"] = build_cmd
    agent_state["logs"].clear()
    agent_state["timeline"].clear()
    agent_state["last_diff"] = None
    agent_state["build_passed"] = False
    agent_state["current_step"] = 0

    broadcast_log("SYSTEM", f"🚀 Initializing Healer Agent ({model_name})")
    broadcast_log("SYSTEM", f"Target: '{target_dir}' | Command: '{build_cmd}'")

    initial_user_msg = f"Project Directory: {os.path.abspath(target_dir)}\nBuild Command: {build_cmd}\n\n"

    if pasted_error:
        broadcast_log("USER_INPUT", "Using pasted build error log")
        initial_user_msg += f"Pasted Error Output:\n{pasted_error}"
    else:
        broadcast_log("BUILD_CHECK", "Running initial build check...")
        initial_build = web_execute_tool("run_build_command", {"working_directory": target_dir, "build_command": build_cmd}, target_dir, build_cmd)
        if "PASSED" in initial_build:
            broadcast_log("SUCCESS", "✨ The build is ALREADY passing! No healing needed.")
            update_agent_status("PASSED", "Already Passing")
            return
        initial_user_msg += f"Initial Build Output:\n{initial_build}"

    client = genai.Client(api_key=api_key)
    
    SYSTEM_PROMPT = """You are the Autonomous Codebase Healer, an AI developer assistant specialized in Next.js, TypeScript, and Node.js applications.
YOUR GOAL: Investigate build failures, locate broken source files, apply surgical patches using `replace_in_file`, and verify with `run_build_command`.
ALWAYS run `run_build_command` after editing code to verify that the build succeeds before concluding!"""

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
    for step in range(1, max_steps + 1):
        agent_state["current_step"] = step
        broadcast_log("STEP_HEADER", f"--- Agent Turn {step}/{max_steps} ---")
        update_agent_status("THINKING", f"Turn {step}/{max_steps}")

        # Execute API call in thread pool to prevent blocking asyncio loop
        response = None
        for attempt in range(3):
            try:
                loop = asyncio.get_running_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: client.models.generate_content(
                        model=model_name,
                        contents=contents,
                        config=config
                    )
                )
                break
            except Exception as err:
                if "429" in str(err) or "RESOURCE_EXHAUSTED" in str(err):
                    if attempt < 2:
                        wait_sec = 15 * (attempt + 1)
                        broadcast_log("WARNING", f"⚠️ API Rate limit reached. Waiting {wait_sec}s before retry...")
                        await asyncio.sleep(wait_sec)
                    else:
                        broadcast_log("ERROR", f"API Error: {err}")
                        update_agent_status("FAILED", "Rate Limit Exceeded")
                        return
                else:
                    broadcast_log("ERROR", f"API Error: {err}")
                    update_agent_status("FAILED", f"Error: {err}")
                    return

        if not response:
            break

        model_parts = []
        if response.text:
            broadcast_log("AGENT_THINKING", response.text)
            model_parts.append(types.Part.from_text(text=response.text))

        if response.function_calls:
            for call in response.function_calls:
                model_parts.append(
                    types.Part.from_function_call(name=call.name, args=call.args)
                )

        contents.append(types.Content(role="model", parts=model_parts))

        if response.function_calls:
            tool_response_parts = []
            for call in response.function_calls:
                fn_name = call.name
                fn_args = dict(call.args) if call.args else {}
                
                tool_output = web_execute_tool(fn_name, fn_args, target_dir, build_cmd)
                
                tool_response_parts.append(
                    types.Part.from_function_response(name=fn_name, response={"result": tool_output})
                )
            contents.append(types.Content(role="user", parts=tool_response_parts))
        else:
            if agent_state["build_passed"]:
                broadcast_log("SYSTEM", "🎉 HEALER WORKFLOW COMPLETE! Build Verified & Passed!")
                update_agent_status("PASSED", "Build Verified & Passed 🎉")
            else:
                broadcast_log("SYSTEM", "Agent concluded turn.")
                update_agent_status("FINISHED", "Completed")
            break

class HealRequest(BaseModel):
    target_dir: str = "./demo-app"
    build_cmd: str = "npm run build"
    auto_detect: bool = True
    pasted_error: Optional[str] = None
    model_name: str = "gemini-3.1-flash-lite"

@app.post("/api/heal")
async def trigger_heal(req: HealRequest, background_tasks: BackgroundTasks):
    if agent_state["status"] not in ["IDLE", "PASSED", "FAILED", "FINISHED"]:
        raise HTTPException(status_code=400, detail="Agent is already running a healing task.")
    
    background_tasks.add_task(
        run_healer_task,
        target_dir=req.target_dir,
        build_cmd=req.build_cmd,
        auto_detect=req.auto_detect,
        pasted_error=req.pasted_error or "",
        model_name=req.model_name
    )
    return {"status": "STARTED", "message": "Autonomous Healer initiated."}

@app.get("/api/state")
async def get_state():
    return agent_state

@app.websocket("/ws/logs")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Mount Static Files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir, exist_ok=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/", response_class=FileResponse)
async def serve_index():
    return os.path.join(static_dir, "index.html")

if __name__ == "__main__":
    import uvicorn
    print("⚡ ADK Web Dashboard starting on http://127.0.0.1:8000")
    uvicorn.run("web_app:app", host="127.0.0.1", port=8000, reload=True)
