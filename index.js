const v3 = require('node-hue-api').v3;
const hueApi = v3.api;
const discovery = v3.discovery;
const fs = require('fs');
const path = require('path');

// Configuration
const CONFIG_FILE = path.join(__dirname, 'hue-config.json');
const APP_NAME = 'hue-light-show';
const DEVICE_NAME = 'node-hue-api';
const TRANSITION_TIME = 2; // Time in seconds for each color transition
const FULL_CYCLE_TIME = 30; // Time in seconds for a full color cycle

// Main function
async function main() {
  try {
    // Step 1: Get bridge connection
    const bridge = await getBridgeConnection();
    
    // Step 2: Find the light strip
    const lightStrip = await findLightStrip(bridge);
    if (!lightStrip) {
      console.error('No light strip found. Please make sure your Hue light strip is connected and try again.');
      return;
    }
    
    console.log(`Found light strip: ${lightStrip.name} (ID: ${lightStrip.id})`);
    
    // Step 3: Start the color fading effect
    await startColorFade(bridge, lightStrip.id);
    
  } catch (error) {
    console.error('Error:', error.message);
  }
}

// Function to get bridge connection
async function getBridgeConnection() {
  // Check if we have saved credentials
  if (fs.existsSync(CONFIG_FILE)) {
    const config = JSON.parse(fs.readFileSync(CONFIG_FILE, 'utf8'));
    console.log(`Using saved connection to bridge at ${config.ipAddress}`);
    return hueApi.createLocal(config.ipAddress).connect(config.username);
  }
  
  // No saved credentials, need to discover and authenticate
  console.log('Searching for Hue Bridges on your network...');
  const bridges = await discovery.nupnpSearch();
  
  if (bridges.length === 0) {
    throw new Error('No Hue Bridges found. Please make sure your Hue Bridge is connected to your network.');
  }
  
  const bridge = bridges[0];
  console.log(`Found Hue Bridge at ${bridge.ipaddress}`);
  
  // Create a new user
  console.log('Please press the link button on your Hue Bridge within the next 30 seconds...');
  
  try {
    const unauthenticatedApi = await hueApi.createLocal(bridge.ipaddress).connect();
    const createdUser = await unauthenticatedApi.users.createUser(APP_NAME, DEVICE_NAME);
    
    // Save the config for future use
    const config = {
      ipAddress: bridge.ipaddress,
      username: createdUser.username
    };
    
    fs.writeFileSync(CONFIG_FILE, JSON.stringify(config, null, 2));
    console.log('Successfully connected to Hue Bridge and saved credentials.');
    
    return hueApi.createLocal(bridge.ipaddress).connect(createdUser.username);
  } catch (error) {
    if (error.getHueErrorType() === 101) {
      throw new Error('Link button not pressed. Please try again and make sure to press the link button on your Hue Bridge.');
    } else {
      throw error;
    }
  }
}

// Function to find the light strip
async function findLightStrip(bridge) {
  const lights = await bridge.lights.getAll();
  
  // Try to find a light strip (usually has "strip" in the name)
  let lightStrip = lights.find(light => 
    light.name.toLowerCase().includes('strip') || 
    light.name.toLowerCase().includes('lightstrip')
  );
  
  // If no specific light strip found, ask the user which light to use
  if (!lightStrip) {
    console.log('Available lights:');
    lights.forEach((light, index) => {
      console.log(`${index + 1}: ${light.name} (ID: ${light.id})`);
    });
    
    // For now, just use the first light if no specific strip is found
    if (lights.length > 0) {
      console.log(`No light strip specifically identified. Using the first light: ${lights[0].name}`);
      return lights[0];
    }
  }
  
  return lightStrip;
}

// Function to start the color fading effect
async function startColorFade(bridge, lightId) {
  console.log('Starting color fade effect. Press Ctrl+C to stop.');
  
  // First, make sure the light is on with 100% brightness
  await bridge.lights.setLightState(lightId, { on: true, brightness: 100 }); // 100 = 100% brightness
  
  // Calculate how many steps we need for a smooth transition
  const totalSteps = 360; // Using hue values from 0-360 (HSL color model)
  const stepTime = (FULL_CYCLE_TIME * 1000) / totalSteps;
  
  let currentStep = 0;
  
  // Start the color cycle
  const interval = setInterval(async () => {
    try {
      // Calculate the current hue value (0-360)
      const hue = currentStep % 360;
      
      // Convert hue (0-360) to the Philips Hue format (0-65535)
      const hueValue = Math.floor((hue / 360) * 65535);
      
      // Set the light state with the new color
      await bridge.lights.setLightState(lightId, {
        hue: hueValue,
        saturation: 100, // 100 = 100% saturation for vibrant colors
        brightness: 100, // 100 = 100% brightness
        transitiontime: Math.floor(TRANSITION_TIME * 10) // Philips Hue uses 1/10 of a second as the unit
      });
      
      // Increment the step
      currentStep = (currentStep + 1) % 360;
      
    } catch (error) {
      console.error('Error updating light:', error.message);
    }
  }, stepTime);
  
  // Handle program termination
  process.on('SIGINT', async () => {
    clearInterval(interval);
    console.log('Color fade stopped. Turning off the light...');
    
    try {
      // Optional: Turn off the light when the program ends
      // await bridge.lights.setLightState(lightId, { on: false });
      console.log('Light state preserved. Exiting...');
    } catch (error) {
      console.error('Error turning off light:', error.message);
    }
    
    process.exit(0);
  });
}

// Run the main function
main().catch(error => {
  console.error('Unhandled error:', error);
});