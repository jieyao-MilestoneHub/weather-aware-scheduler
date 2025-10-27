#!/usr/bin/env python
"""Check which API mode is currently active."""

import os
from pathlib import Path

# Load .env file
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    from dotenv import load_dotenv
    load_dotenv(env_file)
else:
    print("[WARNING] .env file not found. Using environment variables.")

# Check MOCK_MODE
mock_mode = os.getenv("MOCK_MODE", "true").lower() in ("true", "1", "yes")
openai_key = os.getenv("OPENAI_API_KEY", "")
azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")

print("=" * 60)
print("Weather-Aware Scheduler - API Mode Check")
print("=" * 60)

print(f"\nMOCK_MODE: {os.getenv('MOCK_MODE', 'true')} (default: true)")
print(f"Using Mock Tools: {mock_mode}")
print(f"Will call OpenAI API: {not mock_mode}")

print("\n" + "=" * 60)
print("API Configuration")
print("=" * 60)

if mock_mode:
    print("\n[OK] Mock Mode Enabled")
    print("  - No API keys required")
    print("  - Uses local mock weather/calendar data")
    print("  - Fast execution (<10ms per request)")
    print("  - No API costs")
else:
    print("\n[!] Real API Mode Enabled")

    # Check OpenAI configuration
    if openai_key and openai_key != "sk-...":
        print(f"  - OpenAI API Key: {openai_key[:10]}...{openai_key[-4:]}")
        print("  - Provider: OpenAI (standard)")
    elif azure_endpoint:
        print(f"  - Azure Endpoint: {azure_endpoint}")
        print("  - Provider: Azure OpenAI")
        azure_key = os.getenv("AZURE_OPENAI_API_KEY", "")
        if azure_key:
            print(f"  - Azure API Key: {azure_key[:10]}...{azure_key[-4:]}")
    else:
        print("  [ERROR] No valid API configuration found!")
        print("  Please set one of:")
        print("    - OPENAI_API_KEY (for standard OpenAI)")
        print("    - AZURE_OPENAI_ENDPOINT + AZURE_OPENAI_API_KEY (for Azure)")
        exit(1)

    print("\n  [!] WARNING: Running tests will call OpenAI API")
    print("  [!] Estimated cost: ~$0.0003 per test")
    print("  [!] Check usage: https://platform.openai.com/usage")

print("\n" + "=" * 60)
print("Testing Commands")
print("=" * 60)

if mock_mode:
    print("\nRun tests (Mock Mode - Free):")
    print("  uv run pytest tests/integration/test_sunny_path.py -v")
else:
    print("\nRun tests (Real API - Costs Money!):")
    print("  uv run pytest tests/integration/test_sunny_path.py -v")
    print("\nSwitch to Mock Mode:")
    print("  1. Edit .env and set: MOCK_MODE=True")
    print("  2. Or run: set MOCK_MODE=True (Windows CMD)")

print("\n" + "=" * 60)
