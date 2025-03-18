// Connect to the Socket.IO server
// This will work with any host, including external connections
const socket = io(window.location.origin);

// DOM Elements
const colorPreview = document.getElementById('colorPreview');
const statusValue = document.getElementById('statusValue');
const currentColor = document.getElementById('currentColor');
const currentBrightness = document.getElementById('currentBrightness');

const startBtn = document.getElementById('startBtn');
const pauseBtn = document.getElementById('pauseBtn');
const stopBtn = document.getElementById('stopBtn');

const minBrightness = document.getElementById('minBrightness');
const maxBrightness = document.getElementById('maxBrightness');
const minBrightnessValue = document.getElementById('minBrightnessValue');
const maxBrightnessValue = document.getElementById('maxBrightnessValue');
const applyRangeBtn = document.getElementById('applyRangeBtn');

const transitionTime = document.getElementById('transitionTime');
const fullCycleTime = document.getElementById('fullCycleTime');
const transitionTimeValue = document.getElementById('transitionTimeValue');
const fullCycleTimeValue = document.getElementById('fullCycleTimeValue');
const applySpeedBtn = document.getElementById('applySpeedBtn');

const hueSlider = document.getElementById('hueSlider');
const brightnessSlider = document.getElementById('brightnessSlider');
const saturationSlider = document.getElementById('saturationSlider');
const hueValue = document.getElementById('hueValue');
const brightnessValue = document.getElementById('brightnessValue');
const saturationValue = document.getElementById('saturationValue');
const applyColorBtn = document.getElementById('applyColorBtn');
const manualControlPanel = document.getElementById('manualControlPanel');

const lightsContainer = document.getElementById('lightsContainer');
const applyLightsBtn = document.getElementById('applyLightsBtn');

const themeOptions = document.getElementById('themeOptions');
const applyThemeBtn = document.getElementById('applyThemeBtn');

// State variables
let isRunning = false;
let isPaused = false;
let availableLights = {};
let selectedLights = [];
let selectedTheme = 'rainbow'; // Default theme

// Event Listeners
startBtn.addEventListener('click', () => {
    if (!isRunning) {
        socket.emit('start');
    } else if (isPaused) {
        socket.emit('start'); // Resume if paused
    }
});

pauseBtn.addEventListener('click', () => {
    if (isRunning && !isPaused) {
        socket.emit('pause');
    }
});

stopBtn.addEventListener('click', () => {
    if (isRunning) {
        socket.emit('stop');
    }
});

applyRangeBtn.addEventListener('click', () => {
    const minValue = parseInt(minBrightness.value);
    const maxValue = parseInt(maxBrightness.value);
    
    if (minValue > maxValue) {
        alert('Minimum brightness cannot be greater than maximum brightness');
        return;
    }
    
    socket.emit('set_brightness_range', {
        min: minValue,
        max: maxValue
    });
});

applySpeedBtn.addEventListener('click', () => {
    const transitionTimeValue = parseFloat(transitionTime.value);
    const fullCycleTimeValue = parseFloat(fullCycleTime.value);
    
    socket.emit('set_speed', {
        transition_time: transitionTimeValue,
        full_cycle_time: fullCycleTimeValue
    });
});

// Theme selection
themeOptions.addEventListener('click', (event) => {
    // Find the clicked theme option or its parent
    const themeOption = event.target.closest('.theme-option');
    if (!themeOption) return;
    
    // Remove selected class from all options
    document.querySelectorAll('.theme-option').forEach(option => {
        option.classList.remove('selected');
    });
    
    // Add selected class to clicked option
    themeOption.classList.add('selected');
    
    // Store the selected theme
    selectedTheme = themeOption.dataset.theme;
    
    console.log(`Selected theme: ${selectedTheme}`);
});

applyThemeBtn.addEventListener('click', () => {
    // Find the selected theme option
    const selectedOption = document.querySelector('.theme-option.selected') ||
                          document.querySelector('.theme-option[data-theme="rainbow"]');
    
    // Get the hue range from the selected theme
    const hueStart = parseInt(selectedOption.dataset.hueStart);
    const hueEnd = parseInt(selectedOption.dataset.hueEnd);
    
    console.log(`Applying theme: ${selectedOption.dataset.theme} (${hueStart}° - ${hueEnd}°)`);
    
    // Send the theme to the server
    socket.emit('set_theme', {
        theme: selectedOption.dataset.theme,
        hue_start: hueStart,
        hue_end: hueEnd
    });
});

applyColorBtn.addEventListener('click', () => {
    if (isRunning && isPaused) {
        socket.emit('set_color', {
            hue: parseInt(hueSlider.value),
            brightness: parseInt(brightnessSlider.value),
            saturation: parseInt(saturationSlider.value)
        });
    }
});

applyLightsBtn.addEventListener('click', () => {
    // Show a loading state
    const originalText = applyLightsBtn.textContent;
    applyLightsBtn.textContent = "Applying...";
    applyLightsBtn.disabled = true;
    
    // Determine if the light IDs are integers or strings based on available lights
    let useIntegerIds = false;
    if (Object.keys(availableLights).length > 0) {
        const sampleKey = Object.keys(availableLights)[0];
        useIntegerIds = !isNaN(parseInt(sampleKey)) && sampleKey === parseInt(sampleKey).toString();
        console.log(`Using ${useIntegerIds ? 'integer' : 'string'} IDs for server communication`);
    }
    
    // Process the selected lights to ensure they're in the correct format
    const processedLightIds = selectedLights.map(id => {
        if (useIntegerIds && typeof id === 'string' && !isNaN(parseInt(id))) {
            return parseInt(id);
        } else if (!useIntegerIds && typeof id !== 'string') {
            return String(id);
        }
        return id;
    });
    
    // Log the selection being sent
    console.log("Sending selected lights to server:", processedLightIds);
    
    socket.emit('set_selected_lights', {
        light_ids: processedLightIds
    }, (response) => {
        // Handle the response from the server
        console.log("Server response:", response);
        
        if (response.status === 'success') {
            // Show success message
            applyLightsBtn.textContent = "✓ Applied";
            applyLightsBtn.classList.add('success');
            
            // Reset button after a delay
            setTimeout(() => {
                applyLightsBtn.textContent = `Apply Selection (${selectedLights.length})`;
                applyLightsBtn.classList.remove('success');
                applyLightsBtn.disabled = false;
            }, 2000);
        } else {
            // Show error message
            applyLightsBtn.textContent = "Error: " + (response.message || "Failed to apply");
            applyLightsBtn.classList.add('error');
            
            // Reset button after a delay
            setTimeout(() => {
                applyLightsBtn.textContent = `Apply Selection (${selectedLights.length})`;
                applyLightsBtn.classList.remove('error');
                applyLightsBtn.disabled = false;
            }, 3000);
        }
    });
});

// Update sliders display values
minBrightness.addEventListener('input', () => {
    minBrightnessValue.textContent = `${minBrightness.value}%`;
});

maxBrightness.addEventListener('input', () => {
    maxBrightnessValue.textContent = `${maxBrightness.value}%`;
});

transitionTime.addEventListener('input', () => {
    transitionTimeValue.textContent = `${transitionTime.value}s`;
});

fullCycleTime.addEventListener('input', () => {
    fullCycleTimeValue.textContent = `${fullCycleTime.value}s`;
});

hueSlider.addEventListener('input', updateColorPreview);
brightnessSlider.addEventListener('input', updateColorPreview);
saturationSlider.addEventListener('input', updateColorPreview);

// Function to update the color preview based on slider values
function updateColorPreview() {
    hueValue.textContent = `${hueSlider.value}°`;
    brightnessValue.textContent = `${brightnessSlider.value}%`;
    saturationValue.textContent = `${saturationSlider.value}%`;
    
    // Update the manual color preview
    const hue = parseInt(hueSlider.value);
    const brightness = parseInt(brightnessSlider.value);
    const saturation = parseInt(saturationSlider.value);
    
    const color = hslToHex(hue, saturation, brightness);
    colorPreview.style.backgroundColor = color;
}

// Socket.IO event handlers
socket.on('connect', () => {
    console.log('Connected to server');
});

socket.on('state_update', (state) => {
    isRunning = state.running;
    isPaused = state.paused;
    
    // Update UI based on state
    updateStatusUI(state);
    updateControlButtons();
    updateManualControls();
    
    // Update lights information
    if (state.lights) {
        console.log("Received state update with lights:", state.lights);
        console.log("Selected lights from server:", state.selected_lights);
        
        // Determine if the light IDs are integers or strings
        let useIntegerIds = false;
        if (Object.keys(state.lights).length > 0) {
            const sampleKey = Object.keys(state.lights)[0];
            useIntegerIds = !isNaN(parseInt(sampleKey)) && sampleKey === parseInt(sampleKey).toString();
            console.log(`Light IDs from server appear to be ${useIntegerIds ? 'integers' : 'strings'}`);
        }
        
        availableLights = state.lights;
        
        // Make sure we have an array of selected lights
        if (Array.isArray(state.selected_lights)) {
            // Process the IDs based on the determined type
            selectedLights = state.selected_lights.map(id => {
                if (useIntegerIds && typeof id === 'string' && !isNaN(parseInt(id))) {
                    return parseInt(id);
                } else if (!useIntegerIds && typeof id !== 'string') {
                    return String(id);
                }
                return id;
            });
        } else {
            selectedLights = [];
        }
        
        console.log("Updated selected lights:", selectedLights);
        
        // Update the UI
        renderLights();
        
        // Update the Apply button text to show count
        if (!applyLightsBtn.disabled) {
            applyLightsBtn.textContent = `Apply Selection (${selectedLights.length})`;
        }
    }
    
    // Update sliders with current values
    if (!isDragging) {
        minBrightness.value = state.min_brightness;
        maxBrightness.value = state.max_brightness;
        minBrightnessValue.textContent = `${state.min_brightness}%`;
        maxBrightnessValue.textContent = `${state.max_brightness}%`;
        
        // Update speed sliders if available
        if (state.transition_time !== undefined) {
            transitionTime.value = state.transition_time;
            transitionTimeValue.textContent = `${state.transition_time}s`;
        }
        
        if (state.full_cycle_time !== undefined) {
            fullCycleTime.value = state.full_cycle_time;
            fullCycleTimeValue.textContent = `${state.full_cycle_time}s`;
        }
        
        hueSlider.value = state.hue;
        brightnessSlider.value = state.brightness;
        saturationSlider.value = state.saturation;
        hueValue.textContent = `${state.hue}°`;
        brightnessValue.textContent = `${state.brightness}%`;
        saturationValue.textContent = `${state.saturation}%`;
    }
    
    // Update theme selection if available
    if (state.theme) {
        // Find the theme option with the matching theme name
        const themeOption = document.querySelector(`.theme-option[data-theme="${state.theme}"]`);
        if (themeOption) {
            // Remove selected class from all options
            document.querySelectorAll('.theme-option').forEach(option => {
                option.classList.remove('selected');
            });
            
            // Add selected class to the matching option
            themeOption.classList.add('selected');
            selectedTheme = state.theme;
        }
    }
});

// Track if user is dragging sliders
let isDragging = false;
const sliders = [minBrightness, maxBrightness, transitionTime, fullCycleTime, hueSlider, brightnessSlider, saturationSlider];

sliders.forEach(slider => {
    slider.addEventListener('mousedown', () => {
        isDragging = true;
    });
    
    slider.addEventListener('touchstart', () => {
        isDragging = true;
    });
});

document.addEventListener('mouseup', () => {
    isDragging = false;
});

document.addEventListener('touchend', () => {
    isDragging = false;
});

// Helper Functions
function updateStatusUI(state) {
    // Update status text
    if (!state.running) {
        statusValue.textContent = 'Stopped';
    } else if (state.paused) {
        statusValue.textContent = 'Paused';
    } else {
        statusValue.textContent = 'Running';
    }
    
    // Update color preview
    colorPreview.style.backgroundColor = state.color;
    
    // Update color and brightness text
    currentColor.textContent = state.color;
    currentBrightness.textContent = `${Math.round(state.brightness)}%`;
}

function updateControlButtons() {
    if (isRunning) {
        startBtn.textContent = isPaused ? 'Resume' : 'Start';
        startBtn.disabled = !isPaused;
        pauseBtn.disabled = isPaused;
        stopBtn.disabled = false;
    } else {
        startBtn.textContent = 'Start';
        startBtn.disabled = false;
        pauseBtn.disabled = true;
        stopBtn.disabled = true;
    }
}

function updateManualControls() {
    const isManualMode = isRunning && isPaused;
    
    hueSlider.disabled = !isManualMode;
    brightnessSlider.disabled = !isManualMode;
    saturationSlider.disabled = !isManualMode;
    applyColorBtn.disabled = !isManualMode;
    
    if (isManualMode) {
        manualControlPanel.classList.add('active');
    } else {
        manualControlPanel.classList.remove('active');
    }
}

// Convert HSL to Hex color
function hslToHex(h, s, l) {
    h /= 360;
    s /= 100;
    l /= 100;
    
    let r, g, b;
    
    if (s === 0) {
        r = g = b = l;
    } else {
        const hue2rgb = (p, q, t) => {
            if (t < 0) t += 1;
            if (t > 1) t -= 1;
            if (t < 1/6) return p + (q - p) * 6 * t;
            if (t < 1/2) return q;
            if (t < 2/3) return p + (q - p) * (2/3 - t) * 6;
            return p;
        };
        
        const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
        const p = 2 * l - q;
        
        r = hue2rgb(p, q, h + 1/3);
        g = hue2rgb(p, q, h);
        b = hue2rgb(p, q, h - 1/3);
    }
    
    const toHex = x => {
        const hex = Math.round(x * 255).toString(16);
        return hex.length === 1 ? '0' + hex : hex;
    };
    
    return `#${toHex(r)}${toHex(g)}${toHex(b)}`;
}

// Function to render the available lights
function renderLights() {
    // Clear the container
    lightsContainer.innerHTML = '';
    
    // If no lights available, show a message
    if (Object.keys(availableLights).length === 0) {
        lightsContainer.innerHTML = '<div class="loading-lights">No lights found</div>';
        return;
    }
    
    // Debug log
    console.log("Available lights:", availableLights);
    console.log("Selected lights:", selectedLights);
    
    // Determine if the light IDs are integers or strings
    // This helps us maintain consistency with the server
    let useIntegerIds = false;
    if (Object.keys(availableLights).length > 0) {
        const sampleKey = Object.keys(availableLights)[0];
        useIntegerIds = !isNaN(parseInt(sampleKey)) && sampleKey === parseInt(sampleKey).toString();
        console.log(`Light IDs appear to be ${useIntegerIds ? 'integers' : 'strings'}`);
    }
    
    // Create a light item for each available light
    Object.entries(availableLights).forEach(([lightId, lightData]) => {
        // Process the lightId based on the determined type
        const processedLightId = useIntegerIds && !isNaN(parseInt(lightId)) ?
            parseInt(lightId) : lightId;
        
        // For UI display and comparison, always use string
        const lightIdStr = String(lightId);
        
        // Check if this light is in the selected lights array
        const isSelected = selectedLights.some(id =>
            String(id) === lightIdStr ||
            (useIntegerIds && parseInt(id) === parseInt(lightIdStr))
        );
        
        const lightItem = document.createElement('div');
        lightItem.className = `light-item ${isSelected ? 'selected' : ''}`;
        lightItem.dataset.lightId = lightIdStr;
        
        lightItem.innerHTML = `
            <input type="checkbox" class="light-checkbox" ${isSelected ? 'checked' : ''}>
            <div class="light-info">
                <div class="light-name">${lightData.name}</div>
                <div class="light-type">${lightData.type}</div>
            </div>
        `;
        
        // Add click event to toggle selection
        lightItem.addEventListener('click', () => {
            const checkbox = lightItem.querySelector('.light-checkbox');
            checkbox.checked = !checkbox.checked;
            
            if (checkbox.checked) {
                // Add to selected lights if not already included
                const alreadySelected = selectedLights.some(id =>
                    String(id) === lightIdStr ||
                    (useIntegerIds && parseInt(id) === parseInt(lightIdStr))
                );
                
                if (!alreadySelected) {
                    // Add the ID in the correct format (int or string)
                    selectedLights.push(processedLightId);
                    console.log(`Added light ${processedLightId} (${typeof processedLightId}) to selection`);
                }
                lightItem.classList.add('selected');
            } else {
                // Remove from selected lights
                const index = selectedLights.findIndex(id =>
                    String(id) === lightIdStr ||
                    (useIntegerIds && parseInt(id) === parseInt(lightIdStr))
                );
                
                if (index !== -1) {
                    selectedLights.splice(index, 1);
                    console.log(`Removed light ${lightIdStr} from selection`);
                }
                lightItem.classList.remove('selected');
            }
            
            // Debug log the current selection
            console.log("Current selection:", selectedLights);
            
            // Update the Apply button text to show count
            if (!applyLightsBtn.disabled) {
                applyLightsBtn.textContent = `Apply Selection (${selectedLights.length})`;
            }
        });
        
        lightsContainer.appendChild(lightItem);
    });
    
    // Update the Apply button text to show count
    applyLightsBtn.textContent = `Apply Selection (${selectedLights.length})`;
}

// Theme toggle functionality
const themeToggle = document.getElementById('themeToggle');
const themeIcon = themeToggle.querySelector('i');

// Check for saved theme preference or use preferred color scheme
const savedTheme = localStorage.getItem('theme');
const prefersDarkScheme = window.matchMedia('(prefers-color-scheme: dark)').matches;

// Apply the saved theme or use system preference
if (savedTheme === 'dark' || (!savedTheme && prefersDarkScheme)) {
    document.body.classList.add('dark-mode');
    themeIcon.classList.remove('fa-moon');
    themeIcon.classList.add('fa-sun');
}

// Toggle theme when the button is clicked
themeToggle.addEventListener('click', () => {
    // Toggle dark mode class on body
    document.body.classList.toggle('dark-mode');
    
    // Update the icon
    if (document.body.classList.contains('dark-mode')) {
        themeIcon.classList.remove('fa-moon');
        themeIcon.classList.add('fa-sun');
        localStorage.setItem('theme', 'dark');
    } else {
        themeIcon.classList.remove('fa-sun');
        themeIcon.classList.add('fa-moon');
        localStorage.setItem('theme', 'light');
    }
});

// Opacity control functionality
const opacitySlider = document.getElementById('opacitySlider');
const opacityValue = document.getElementById('opacityValue');

// Check for saved opacity preference
const savedOpacity = localStorage.getItem('opacity');
if (savedOpacity) {
    // Set the slider value
    opacitySlider.value = savedOpacity;
    
    // Update the CSS variable
    document.documentElement.style.setProperty('--app-opacity', savedOpacity / 100);
    
    // Update the display value
    opacityValue.textContent = `${savedOpacity}%`;
}

// Handle opacity slider changes
opacitySlider.addEventListener('input', () => {
    const value = opacitySlider.value;
    
    // Update the CSS variable
    document.documentElement.style.setProperty('--app-opacity', value / 100);
    
    // Update the display value
    opacityValue.textContent = `${value}%`;
    
    // Save the preference
    localStorage.setItem('opacity', value);
});

// Initialize UI
updateColorPreview();