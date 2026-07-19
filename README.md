# ⚡ Autonomous Codebase Healer

**Track:** Developer Tools  
**Built With:** Python, Google GenAI SDK (`google-genai`), Gemini AI, and Rich Terminal UI.

The **Autonomous Codebase Healer** is a terminal utility for Next.js, TypeScript, and Node.js development. When your project build fails, run the healer agent. The agent uses built-in codebase search to locate broken source files, applies surgical code patches, and autonomously re-executes `npm run build` in the terminal to visually verify the fix.

---

## 🌟 The "Wow" Hackathon Demo Factor

Watching an AI agent physically navigate your directory tree, open broken files, rewrite code diffs on screen, and re-trigger terminal build commands until green checkmarks appear is a top-tier developer tools demonstration.

```
 ┌──────────────────────────────────────────────────────────┐
 │ ⚡ AUTONOMOUS CODEBASE HEALER ⚡                         │
 │ Track: Developer Tools | Powered by Google GenAI SDK     │
 └──────────────────────────────────────────────────────────┘
  ⚙️ Running terminal command: npm run build in ./demo-app
  ✖ Build Failed! (Exit Code: 2)

  🤖 Agent Strategy: Analyzed TypeScript error in src/app.ts
  📖 Reading File: ./demo-app/src/app.ts
  🛠️ Patching File: ./demo-app/src/app.ts
  ⚙️ Running terminal command: npm run build in ./demo-app
  ✔ Build Succeeded!

  🎉 HEALER WORKFLOW COMPLETE!
```

---

## 🚀 Quick Start

### 1. Prerequisites
- **Python 3.10+**
- **Node.js & npm** (for Next.js / TypeScript target projects)
- **Google Gemini API Key** ([Get key from Google AI Studio](https://aistudio.google.com/))

### 2. Setup Environment
Clone or navigate to the project directory:

```bash
# Install Python dependencies
pip install -r requirements.txt

# Set your Gemini API key
# On Windows (PowerShell):
$env:GEMINI_API_KEY="your_api_key_here"

# On macOS / Linux:
export GEMINI_API_KEY="your_api_key_here"
```

Alternatively, copy `.env.example` to `.env` and fill in `GEMINI_API_KEY`.

---

## 🧪 Try the Included Demo App

The repository includes a ready-to-test sample project inside `./demo-app` with intentional TypeScript build errors.

Run the Healer in auto-detection mode:

```bash
python healer.py --path ./demo-app --auto
```

### What happens live:
1. Healer runs `npm run build` inside `./demo-app`.
2. Captures TypeScript compilation errors.
3. Uses `find_files`, `grep_codebase`, and `read_file_content` to inspect `src/app.ts` and `src/math.ts`.
4. Writes a clean code fix directly using `write_file_content`.
5. Re-runs `npm run build` to verify that the build **PASSES** with exit code 0.

---

## 📖 CLI Usage & Options

```bash
python healer.py [FLAGS]
```

| Flag | Description | Default |
| :--- | :--- | :--- |
| `--path <dir>` | Target project directory path | `.` (current directory) |
| `--cmd "<command>"` | Terminal build command to execute | `npm run build` |
| `--auto` | Automatically run build command at startup | `True` if no flags passed |
| `--paste "<error>"` | Manually paste error log text | None |
| `--model <model_id>` | Gemini model name | `gemini-2.5-flash` |

### Custom Project Usage Example:
```bash
# Run healer on your Next.js project
python healer.py --path C:\projects\my-nextjs-app --cmd "npm run build"
```

---

## 🛠️ Architecture & Google GenAI Integration

The Healer is powered by the new official **Google GenAI SDK (`google-genai`)** with native Function Calling / Tool Use.

```
┌─────────────────┐       ┌────────────────────┐       ┌──────────────────────┐
│  Target App     │ ◄───► │  Autonomous Agent  │ ◄───► │   Google GenAI SDK   │
│  (Next.js/Node) │       │    (healer.py)     │       │ (Gemini 2.5 / 3.5)   │
└─────────────────┘       └────────────────────┘       └──────────────────────┘
         ▲                          │
         │  1. Run Build            │
         │  2. Search Codebase      │ (Function Calling Loop)
         │  3. Read & Edit Files    │
         └──────────────────────────┘
```

### Native Tools (`tools.py`):
- `run_build_command`: Executes terminal build commands asynchronously.
- `read_file_content`: Reads line-numbered source files.
- `write_file_content`: Applies patches to broken files.
- `find_files`: Lists project files matching glob patterns.
- `grep_codebase`: Locates symbols and error references across source files.

---

## 📄 License
MIT License. Built for the Google Build With AI Hackathon.