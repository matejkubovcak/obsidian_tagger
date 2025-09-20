#!/usr/bin/env python3
import subprocess
import time
import signal
import sys
import requests
from pathlib import Path

def check_ollama_available():
    """Check if Ollama is already running"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        return response.status_code == 200
    except:
        return False

def start_ollama():
    """Start Ollama serve process"""
    print("Starting Ollama serve...")
    try:
        # Start ollama serve in background
        process = subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=None if sys.platform == "win32" else lambda: signal.signal(signal.SIGINT, signal.SIG_IGN)
        )
        return process
    except FileNotFoundError:
        print("Error: 'ollama' command not found. Please make sure Ollama is installed and in your PATH.")
        return None

def wait_for_ollama(max_wait=30):
    """Wait for Ollama to be ready"""
    print("Waiting for Ollama to be ready...")
    for i in range(max_wait):
        if check_ollama_available():
            print("Ollama is ready!")
            return True
        time.sleep(1)
        print(f"Waiting... ({i+1}/{max_wait})")
    
    print("Timeout: Ollama did not start within 30 seconds")
    return False

def run_tagger():
    """Run the simple_llm_tagger.py script"""
    print("Running simple_llm_tagger.py...")
    try:
        result = subprocess.run(
            [sys.executable, "simple_llm_tagger.py"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        return result.returncode == 0
    except Exception as e:
        print(f"Error running tagger: {e}")
        return False

def stop_ollama(process):
    """Stop the Ollama process"""
    if process and process.poll() is None:
        print("Stopping Ollama...")
        try:
            process.terminate()
            # Wait for graceful shutdown
            try:
                process.wait(timeout=10)
                print("Ollama stopped gracefully")
            except subprocess.TimeoutExpired:
                print("Force killing Ollama...")
                process.kill()
                process.wait()
                print("Ollama force stopped")
        except Exception as e:
            print(f"Error stopping Ollama: {e}")

def main():
    ollama_process = None
    
    try:
        # Check if Ollama is already running
        if check_ollama_available():
            print("Ollama is already running, using existing instance")
        else:
            # Start Ollama
            ollama_process = start_ollama()
            if not ollama_process:
                return 1
            
            # Wait for Ollama to be ready
            if not wait_for_ollama():
                return 1
        
        # Run the tagger
        success = run_tagger()
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1
    finally:
        # Only stop Ollama if we started it
        if ollama_process:
            stop_ollama(ollama_process)

if __name__ == "__main__":
    sys.exit(main())
