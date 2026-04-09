"""
Setup script for LuggageIQ environment
"""

import subprocess
import sys
import os
from pathlib import Path

def install_requirements():
    """Install Python requirements"""
    print("Installing Python requirements...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("Requirements installed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"Failed to install requirements: {e}")
        return False
    return True

def install_playwright():
    """Install Playwright browsers"""
    print("Installing Playwright browsers...")
    try:
        subprocess.check_call([sys.executable, "-m", "playwright", "install"])
        print("Playwright browsers installed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"Failed to install Playwright browsers: {e}")
        return False
    return True

def download_nltk_data():
    """Download NLTK data"""
    print("Downloading NLTK data...")
    try:
        import nltk
        nltk.download('punkt', quiet=True)
        nltk.download('stopwords', quiet=True)
        nltk.download('wordnet', quiet=True)
        nltk.download('averaged_perceptron_tagger', quiet=True)
        print("NLTK data downloaded successfully!")
    except Exception as e:
        print(f"Failed to download NLTK data: {e}")
        return False
    return True

def create_directories():
    """Create necessary directories"""
    print("Creating directories...")
    directories = [
        "data",
        "data/raw",
        "data/processed",
        "logs",
        "notebooks"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("Directories created successfully!")

def create_env_file():
    """Create .env file from template"""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists() and env_example.exists():
        print("Creating .env file from template...")
        env_file.write_text(env_example.read_text())
        print(".env file created!")
    elif env_file.exists():
        print(".env file already exists!")
    else:
        print(".env.example file not found!")

def main():
    """Main setup function"""
    print("Setting up LuggageIQ environment...")
    print("=" * 50)
    
    # Create directories
    create_directories()
    
    # Create .env file
    create_env_file()
    
    # Install requirements
    if not install_requirements():
        print("Failed to install requirements. Please install manually.")
        return False
    
    # Install Playwright
    if not install_playwright():
        print("Failed to install Playwright. Please install manually.")
        return False
    
    # Download NLTK data
    if not download_nltk_data():
        print("Failed to download NLTK data. Please download manually.")
        return False
    
    print("\n" + "=" * 50)
    print("Setup completed successfully!")
    print("=" * 50)
    print("Next steps:")
    print("1. Run the scraper: python scraper/main.py")
    print("2. Start the API: python api/main.py")
    print("3. Start the dashboard: streamlit run dashboard/app.py")
    print("Or run the full pipeline: python scripts/run_full_pipeline.py")
    print("=" * 50)
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
