import getpass
import json
import os
from garminconnect import Garmin

TOKEN_FILE = "garmin_tokens.json"

def setup_garmin_auth():
    print("=== Garmin MFA Setup ===")
    print("This script runs ONE TIME on your laptop to generate an OAuth session token.")
    print("It will prompt for your MFA code if you have it enabled.")
    
    email = input("Garmin Email: ")
    password = getpass.getpass("Garmin Password: ")
    
    try:
        # Initialize client (this triggers MFA if enabled)
        # Note: If MFA is required, the garminconnect library handles the prompt in the terminal
        client = Garmin(email, password)
        client.login()
        
        # Save the tokens to a file
        tokens = {
            "oauth1_token": client.oauth1_token,
            "oauth1_token_secret": client.oauth1_token_secret,
            "oauth2_token": client.oauth2_token
        }
        
        with open(TOKEN_FILE, "w") as f:
            json.dump(tokens, f)
            
        print(f"\n✅ SUCCESS! Session saved to '{TOKEN_FILE}'.")
        print("You can now safely remove your password from your mind.")
        print("Just copy this JSON file into your Home Assistant /config folder so the add-on can use it!")
        
    except Exception as e:
        print(f"\n❌ Login Failed: {e}")

if __name__ == "__main__":
    setup_garmin_auth()
