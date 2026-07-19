import os
import glob
import subprocess
from pathlib import Path
from typing import List, Optional, Dict, Any

IGNORE_DIRS = {".git", "node_modules", ".next", "dist", "build", "__pycache__", ".venv", "venv"}

def run_build_command(working_directory: str = ".", build_command: str = "npm run build") -> str:
    """
    Executes a terminal build command (e.g. 'npm run build') in the target directory and returns the console output.
    
    Args:
        working_directory: Absolute or relative path to project directory.
        build_command: Shell command to run (e.g., 'npm run build', 'npx tsc', 'npm test').
    """
    abs_path = os.path.abspath(working_directory)
    if not os.path.exists(abs_path):
        return f"Error: Working directory '{abs_path}' does not exist."

    try:
        # Run command with shell=True for npm/npx resolving on Windows/macOS/Linux
        result = subprocess.run(
            build_command,
            cwd=abs_path,
            shell=True,
            capture_output=True,
            text=True,
            timeout=120
        )
        output = result.stdout + "\n" + result.stderr
        status = "PASSED" if result.returncode == 0 else f"FAILED (Exit Code: {result.returncode})"
        return f"=== BUILD STATUS: {status} ===\nCommand: {build_command}\nDirectory: {abs_path}\n\n=== OUTPUT ===\n{output.strip()}"
    except subprocess.TimeoutExpired:
        return f"Error: Command '{build_command}' timed out after 120 seconds."
    except Exception as e:
        return f"Error running command '{build_command}': {str(e)}"

def read_file_content(file_path: str, start_line: int = 1, end_line: int = 500) -> str:
    """
    Reads the content of a specific file in the project with 1-based line numbers.
    
    Args:
        file_path: Relative or absolute path to the target file.
        start_line: 1-based starting line number to read.
        end_line: 1-based ending line number to read.
    """
    abs_path = os.path.abspath(file_path)
    if not os.path.isfile(abs_path):
        return f"Error: File '{file_path}' not found."

    try:
        with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        
        total_lines = len(lines)
        start_idx = max(0, start_line - 1)
        end_idx = min(total_lines, end_line)
        
        selected_lines = lines[start_idx:end_idx]
        formatted = []
        for idx, line in enumerate(selected_lines, start=start_idx + 1):
            formatted.append(f"{idx:4d} | {line.rstrip()}")
        
        header = f"=== File: {file_path} (Lines {start_idx+1}-{end_idx} of {total_lines}) ===\n"
        return header + "\n".join(formatted)
    except Exception as e:
        return f"Error reading file '{file_path}': {str(e)}"

def write_file_content(file_path: str, content: str) -> str:
    """
    Overwrites or creates a file with the provided source code content.
    
    Args:
        file_path: Target file path to write to.
        content: Complete new source code content to write.
    """
    abs_path = os.path.abspath(file_path)
    try:
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote {len(content)} bytes to '{file_path}'."
    except Exception as e:
        return f"Error writing to file '{file_path}': {str(e)}"

def find_files(working_directory: str = ".", pattern: str = "*") -> str:
    """
    Finds files in the project directory matching a glob pattern, ignoring build/dependency folders.
    
    Args:
        working_directory: Base directory to search.
        pattern: File extension pattern (e.g. '*.tsx', '*.ts', '*.js', 'package.json').
    """
    abs_path = os.path.abspath(working_directory)
    matched_files = []
    
    for root, dirs, files in os.walk(abs_path):
        # Filter out ignored directories in-place
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        
        for file in files:
            rel_dir = os.path.relpath(root, abs_path)
            rel_path = os.path.normpath(os.path.join(rel_dir, file)) if rel_dir != "." else file
            
            if pattern == "*" or pattern.lower() in file.lower() or file.endswith(pattern.replace("*", "")):
                matched_files.append(rel_path)
                
    if not matched_files:
        return f"No files found matching pattern '{pattern}' in '{working_directory}'."
    
    return f"=== Found {len(matched_files)} matching file(s) ===\n" + "\n".join(matched_files[:100])

def grep_codebase(working_directory: str = ".", query: str = "") -> str:
    """
    Searches for a text string or symbol across the code files in the codebase.
    
    Args:
        working_directory: Base directory to search.
        query: String or identifier to locate (e.g. variable name, function call, error message snippet).
    """
    if not query.strip():
        return "Error: Search query cannot be empty."
        
    abs_path = os.path.abspath(working_directory)
    matches = []
    
    valid_exts = {".ts", ".tsx", ".js", ".jsx", ".json", ".css", ".html", ".py", ".md", ".mjs", ".cjs"}
    
    for root, dirs, files in os.walk(abs_path):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext not in valid_exts:
                continue
                
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, abs_path)
            
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    for line_num, line in enumerate(f, 1):
                        if query in line:
                            matches.append(f"{rel_path}:{line_num}: {line.strip()}")
                            if len(matches) >= 50:
                                break
            except Exception:
                continue
                
    if not matches:
        return f"No occurrences of '{query}' found in '{working_directory}'."
        
    return f"=== Found {len(matches)} match(es) for '{query}' ===\n" + "\n".join(matches)
