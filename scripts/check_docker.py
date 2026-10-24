import subprocess
import sys
import time

def is_docker_running():
    try:
        result = subprocess.run(["docker", "info"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False

def main():
    print("🔍 Checking Docker Desktop status...")
    if not is_docker_running():
        print("⚠️ Docker Desktop daemon is not running.")
        print("🚀 Waiting for Docker daemon to initialize...")
        
        retries = 5
        while retries > 0:
            time.sleep(3)
            if is_docker_running():
                print("✅ Docker Daemon is ready!")
                break
            retries -= 1
        else:
            print("❌ Error: Please start Docker Desktop and try again.")
            sys.exit(1)
    else:
        print("✅ Docker Desktop is running.")

    print("📦 Launching isolated containers for 'aws-pet-owner-app'...")
    subprocess.run(["docker-compose", "-p", "aws-pet-owner-app", "up", "-d", "--build"])

if __name__ == "__main__":
    main()