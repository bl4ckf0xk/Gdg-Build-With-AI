# ⚡ Autonomous Codebase Healer

> **Hackathon Track:** Developer Tools  
> **Built With:** Python 3.10+, Google GenAI SDK (`google-genai`), Google ADK (`google-adk`), Gemini 3.1 AI, FastAPI, WebSockets & Modern Cyberpunk UI

---

## 💡 What is the Autonomous Codebase Healer?

The **Autonomous Codebase Healer** is a self-healing terminal utility and real-time Web Dashboard designed for Next.js, TypeScript, and Node.js development.

When a software build fails during development or CI/CD, developers usually have to manually read stack traces, search through files, figure out broken imports/type mismatches, edit the code, and re-run `npm run build`. 

The **Autonomous Codebase Healer** completely automates this loop:
1. **Detects** build errors by physically executing terminal build commands (`npm run build` / `tsc`).
2. **Investigates** the codebase using native directory search, grep, and line-numbered file inspection tools.
3. **Patches** broken source files using surgical string replacement (`replace_in_file`) or complete file rewrites.
4. **Verifies** the fix by re-executing terminal build commands in real-time until a green pass is achieved.

---

## 🌟 The Hackathon Demo "Wow" Factor

Watching an AI physically open terminal sessions, inspect broken TypeScript/Next.js code on screen, apply diff patches live, and re-trigger build commands until green checkmarks appear is a top-tier hackathon demo for Developer Tools.

```
 ┌───────────────────────────────────────────────────────────┐
 │ ⚡ AUTONOMOUS CODEBASE HEALER ⚡                          │
 │ Track: Developer Tools | Powered by Google GenAI & Gemini │
 └───────────────────────────────────────────────────────────┘
  ⚙️ Running terminal command: npm run build in ./demo-app
  ✖ Build Failed! (Exit Code: 1)

  🤖 Agent Strategy: Analyzed TypeScript error in src/app.ts
  📖 Reading File: ./demo-app/src/app.ts
  🛠️ Surgically Patching File: ./demo-app/src/app.ts
     Replacing: multiplyNumbers("100", 2) -> multiplyNumbers(100, 2)
  ⚙️ Running terminal command: npm run build in ./demo-app
  ✔ Build Succeeded!

  🎉 HEALER WORKFLOW COMPLETE!
```

---

## 🌐 Google ADK Web Dashboard & UI

This project includes an **Ultra-Modern Cyberpunk Glassmorphism Web Dashboard** as well as compatibility with official `adk web`!

### Option 1: Custom ADK Web Dashboard (Recommended)
Launch the real-time streaming glassmorphism dashboard:

```bash
python web_app.py
```
👉 Open your browser to: **`http://127.0.0.1:8000`**

#### Web Dashboard Features:
- 📺 **Live Terminal Stream**: Real-time WebSocket terminal log stream showing agent turns & tool executions.
- ⚡ **One-Click Auto Heal**: Trigger auto-detection & healing directly from the web interface.
- 🛠️ **Live Code Patch Diff**: Visual diff display showing target deletion lines in rose red and patch additions in emerald green.
- ⏱️ **Agent Activity Timeline**: Real-time status badge and step progress tracking.
- 🧠 **Pro Engine Selection**: Switch live between `Gemini 2.5 Pro`, `Gemini 1.5 Pro`, `Gemini 2.5 Flash`, and `Gemini 1.5 Flash`.

---

### Option 2: Official Google ADK Web UI (`adk web`)
Run the official Google Agent Development Kit Web Server:

```bash
# Using python module syntax (works on all environments)
python -m google.adk.cli web . --port 8080
```
👉 Open your browser to: **`http://127.0.0.1:8080`**

---

## 🚀 How to Run It (Step-by-Step Guide)

### Step 1: Install Dependencies
Ensure you have Python 3.10+ and Node.js installed. Install the Python dependencies:

```bash
pip install -r requirements.txt
```

### Step 2: Configure Gemini API Key & Model
Get a free Gemini API Key from [Google AI Studio](https://aistudio.google.com/app/apikey).

Create a `.env` file in the root directory (or copy `.env.example`):

```bash
# On Windows (PowerShell)
Copy-Item .env.example .env

# On macOS / Linux
cp .env.example .env
```

Open `.env` and configure your key and preferred model engine:
```env
GEMINI_API_KEY=your_gemini_api_key_here

# Model Selection:
# - gemini-2.5-pro  (Most Capable: Deep Reasoning for Complex Bugs)
# - gemini-1.5-pro  (Highly Capable Reasoning)
# - gemini-3.1-flash-lite (High Speed Execution)
# - gemini-1.5-flash (Standard Fast Model)
HEALER_MODEL=gemini-2.5-pro
```

---

### Step 3: Run the Healer on the Built-in Demo App

This repository includes a ready-to-test sample project inside `./demo-app` with intentional TypeScript build errors.

Run the Healer CLI in **auto-detect mode**:

```bash
python healer.py --path ./demo-app --auto
```

#### What happens step-by-step during the run:
1. The agent runs `npm run build` inside `./demo-app`.
2. It captures the TypeScript compilation error (`Argument of type 'string' is not assignable to parameter of type 'number'`).
3. It uses `find_files` and `read_file_content` to locate `src/app.ts`.
4. It calls `replace_in_file` to surgically fix `"100"` into `100`.
5. It re-runs `npm run build` and displays **✔ Build Succeeded!**

---

## ⚙️ Running on Your Own Projects

You can run the Healer on any Next.js, React, TypeScript, or Node.js project on your computer!

### 1. Auto-Detect & Heal Mode
Automatically runs `npm run build` in your project folder, catches failures, and heals them:
```bash
python healer.py --path /path/to/your/nextjs-project --auto
```

### 2. Manual Error Paste Mode
Paste an error stack trace directly into the terminal prompt:
```bash
python healer.py --path /path/to/your/project --paste "Type error: Property 'user' does not exist on type 'Props'"
```

### 3. Custom Build Commands & Pro Models
Specify custom build scripts such as `npm test`, `npx tsc`, or `yarn build`:
```bash
python healer.py --path ./my-app --cmd "npm test" --model gemini-2.5-pro
```

---

## 📖 CLI Flags Reference

| Flag | Description | Default |
| :--- | :--- | :--- |
| `--path <dir>` | Path to target project directory | `.` (current directory) |
| `--cmd "<command>"` | Terminal build command to execute & verify | `npm run build` |
| `--auto` | Automatically run build command at startup | Enabled if no flags passed |
| `--paste "<text>"` | Paste error message or stack trace directly | None |
| `--model <model>` | Gemini Model ID (`gemini-2.5-pro`, `gemini-3.1-flash-lite`, etc.) | `gemini-2.5-pro` |

---

## 🛠️ Architecture & Tools

The Healer is built using the official **Google GenAI SDK (`google-genai`)** and **Google ADK (`google-adk`)** with native function calling.

```
┌─────────────────────────┐       ┌──────────────────────┐       ┌────────────────────────┐
│  Target App / Codebase  │ ◄───► │   Healer Agent CLI   │ ◄───► │  Google GenAI (Gemini) │
│  (Next.js / Node.js)    │       │     (healer.py)      │       │ (Function Calling Loop)│
└─────────────────────────┘       └──────────────────────┘       └────────────────────────┘
            ▲                                 │
            │  1. run_build_command           │
            │  2. find_files / grep_codebase  │
            │  3. read_file_content           │
            │  4. replace_in_file             │
            └─────────────────────────────────┘
```

### Native Python Tools (`tools.py`):
- **`run_build_command`**: Runs terminal build commands asynchronously and captures return code and stdout/stderr.
- **`find_files`**: Globs files in project tree ignoring `node_modules`, `.next`, `dist`.
- **`grep_codebase`**: Searches for symbols, variables, or error text across code files.
- **`read_file_content`**: Reads line-numbered source code.
- **`replace_in_file`**: Surgically replaces target substrings in source files.
- **`write_file_content`**: Overwrites complete file contents.

---

## 📂 Repository Layout

```
Gdg-Build-With-AI/
├── healer.py           # Main CLI Agent & Rich Terminal Visualizer
├── tools.py            # Codebase Inspection & Execution Tools
├── agent.py            # Official Google ADK Agent Definition
├── healer_agent/       # Google ADK Agent Module Directory
│   ├── __init__.py
│   └── agent.py
├── web_app.py          # FastAPI Real-time Web Dashboard Server
├── static/             # Web Dashboard Frontend (HTML, CSS, JS)
│   ├── index.html
│   ├── style.css
│   └── app.js
├── requirements.txt    # Python dependencies (google-genai, google-adk, rich, fastapi)
├── .env.example        # Environment variable template for GEMINI_API_KEY
├── README.md           # Project Documentation & User Guide
└── demo-app/           # Hackathon Demo Target Project
    ├── package.json    # Node.js project with build script
    ├── tsconfig.json   # TypeScript configuration
    └── src/
        ├── math.ts     # Helper math library
        └── app.ts      # Sample application file with intentional errors
```

---

## 📄 License
MIT License. Built for the Google Build With AI Hackathon.