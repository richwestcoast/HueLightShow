#!/usr/bin/env python3
"""
Hue Light Show Web Controller - A Python application that creates a smooth color fading effect
for Philips Hue light strips with a web interface for control.
"""

import json
import os
import time
import sys
import math
import threading
import logging
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
from phue import Bridge

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
CONFIG_FILE = 'hue-config.json'
APP_NAME = 'hue-light-show'
TRANSITION_TIME = 2  # Time in seconds for each color transition
FULL_CYCLE_TIME = 30  # Time in seconds for a full color cycle
DEFAULT_MIN_BRIGHTNESS = 50  # Default minimum brightness (%)
DEFAULT_MAX_BRIGHTNESS = 100  # Default maximum brightness (%)

# Flask app setup
app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SECRET_KEY'] = 'hue-light-show-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global variables
bridge = None
available_lights = {}  # Dictionary of all available lights
selected_lights = []   # List of selected light IDs
light_show_thread = None
light_show_running = False
light_show_paused = False
current_hue = 0
current_brightness = 100
current_saturation = 100
min_brightness = DEFAULT_MIN_BRIGHTNESS
max_brightness = DEFAULT_MAX_BRIGHTNESS
transition_time = TRANSITION_TIME
full_cycle_time = FULL_CYCLE_TIME


def get_bridge_connection():
    """Connect to the Hue Bridge using saved credentials or create new ones."""
    # Check if we have saved credentials
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
            
            logger.info(f"Using saved connection to bridge at {config['ipAddress']}")
            logger.info("Attempting to connect to the bridge...")
            bridge = Bridge(config['ipAddress'])
            
            # If the bridge is already authorized, this won't do anything
            # If not, it will raise an exception
            try:
                bridge.connect()
                logger.info("Successfully connected to the Hue Bridge.")
                return bridge
            except Exception as e:
                logger.info(f"Authentication error: {e}")
                # Continue to the registration process
        except Exception as e:
            logger.info(f"Error opening config file, will attempt bridge registration")
    else:
        logger.info("No saved configuration found.")
    
    # Try to discover bridges on the network
    try:
        from phue import PhueRegistrationException
        
        # Ask for IP address
        ip_address = input("Please enter your Hue Bridge IP address: ")
        
        print("\n===== IMPORTANT: HUE BRIDGE LINK BUTTON =====")
        print("1. Go to your Hue Bridge (the round white device)")
        print("2. Press the large link button on top of the bridge")
        print("3. Return here within 30 seconds and press Enter")
        print("==============================================\n")
        
        input("Press Enter after you've pressed the link button on the Hue Bridge...")
        
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
                
            logger.info("Successfully connected to Hue Bridge and saved credentials.")
            return bridge
        
        except PhueRegistrationException:
            logger.error("Error: The link button wasn't pressed in time.")
            logger.error("Please restart the application and try again.")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Error connecting to bridge: {e}")
            logger.error("Please make sure you pressed the link button and try again.")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


def get_all_lights(bridge):
    """Get all available lights from the Hue Bridge."""
    global available_lights, selected_lights
    
    # Get all lights from the bridge
    lights = bridge.get_light_objects('id')
    available_lights = {}
    
    # Convert to a dictionary with light ID as key
    for light_id, light in lights.items():
        light_name = light.name
        light_type = "Unknown"
        
        # Try to determine light type
        if 'strip' in light_name.lower() or 'lightstrip' in light_name.lower():
            light_type = "Light Strip"
        elif 'bulb' in light_name.lower():
            light_type = "Bulb"
        elif 'lamp' in light_name.lower():
            light_type = "Lamp"
        
        # Store light information
        available_lights[light_id] = {
            'id': light_id,
            'name': light_name,
            'type': light_type,
            'object': light
        }
        
        logger.info(f"Found light: {light_name} (ID: {light_id}, Type: {light_type})")
    
    # If no lights found, exit
    if not available_lights:
        logger.error("No lights found. Please make sure your Hue lights are connected.")
        sys.exit(1)
    
    # By default, select all lights
    if not selected_lights:
        selected_lights = list(available_lights.keys())
        logger.info(f"Selected all {len(selected_lights)} lights by default")
    
    return available_lights


def set_selected_lights(light_ids):
    """Set which lights are included in the light show."""
    global selected_lights
    
    # Debug log the incoming light_ids
    logger.info(f"Received light_ids: {light_ids}")
    
    # Log the available_lights keys for debugging
    logger.info(f"Available light keys (types): {[(k, type(k).__name__) for k in available_lights.keys()]}")
    
    # Check if available_lights keys are integers or strings
    # Get a sample key to determine the type
    available_key_type = None
    if available_lights:
        sample_key = next(iter(available_lights.keys()))
        available_key_type = type(sample_key)
        logger.info(f"Available lights keys are of type: {available_key_type.__name__}")
    
    # Convert light_ids to the same type as the keys in available_lights
    processed_ids = []
    for light_id in light_ids:
        if available_key_type == int and isinstance(light_id, str) and light_id.isdigit():
            processed_ids.append(int(light_id))
        elif available_key_type == str and not isinstance(light_id, str):
            processed_ids.append(str(light_id))
        else:
            processed_ids.append(light_id)
    
    logger.info(f"Processed light_ids: {processed_ids}")
    
    # Validate light IDs
    valid_ids = [light_id for light_id in processed_ids if light_id in available_lights]
    
    logger.info(f"Valid light_ids: {valid_ids}")
    
    if not valid_ids and processed_ids:  # Only warn if user actually sent some IDs but none were valid
        logger.warning("No valid lights selected. Keeping previous selection.")
        return False
    
    # Log the change in selection
    old_selection = set(selected_lights)
    new_selection = set(valid_ids)
    
    added = new_selection - old_selection
    removed = old_selection - new_selection
    
    if added:
        logger.info(f"Adding lights: {', '.join([available_lights[light_id]['name'] for light_id in added])}")
    
    if removed:
        logger.info(f"Removing lights: {', '.join([available_lights[light_id]['name'] for light_id in removed])}")
    
    # If the user selected no lights, keep the current selection
    if not valid_ids and not processed_ids:
        logger.warning("Empty light selection received. Keeping previous selection.")
        return False
    
    selected_lights = valid_ids
    logger.info(f"Selected {len(selected_lights)} lights: {', '.join([available_lights[light_id]['name'] for light_id in selected_lights])}")
    
    # If the light show is running, make sure newly added lights are turned on
    if light_show_running and not light_show_paused:
        for light_id in selected_lights:
            try:
                light = available_lights[light_id]['object']
                if not light.on:
                    light.on = True
                    logger.info(f"Turned on newly selected light: {available_lights[light_id]['name']}")
            except Exception as e:
                logger.error(f"Error turning on light {light_id}: {e}")
    
    return True


def get_selected_lights():
    """Get the currently selected lights."""
    return {
        'available': available_lights,
        'selected': selected_lights
    }


def hue_to_rgb(h):
    """Convert Hue value (0-360) to RGB."""
    h = h % 360
    c = 1
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = 0
    
    if 0 <= h < 60:
        r, g, b = c, x, 0
    elif 60 <= h < 120:
        r, g, b = x, c, 0
    elif 120 <= h < 180:
        r, g, b = 0, c, x
    elif 180 <= h < 240:
        r, g, b = 0, x, c
    elif 240 <= h < 300:
        r, g, b = x, 0, c
    else:
        r, g, b = c, 0, x
    
    r, g, b = int((r + m) * 255), int((g + m) * 255), int((b + m) * 255)
    return f"#{r:02x}{g:02x}{b:02x}"


def run_light_show():
    """Run the light show in a separate thread."""
    global light_show_running, light_show_paused, current_hue, current_brightness, current_saturation
    
    if not selected_lights:
        logger.error("No lights selected for the light show")
        light_show_running = False
        return
    
    logger.info(f"Starting color fade effect on {len(selected_lights)} lights. Control via web interface at http://localhost:3000")
    logger.info(f"Speed settings: Transition time = {transition_time}s, Full cycle time = {full_cycle_time}s")
    
    # Calculate how many steps we need for a smooth transition
    total_steps = 360  # Using hue values from 0-360 (HSV color model)
    step_time = full_cycle_time / total_steps
    
    current_step = 0
    
    try:
        while light_show_running:
            if not light_show_paused:
                # Check if we have any selected lights
                if not selected_lights:
                    logger.warning("No lights selected, waiting for selection")
                    time.sleep(1)
                    continue
                
                # Make sure all currently selected lights are on
                for light_id in selected_lights:
                    try:
                        if light_id in available_lights:
                            light = available_lights[light_id]['object']
                            if not light.on:
                                light.on = True
                                logger.info(f"Turned on {available_lights[light_id]['name']}")
                    except Exception as e:
                        logger.error(f"Error turning on light {light_id}: {e}")
                
                # Calculate the current hue value (0-360)
                current_hue = current_step % 360
                
                # Calculate brightness based on min/max settings
                # We'll use a sine wave to smoothly transition between min and max brightness
                brightness_range = max_brightness - min_brightness
                brightness_offset = (math.sin(current_step * math.pi / 180) + 1) / 2  # 0 to 1
                current_brightness = min_brightness + (brightness_offset * brightness_range)
                
                # Convert values to Philips Hue format
                hue_value = int((current_hue / 360) * 65535)
                brightness_value = int((current_brightness / 100) * 254)  # Convert percentage to 0-254
                
                # Set the light state for all selected lights
                for light_id in selected_lights:
                    try:
                        if light_id in available_lights:
                            light = available_lights[light_id]['object']
                            light.transitiontime = int(transition_time * 10)  # Philips Hue uses 1/10 of a second as the unit
                            light.hue = hue_value
                            light.saturation = 254  # 254 = 100% saturation for vibrant colors
                            light.brightness = brightness_value
                    except Exception as e:
                        logger.error(f"Error updating light {light_id}: {e}")
                
                # Increment the step
                current_step = (current_step + 1) % 360
                
                # Emit the current state to connected clients
                emit_state()
            
            # Sleep for the calculated step time
            time.sleep(step_time)
            
    except Exception as e:
        logger.error(f"Error in light show thread: {e}")
        light_show_running = False


def emit_state():
    """Emit the current state to all connected clients."""
    # Prepare light information
    lights_info = {}
    for light_id, light_data in available_lights.items():
        lights_info[light_id] = {
            'id': light_id,
            'name': light_data['name'],
            'type': light_data['type'],
            'selected': light_id in selected_lights
        }
    
    state = {
        'running': light_show_running,
        'paused': light_show_paused,
        'hue': current_hue,
        'brightness': current_brightness,
        'saturation': current_saturation,
        'color': hue_to_rgb(current_hue),
        'min_brightness': min_brightness,
        'max_brightness': max_brightness,
        'transition_time': transition_time,
        'full_cycle_time': full_cycle_time,
        'lights': lights_info,
        'selected_lights': selected_lights
    }
    socketio.emit('state_update', state)


def start_light_show():
    """Start the light show in a separate thread."""
    global light_show_thread, light_show_running, light_show_paused
    
    if light_show_thread is None or not light_show_thread.is_alive():
        light_show_running = True
        light_show_paused = False
        light_show_thread = threading.Thread(target=run_light_show)
        light_show_thread.daemon = True
        light_show_thread.start()
        logger.info("Light show started")
    elif light_show_paused:
        light_show_paused = False
        logger.info("Light show resumed")
    
    emit_state()


def stop_light_show():
    """Stop the light show."""
    global light_show_running, light_show_paused
    
    light_show_running = False
    light_show_paused = False
    logger.info("Light show stopped")
    emit_state()


def pause_light_show():
    """Pause the light show."""
    global light_show_paused
    
    if light_show_running and not light_show_paused:
        light_show_paused = True
        logger.info("Light show paused")
        emit_state()


def set_manual_color(hue, brightness, saturation):
    """Set a manual color when the light show is paused."""
    global current_hue, current_brightness, current_saturation
    
    if light_show_running and light_show_paused:
        current_hue = hue
        current_brightness = brightness
        current_saturation = saturation
        
        # Convert values to Philips Hue format
        hue_value = int((hue / 360) * 65535)
        brightness_value = int((brightness / 100) * 254)  # Convert percentage to 0-254
        saturation_value = int((saturation / 100) * 254)  # Convert percentage to 0-254
        
        # Set the light state for all selected lights
        for light_id in selected_lights:
            try:
                light = available_lights[light_id]['object']
                light.transitiontime = 1  # Quick transition
                light.hue = hue_value
                light.saturation = saturation_value
                light.brightness = brightness_value
            except Exception as e:
                logger.error(f"Error setting manual color for light {light_id}: {e}")
        
        logger.info(f"Manual color set: Hue={hue}, Brightness={brightness}%, Saturation={saturation}%")
        emit_state()


def set_brightness_range(min_value, max_value):
    """Set the brightness range for the light show."""
    global min_brightness, max_brightness
    
    min_brightness = max(0, min(100, min_value))
    max_brightness = max(min_brightness, min(100, max_value))
    
    logger.info(f"Brightness range set: {min_brightness}% - {max_brightness}%")
    emit_state()


def set_speed(transition_time_value, full_cycle_time_value):
    """Set the speed parameters for the light show."""
    global transition_time, full_cycle_time
    
    # Validate and set transition time (0.1 to 10 seconds)
    transition_time = max(0.1, min(10, transition_time_value))
    
    # Validate and set full cycle time (5 to 300 seconds)
    full_cycle_time = max(5, min(300, full_cycle_time_value))
    
    logger.info(f"Speed set: Transition time = {transition_time}s, Full cycle time = {full_cycle_time}s")
    emit_state()


# Flask routes
@app.route('/')
def index():
    """Render the main control page."""
    return render_template('index.html')


# SocketIO events
@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    logger.info("Client connected")
    emit_state()


@socketio.on('start')
def handle_start():
    """Handle start event."""
    start_light_show()
    return {'status': 'success'}


@socketio.on('stop')
def handle_stop():
    """Handle stop event."""
    stop_light_show()
    return {'status': 'success'}


@socketio.on('pause')
def handle_pause():
    """Handle pause event."""
    pause_light_show()
    return {'status': 'success'}


@socketio.on('set_color')
def handle_set_color(data):
    """Handle set color event."""
    hue = data.get('hue', 0)
    brightness = data.get('brightness', 100)
    saturation = data.get('saturation', 100)
    set_manual_color(hue, brightness, saturation)
    return {'status': 'success'}


@socketio.on('set_brightness_range')
def handle_set_brightness_range(data):
    """Handle set brightness range event."""
    min_value = data.get('min', DEFAULT_MIN_BRIGHTNESS)
    max_value = data.get('max', DEFAULT_MAX_BRIGHTNESS)
    set_brightness_range(min_value, max_value)
    return {'status': 'success'}


@socketio.on('set_selected_lights')
def handle_set_selected_lights(data):
    """Handle set selected lights event."""
    try:
        # Get the light IDs from the request
        light_ids = data.get('light_ids', [])
        
        # Log the raw data received
        logger.info(f"Received set_selected_lights request with data: {data}")
        logger.info(f"Light IDs received (type: {type(light_ids)}): {light_ids}")
        
        # Ensure light_ids is a list
        if not isinstance(light_ids, list):
            logger.error(f"Invalid light_ids format: expected list, got {type(light_ids)}")
            return {
                'status': 'error',
                'message': "Invalid format: light_ids must be an array"
            }
        
        # Convert string IDs to integers if needed
        processed_ids = []
        for id in light_ids:
            if isinstance(id, str) and id.isdigit():
                processed_ids.append(int(id))
            else:
                processed_ids.append(id)
        
        logger.info(f"Processed light IDs: {processed_ids}")
        
        # Apply the selection
        success = set_selected_lights(processed_ids)
        
        # Immediately emit the updated state to all clients
        emit_state()
        
        # Return appropriate response
        if success:
            return {
                'status': 'success',
                'message': f"Successfully updated light selection to {len(selected_lights)} lights",
                'selected_count': len(selected_lights)
            }
        else:
            if not light_ids:
                return {
                    'status': 'error',
                    'message': "No lights were selected",
                    'selected_count': len(selected_lights)
                }
            else:
                return {
                    'status': 'error',
                    'message': "No valid lights were found in your selection",
                    'selected_count': len(selected_lights)
                }
    except Exception as e:
        logger.error(f"Error in handle_set_selected_lights: {e}")
        return {
            'status': 'error',
            'message': f"Server error: {str(e)}",
            'selected_count': len(selected_lights)
        }


@socketio.on('set_speed')
def handle_set_speed(data):
    """Handle set speed event."""
    transition_time_value = data.get('transition_time', TRANSITION_TIME)
    full_cycle_time_value = data.get('full_cycle_time', FULL_CYCLE_TIME)
    set_speed(transition_time_value, full_cycle_time_value)
    return {'status': 'success'}


def main():
    """Main function to run the Hue light show with web interface."""
    global bridge
    
    try:
        # Step 1: Get bridge connection
        bridge = get_bridge_connection()
        
        # Step 2: Get all available lights
        get_all_lights(bridge)
        
        # Step 3: Start the web server
        logger.info("Starting web server on http://localhost:3000")
        socketio.run(app, host='0.0.0.0', port=3000, debug=False)
        
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        # Make sure to stop the light show thread
        if light_show_running:
            stop_light_show()


if __name__ == "__main__":
    main()