#!/usr/bin/env python3
"""
InsightForge-AI Setup Script
Run this once to set up everything automatically.
Usage: python setup.py
"""
import os
import sys
import subprocess
import platform
import time


def print_banner():
    print("""
╔══════════════════════════════════════════════════════╗
║          InsightForge-AI — Setup Wizard             ║
║     AI-powered Business Intelligence Platform       ║
╚══════════════════════════════════════════════════════╝
""")


def check_docker():
    try:
        subprocess.run(["docker", "--version"], capture_output=True, check=True)
        print("✅ Docker found")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Docker not found. Please install Docker Desktop from https://docker.com")
        return False


def check_ollama():
    try:
        import httpx
        response = httpx.get("http://localhost:11434/api/tags", timeout=3)
        return response.status_code == 200
    except Exception:
        return False


def install_ollama():
    system = platform.system()
    print("\n📦 Ollama not found. Installing...")

    if system == "Windows":
        print("Please download Ollama for Windows from: https://ollama.com/download/windows")
        print("After installing, run 'ollama serve' in a separate terminal, then re-run this script.")
        input("Press Enter after Ollama is installed and running...")
    elif system == "Darwin":
        subprocess.run(["brew", "install", "ollama"], check=True)
        subprocess.Popen(["ollama", "serve"])
        time.sleep(3)
    elif system == "Linux":
        subprocess.run(
            "curl -fsSL https://ollama.com/install.sh | sh",
            shell=True, check=True
        )
        subprocess.Popen(["ollama", "serve"])
        time.sleep(3)


def pull_model(model_name: str = "llama3.2"):
    print(f"\n🤖 Checking if {model_name} is downloaded...")

    try:
        import httpx
        response = httpx.get("http://localhost:11434/api/tags", timeout=5)
        models = [m["name"] for m in response.json().get("models", [])]
        if any(model_name in m for m in models):
            print(f"✅ {model_name} already downloaded")
            return True
    except Exception:
        pass

    print(f"\n🔽 Downloading {model_name} (2GB — this takes 5-15 minutes on first run)...")
    print("This only happens once. Future runs are instant.\n")

    answer = input(f"Download {model_name} now? (yes/no): ").strip().lower()
    if answer not in ["yes", "y"]:
        print("Skipping model download. Set LLM_PROVIDER=groq in .env to use cloud LLM instead.")
        return False

    try:
        subprocess.run(["ollama", "pull", model_name], check=True)
        print(f"✅ {model_name} downloaded successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to download model: {e}")
        return False


def setup_env():
    env_path = os.path.join("backend", ".env")
    example_path = os.path.join("backend", ".env.example")

    if os.path.exists(env_path):
        print("✅ backend/.env already exists")
        return

    print("\n⚙️  Creating backend/.env from template...")
    with open(example_path, "r") as f:
        content = f.read()

    with open(env_path, "w") as f:
        f.write(content)

    print("✅ backend/.env created")
    print("📝 Note: LLM_PROVIDER is set to 'ollama' by default (local, unlimited, free)")


def start_with_docker():
    print("\n🐳 Starting with Docker Compose...")
    subprocess.run(["docker-compose", "up", "--build", "-d"], check=True)

    print("\n⏳ Waiting for services to start...")
    time.sleep(10)

    print("🔄 Running database migrations...")
    subprocess.run(
        ["docker-compose", "exec", "api", "alembic", "upgrade", "head"],
        check=True
    )

    print("""
╔══════════════════════════════════════════════════════╗
║              InsightForge-AI is Ready! 🎉           ║
╠══════════════════════════════════════════════════════╣
║  Frontend:  http://localhost:8501                   ║
║  API Docs:  http://localhost:8000/docs              ║
║  API Health: http://localhost:8000/health           ║
╚══════════════════════════════════════════════════════╝
""")


def main():
    print_banner()

    if not check_docker():
        sys.exit(1)

    if not check_ollama():
        install_ollama()

    pull_model("llama3.2")
    setup_env()
    start_with_docker()


if __name__ == "__main__":
    main()