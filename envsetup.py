import os
import sys
import subprocess
import platform

def create_virtual_environment():
    """Create and set up the virtual environment"""
    print("🚀 Setting up Virtual Environment...")

    # Determine the correct python executable
    python_executable = sys.executable

    # Determine OS-specific commands
    is_windows = platform.system().lower() == "windows"
    venv_path = "venv"
    activate_script = os.path.join(venv_path, "Scripts" if is_windows else "bin", "activate")

    try:
        # Create virtual environment
        subprocess.run([python_executable, "-m", "venv", venv_path], check=True)
        print("✅ Virtual environment created successfully")

        # Construct the activation command
        if is_windows:
            activate_cmd = f"call {activate_script}"
            pip_cmd = f"{venv_path}\\Scripts\\pip"
        else:
            activate_cmd = f"source {activate_script}"
            pip_cmd = f"{venv_path}/bin/pip"

        # Upgrade pip
        subprocess.run([pip_cmd, "install", "--upgrade", "pip"], check=True)
        print("✅ Pip upgraded successfully")

        # Install requirements
        subprocess.run([pip_cmd, "install", "-r", "requirements.txt"], check=True)
        print("✅ Requirements installed successfully")

        # Print activation instructions
        print("\n🎉 Setup completed successfully!")
        print("\nTo activate the virtual environment:")
        if is_windows:
            print(f"Run: {activate_script}")
        else:
            print(f"Run: source {activate_script}")

    except subprocess.CalledProcessError as e:
        print(f"❌ Error during setup: {e}")
        sys.exit(1)

if __name__ == "__main__":
    create_virtual_environment()