# HueLightShow

A dynamic color fading application for Philips Hue lights that creates stunning visual experiences by cycling through the entire color spectrum. This project includes both Node.js and Python implementations with an advanced web interface for complete control.

![HueLightShow Demo](https://via.placeholder.com/800x400?text=HueLightShow+Demo)

## Features

- Automatically discovers Hue Bridge on your network
- Handles authentication with your Hue Bridge
- Finds your light strip (or allows you to select specific lights)
- Creates a smooth color transition effect that cycles through all colors
- Brightness fades between user-defined minimum and maximum values
- Web interface for controlling the light show (Python version)
- Saves credentials for future use

## Web Interface Features

The Python implementation includes a feature-rich web interface that allows you to:

- Start, pause, and stop the light show from your browser
- Set minimum and maximum brightness levels (50-100% by default)
- Adjust transition speed and full cycle time
- Select which lights to include in the light show
- See real-time feedback of the current color and brightness
- When paused, manually select a specific color and brightness
- **Dark Mode**: Toggle between light and dark themes for comfortable viewing in any environment
- **Opacity Control**: Adjust the transparency of the interface against a black background

## Requirements

- Philips Hue Bridge connected to your network
- Philips Hue light strip or other color-capable Hue lights
- Either:
  - Node.js installed on your computer (for the Node.js version)
  - Python 3.6+ installed on your computer (for the Python version)

## Choose Your Implementation

This project provides two implementations of the same functionality:

1. **Node.js Implementation**: Uses the `node-hue-api` library
2. **Python Implementation**: Uses the `phue` library with a Flask/SocketIO web interface

Choose the one that best fits your environment and preferences.

## Node.js Implementation

### Installation

1. Navigate to the project directory
2. Install dependencies:
   ```
   npm install
   ```

### Usage

To start the light show with Node.js:

```
npm start
```

## Python Implementation

### Installation

1. Navigate to the project directory
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

### Usage

#### Basic Light Show

To start the basic light show with Python:

```
python hue_light_show.py
```

#### Web Interface Version

To start the light show with web interface control:

```
python hue_web_controller.py
```

Then open your browser and navigate to:
```
http://localhost:3000
```

### Accessing from Other Devices

To access the web interface from other devices on your network:

1. Find your computer's IP address:
   - On Windows: Open Command Prompt and type `ipconfig`
   - On macOS/Linux: Open Terminal and type `ifconfig` or `ip addr`

2. Use that IP address instead of localhost:
   ```
   http://YOUR_IP_ADDRESS:3000
   ```
   For example: `http://192.168.1.100:3000`

The web interface is designed to work from any device on your network, including smartphones and tablets.

## Web Interface Guide

### Main Controls
- **Start/Resume**: Begin the light show or resume if paused
- **Pause**: Pause the light show (enables manual color control)
- **Stop**: Stop the light show completely

### Brightness Range
- Set the minimum and maximum brightness levels (50-100% by default)
- The brightness will smoothly transition between these values

### Speed Settings
- **Transition Time**: How long each color transition takes (lower = faster transitions)
- **Full Cycle Time**: Time to complete a full color cycle (lower = faster overall speed)

### Light Selection
- Choose which lights to include in the light show
- Apply your selection with the "Apply Selection" button

### Manual Color Control
- Available when the light show is paused
- Adjust Hue (0-360°), Brightness (0-100%), and Saturation (0-100%)
- Apply your color with the "Apply Color" button

### Interface Customization
- **Dark Mode**: Toggle between light and dark themes using the moon/sun icon in the top-right corner
- **Opacity Control**: Adjust the transparency of the interface using the slider in the bottom-right corner

## How It Works

On first run, the application will:
1. Ask for your Hue Bridge IP address (Python version) or discover it automatically (Node.js version)
2. Prompt you to press the link button on your Hue Bridge
3. Save the connection details for future use
4. Find your light strip or list available lights
5. Start the color fading effect

To stop the light show, press `Ctrl+C` in your terminal or use the Stop button in the web interface.

## Getting Your Hue Bridge Username

The Hue Bridge requires a username (authentication token) for API access. Both implementations will automatically generate this for you when you run them for the first time.

However, if you want to get the username separately or have issues with the automatic process, you can use the included helper script:

```
python get_hue_username.py
```

This script will:
1. Ask for your Hue Bridge IP address
2. Prompt you to press the link button on your Hue Bridge
3. Generate a username and save it to `hue-config.json`

The script doesn't require any external dependencies, so you can run it even if you haven't installed the requirements yet.

### Finding Your Hue Bridge IP Address

To find your Hue Bridge IP address:
1. Open the Philips Hue app on your smartphone
2. Go to Settings > Hue Bridges
3. Tap the information (i) icon next to your bridge
4. Note the IP address shown (e.g., 192.168.1.100)

Alternatively, you can check your router's connected devices list.

## Configuration

### Code Configuration

You can modify the following settings in the source code:

- `TRANSITION_TIME`: Time in seconds for each color transition (default: 2)
- `FULL_CYCLE_TIME`: Time in seconds for a full color cycle (default: 30)

#### Brightness Settings

- **Node.js version**: Fixed at 100% brightness
  - To adjust: Change the `brightness` value (lines 115 and 136) to a number between 1-100

- **Python basic version**: Fixed at 100% brightness
  - To adjust: Change the `brightness` value (line 121) to a number between 1-254

- **Python web version**: Variable brightness that fades between min and max values
  - Default range: 50-100% brightness
  - Adjustable through the web interface

### Web Interface Configuration

The web interface allows you to configure the following settings in real-time:

- **Brightness Range**: Set minimum and maximum brightness levels (50-100% by default)
- **Speed Settings**: Adjust transition time and full cycle time
- **Light Selection**: Choose which lights to include in the light show
- **Manual Color Control**: When paused, you can select:
  - Hue (0-360°)
  - Brightness (0-100%)
  - Saturation (0-100%)
- **Interface Preferences**: 
  - Dark/Light mode (saved between sessions)
  - Interface opacity (saved between sessions)

## Troubleshooting

- **No Hue Bridge found/connection issues**:
  - Make sure your Hue Bridge is connected to the same network as your computer
  - For the Python version, you may need to manually enter the IP address of your Hue Bridge
  - You can find your bridge IP in the Hue app under Settings > Hue Bridges > i (information icon)

- **Link button not pressed**:
  - You need to press the physical link button on your Hue Bridge when prompted
  - The button is located on top of the Hue Bridge

- **No light strip found**:
  - The application will list all available lights and allow you to select one
  - If no selection is made, it will use the first light

- **Python-specific issues**:
  - If you get an error about the `phue` module not being found, make sure you've installed the requirements with `pip install -r requirements.txt`
  - You may need to use `python3` instead of `python` depending on your system

- **Web interface issues**:
  - If you get an error about Flask or SocketIO not being found, make sure you've installed the requirements with `pip install -r requirements.txt`
  - If the web interface doesn't load, make sure you're accessing http://localhost:3000 in your browser
  - If you can't connect to the web interface from another device:
    - Make sure you're using your computer's IP address instead of localhost (e.g., http://192.168.1.100:3000)
    - Check that your computer's firewall isn't blocking port 3000
    - Ensure both devices are on the same network
  - If the interface loads but doesn't update in real-time, check that your browser supports WebSockets

- **Node.js-specific issues**:
  - If you get an error about modules not being found, make sure you've run `npm install`

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.