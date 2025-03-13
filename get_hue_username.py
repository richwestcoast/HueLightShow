#!/usr/bin/env python3
"""
Simple script to get a username (authentication token) for your Philips Hue Bridge.
This script doesn't require any external dependencies.
"""

import json
import http.client
import time
import sys

def get_bridge_ip():
    """Ask the user for the Hue Bridge IP address."""
    print("To get your Hue Bridge IP address, you can:")
    print("1. Check the Philips Hue app (Settings > Hue Bridges > i)")
    print("2. Log into your router and look for the device")
    print("3. Use a network scanner app\n")
    
    return input("Enter your Hue Bridge IP address: ")

def create_user(bridge_ip):
    """Create a new user (authentication token) on the Hue Bridge."""
    print("\nPress the link button on your Hue Bridge now...")
    print("You have 30 seconds to press the button.")
    print("Waiting for button press...\n")
    
    # Give the user time to press the button
    time.sleep(5)
    
    # Create the request body
    body = json.dumps({
        "devicetype": "hue_light_show#python_script"
    })
    
    # Connect to the bridge
    conn = http.client.HTTPConnection(bridge_ip, 80)
    
    # Try to create a user
    max_attempts = 10
    for attempt in range(max_attempts):
        try:
            conn.request("POST", "/api", body)
            response = conn.getresponse()
            data = json.loads(response.read().decode())
            
            # Check if we got a success response
            if "success" in data[0]:
                username = data[0]["success"]["username"]
                return username
            elif "error" in data[0]:
                if data[0]["error"]["type"] == 101:  # Link button not pressed
                    print(f"Waiting for button press... ({attempt + 1}/{max_attempts})")
                    time.sleep(3)
                else:
                    print(f"Error: {data[0]['error']['description']}")
                    return None
        except Exception as e:
            print(f"Connection error: {e}")
            return None
    
    print("Timeout waiting for button press. Please try again.")
    return None

def main():
    """Main function to get the Hue Bridge username."""
    print("=== Philips Hue Username Generator ===\n")
    
    # Get the bridge IP
    bridge_ip = get_bridge_ip()
    
    # Create a user
    username = create_user(bridge_ip)
    
    if username:
        print("\n=== Success! ===")
        print(f"Your Hue Bridge username (authentication token) is:")
        print(f"\n{username}\n")
        
        # Update the hue-config.json file
        config = {
            "ipAddress": bridge_ip,
            "username": username
        }
        
        with open("hue-config.json", "w") as f:
            json.dump(config, f, indent=2)
        
        print("This username has been saved to hue-config.json")
        print("You can now run the light show application.")
    else:
        print("\nFailed to get a username. Please try again.")

if __name__ == "__main__":
    main()