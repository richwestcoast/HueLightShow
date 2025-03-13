#!/usr/bin/env python3
"""
Hue Light Show - A Python application that creates a smooth color fading effect
for Philips Hue light strips, cycling through the entire color spectrum.
"""

import json
import os
import time
import sys
import math
from phue import Bridge

# Configuration
CONFIG_FILE = 'hue-config.json'
APP_NAME = 'hue-light-show'
TRANSITION_TIME = 2  # Time in seconds for each color transition
FULL_CYCLE_TIME = 30  # Time in seconds for a full color cycle


def get_bridge_connection():
    """Connect to the Hue Bridge using saved credentials or create new ones."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
        
        print(f"Using saved connection to bridge at {config['ipAddress']}")
        bridge = Bridge(config['ipAddress'])
        
        # If the bridge is already authorized, this won't do anything
        # If not, it will raise an exception
        try:
            bridge.connect()
        except Exception as e:
            print(f"Error connecting to bridge: {e}")
            print("Please press the link button on your Hue Bridge and run the script again.")
            sys.exit(1)
            
        return bridge
    
    # No saved credentials, need to discover and authenticate
    print("No saved configuration found.")
    ip_address = input("Please enter your Hue Bridge IP address: ")
    
    print("Press the link button on your Hue Bridge within the next 30 seconds...")
    print("Then press Enter to continue...")
    input()
    
    try:
        bridge = Bridge(ip_address)
        bridge.connect()
        
        # Save the config for future use
        config = {
            "ipAddress": ip_address,
            "username": bridge.username
        }
        
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
            
        print("Successfully connected to Hue Bridge and saved credentials.")
        return bridge
    
    except Exception as e:
        print(f"Error connecting to bridge: {e}")
        print("Please make sure you pressed the link button and try again.")
        sys.exit(1)


def find_light_strip(bridge):
    """Find the light strip or ask the user which light to use."""
    lights = bridge.get_light_objects('name')
    
    # Try to find a light strip (usually has "strip" in the name)
    light_strip = None
    for light_name, light in lights.items():
        if 'strip' in light_name.lower() or 'lightstrip' in light_name.lower():
            light_strip = light
            print(f"Found light strip: {light_name}")
            break
    
    # If no specific light strip found, ask the user which light to use
    if not light_strip:
        print("Available lights:")
        light_names = list(lights.keys())
        for i, name in enumerate(light_names):
            print(f"{i+1}: {name}")
        
        if light_names:
            try:
                selection = input("Enter the number of the light to use (or press Enter for the first one): ")
                if selection.strip():
                    index = int(selection) - 1
                    if 0 <= index < len(light_names):
                        selected_name = light_names[index]
                    else:
                        print("Invalid selection. Using the first light.")
                        selected_name = light_names[0]
                else:
                    print(f"Using the first light: {light_names[0]}")
                    selected_name = light_names[0]
                
                light_strip = lights[selected_name]
            except (ValueError, IndexError):
                print("Invalid input. Using the first light.")
                light_strip = lights[light_names[0]]
        else:
            print("No lights found. Please make sure your Hue lights are connected.")
            sys.exit(1)
    
    return light_strip


def start_color_fade(light):
    """Start the color fading effect."""
    print("Starting color fade effect. Press Ctrl+C to stop.")
    
    # First, make sure the light is on with 100% brightness
    light.on = True
    light.brightness = 254  # 254 = 100% brightness (Philips Hue API uses 0-254 scale)
    
    # Calculate how many steps we need for a smooth transition
    total_steps = 360  # Using hue values from 0-360 (HSV color model)
    step_time = FULL_CYCLE_TIME / total_steps
    
    try:
        current_step = 0
        while True:
            # Calculate the current hue value (0-360)
            hue = current_step % 360
            
            # Convert hue (0-360) to the Philips Hue format (0-65535)
            hue_value = int((hue / 360) * 65535)
            
            # Set the light state with the new color
            light.transitiontime = int(TRANSITION_TIME * 10)  # Philips Hue uses 1/10 of a second as the unit
            light.hue = hue_value
            light.saturation = 254  # 254 = 100% saturation for vibrant colors (Philips Hue API uses 0-254 scale)
            
            # Increment the step
            current_step = (current_step + 1) % 360
            
            # Sleep for the calculated step time
            time.sleep(step_time)
            
    except KeyboardInterrupt:
        print("\nColor fade stopped.")
        print("Light state preserved. Exiting...")


def main():
    """Main function to run the Hue light show."""
    try:
        # Step 1: Get bridge connection
        bridge = get_bridge_connection()
        
        # Step 2: Find the light strip
        light_strip = find_light_strip(bridge)
        
        # Step 3: Start the color fading effect
        start_color_fade(light_strip)
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()