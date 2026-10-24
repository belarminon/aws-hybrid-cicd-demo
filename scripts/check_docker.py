import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROJECT_NAME = "aws-pet-owner-app"
HOST_PORTS = {
    "FRONTEND_PORT": 3000,
    "BACKEND_PORT": 8000,
}


def is_docker_running():
    try:
        result = subprocess.run(
            ["docker", "info"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def find_available_port(preferred_port, reserved_ports):
    for port in range(preferred_port, min(preferred_port + 100, 65536)):
        if port in reserved_ports:
            continue
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            try:
                probe.bind(("0.0.0.0", port))
            except OSError:
                continue
            return port
    raise RuntimeError(
        f"No available host port found between {preferred_port} and "
        f"{min(preferred_port + 99, 65535)}."
    )


def get_compose_command():
    if shutil.which("docker") is None:
        raise RuntimeError("Docker CLI was not found. Install Docker and add it to PATH.")

    plugin_check = subprocess.run(
        ["docker", "compose", "version"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if plugin_check.returncode == 0:
        return ["docker", "compose"]

    legacy_compose = shutil.which("docker-compose")
    if legacy_compose:
        return [legacy_compose]

    raise RuntimeError(
        "Docker Compose was not found. Install the Docker Compose plugin "
        "(`docker compose`) or the `docker-compose` command."
    )


def main():
    print("Checking Docker daemon...")
    if not is_docker_running():
        print("Docker daemon is not ready. Waiting up to 15 seconds...")
        retries = 5
        while retries > 0:
            time.sleep(3)
            if is_docker_running():
                print("Docker daemon is ready.")
                break
            retries -= 1
        else:
            print("Error: Start Docker Desktop/Engine and run this script again.", file=sys.stderr)
            sys.exit(1)
    else:
        print("Docker daemon is running.")

    try:
        compose_command = get_compose_command()
        environment = os.environ.copy()
        reserved_ports = set()
        for variable, preferred_port in HOST_PORTS.items():
            selected_port = find_available_port(preferred_port, reserved_ports)
            environment[variable] = str(selected_port)
            reserved_ports.add(selected_port)
            if selected_port == preferred_port:
                print(f"{variable}: using default port {selected_port}.")
            else:
                print(
                    f"{variable}: port {preferred_port} is unavailable; "
                    f"using port {selected_port} instead."
                )

        print(f"Starting isolated Compose project '{PROJECT_NAME}'...")
        subprocess.run(
            compose_command
            + ["-p", PROJECT_NAME, "up", "-d", "--build"],
            cwd=PROJECT_ROOT,
            env=environment,
            check=True,
        )
        print(f"Frontend: http://localhost:{environment['FRONTEND_PORT']}")
        print(f"Backend:  http://localhost:{environment['BACKEND_PORT']}")
    except FileNotFoundError as error:
        print(f"Error: Could not run the required command: {error}", file=sys.stderr)
        sys.exit(1)
    except RuntimeError as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
    except subprocess.CalledProcessError as error:
        print(f"Error: Docker Compose failed with exit code {error.returncode}.", file=sys.stderr)
        sys.exit(error.returncode)

if __name__ == "__main__":
    main()