import os
import re
import time
import requests
import subprocess

# --- CONFIGURATION ---
AI_ENDPOINT = "http://localhost:8070/generate"  
PROJECT_NAME = "phillipedinburg"
GITHUB_REPO = "phillipedinburg/native-android-app"

KOTLIN_FILE_PATH = "app/src/main/java/com/example/mynativeapp/MainActivity.kt"

def get_current_code():
    if os.path.exists(KOTLIN_FILE_PATH):
        with open(KOTLIN_FILE_PATH, "r") as f:
            return f.read()
    return """package com.example.mynativeapp

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.material3.Text

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            Text("Hello Native Android!")
        }
    }
}"""

def query_custom_ai_hoster(user_prompt, current_code):
    system_instructions = (
        "You are an expert native Android Kotlin developer using Jetpack Compose. "
        "Return ONLY valid, executable Kotlin code for MainActivity.kt inside a markdown block "
        "(```kotlin ... ```). Package name MUST be com.example.mynativeapp."
    )
    
    full_prompt = (
        f"{system_instructions}\n\n"
        f"CURRENT KOTLIN CODE:\n```kotlin\n{current_code}\n```\n\n"
        f"USER REQUEST: {user_prompt}"
    )

    payload = {
        "project": PROJECT_NAME,
        "prompt": full_prompt
    }

    headers = {"Content-Type": "application/json"}

    print(f"\n🤖 Sending request to local AI hoster at {AI_ENDPOINT}...")
    try:
        response = requests.post(AI_ENDPOINT, json=payload, headers=headers, timeout=120)
        
        try:
            data = response.json()
            raw_content = data.get("response") or data.get("text") or data.get("content") or str(data)
        except Exception:
            raw_content = response.text

        code_match = re.search(r"```kotlin\n(.*?)```", raw_content, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()
        
        return raw_content.strip()

    except Exception as e:
        print(f"❌ Error communicating with AI server: {e}")
        return current_code

def save_local_code(new_code):
    os.makedirs(os.path.dirname(KOTLIN_FILE_PATH), exist_ok=True)
    with open(KOTLIN_FILE_PATH, "w") as f:
        f.write(new_code)
    print(f"💾 Updated code saved locally to: {KOTLIN_FILE_PATH}")

def push_to_github_and_build():
    print("\n📤 Committing code and pushing to GitHub...")
    try:
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", "AI Kotlin Code Update"], check=True)
        subprocess.run(["git", "push", "origin", "main"], check=True)
    except Exception as e:
        print(f"❌ Git Push Error: {e}")
        return

    print("⏳ Cloud build started on GitHub Actions...")
    time.sleep(15)
    
    while True:
        try:
            status_out = subprocess.check_output(
                ["gh", "run", "list", "--repo", GITHUB_REPO, "--limit", "1", "--json", "status,conclusion"],
                text=True
            )
            if '"status":"completed"' in status_out:
                if '"conclusion":"success"' in status_out:
                    print("✅ Native APK built successfully!")
                    subprocess.run(["gh", "run", "download", "--repo", GITHUB_REPO, "-n", "app-debug"], check=True)
                    print("🎉 Process finished! 'app-debug.apk' downloaded to current directory.")
                    break
                else:
                    print("❌ Cloud compilation failed on GitHub Actions.")
                    subprocess.run(["gh", "run", "view", "--repo", GITHUB_REPO, "--log-failed"])
                    break
            else:
                print("🕒 Compiling native Android Gradle project... checking back in 20s.")
                time.sleep(20)
        except Exception as e:
            print(f"❌ Error checking build status: {e}")
            break

def get_multiline_input(prompt_text):
    print(prompt_text)
    print("👉 (Paste prompt below. Press ENTER, type 'END' on a new line, then press ENTER again):\n")
    lines = []
    while True:
        try:
            line = input()
            if line.strip().upper() == "END":
                break
            lines.append(line)
        except EOFError:
            break
    return "\n".join(lines).strip()

def main():
    print("=== Termux Native Android AI Orchestrator ===")
    print(f"Configured for project: '{PROJECT_NAME}' | Endpoint: {AI_ENDPOINT}\n")
    
    while True:
        current_code = get_current_code()
        
        print("\n--- ACTION MENU ---")
        print("1. Ask AI to generate/edit Kotlin app code")
        print("2. View current local Kotlin code")
        print("3. Push to GitHub & Build APK")
        print("4. Exit")
        
        choice = input("\nSelect choice (1-4): ").strip()
        
        if choice == "1":
            user_prompt = get_multiline_input("\nDescribe what feature or UI to build/change:")
            
            if not user_prompt:
                print("⚠️️ Empty prompt received. Aborting.")
                continue

            new_code = query_custom_ai_hoster(user_prompt, current_code)
            
            print("\n--- GENERATED KOTLIN CODE PREVIEW ---")
            print(new_code[:350] + ("\n... [truncated] ..." if len(new_code) > 350 else ""))
            
            confirm = input("\nAccept and save this code locally? (y/n): ").strip().lower()
            if confirm == 'y':
                save_local_code(new_code)
            else:
                print("❌ Discarded generated code.")
                
        elif choice == "2":
            print("\n--- CURRENT KOTLIN FILE ---")
            print(current_code)
            
        elif choice == "3":
            confirm = input("Push to GitHub and trigger Gradle Cloud APK build now? (y/n): ").strip().lower()
            if confirm == 'y':
                push_to_github_and_build()
                
        elif choice == "4":
            print("Exiting orchestrator.")
            break

if __name__ == "__main__":
    main()
