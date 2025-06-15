# 🏠 Smart Study Room IoT System

A comprehensive IoT application that monitors and optimizes study room conditions using multiple sensors and intelligent actuators. The system provides real-time monitoring, automatic environmental control, and study session tracking.

## 📋 Features

### 🔍 Sensors
- **Temperature Sensor**: Monitors room temperature with day/night patterns
- **Humidity Sensor**: Tracks moisture levels for comfort
- **Light Sensor**: Measures ambient light with realistic daily variations
- **Noise Sensor**: Detects sound levels with occasional spike simulation
- **Motion Sensor**: Tracks presence for study session monitoring

### ⚙️ Actuators
- **Smart Light Control**: Automatically adjusts lighting based on ambient conditions and motion
- **Climate Control**: Simulates HVAC system for temperature/humidity management
- **Focus Mode**: Monitors study conditions and sends break reminders
- **Notification System**: Consolidated alerts for environmental issues

### 🌐 Architecture
- **Multi-tier IoT Architecture**: Sensors → Gateway → Cloud/Dashboard
- **MQTT Protocol**: Lightweight messaging for IoT communication
- **Real-time WebSocket**: Live dashboard updates
- **Edge Computing**: Local processing for immediate responses
- **Concurrent Processing**: Each component runs in separate threads/processes

## 🚀 Quick Start

### Prerequisites
- Python 3.7+
- Mosquitto MQTT Broker
- Web browser (Chrome, Firefox, Safari, Edge)

### Installation

1. **Clone or download all project files** into a single directory:
   ```
   smart-study-room/
   ├── sensor.py
   ├── actuator.py
   ├── gateway.py
   ├── visualize.py
   ├── start.py
   ├── templates/
   │   └── dashboard.html
   └── README.md
   ```

2. **Install required Python packages**:
   ```bash
   pip install paho-mqtt flask flask-socketio flask-cors matplotlib numpy
   ```

3. **Install Mosquitto MQTT Broker**:
   - **Ubuntu/Debian**: `sudo apt-get install mosquitto`
   - **macOS**: `brew install mosquitto`
   - **Windows**: Download from [mosquitto.org](https://mosquitto.org/download/)

### Running the System

1. **Start everything with one command**:
   ```bash
   python start.py
   ```

2. **Access the dashboard**:
   - Open your browser and go to: `http://localhost:5000`

3. **Optional: Start individual components** (for development/testing):
   ```bash
   # Start MQTT broker first
   mosquitto

   # In separate terminals:
   python sensor.py      # Start sensors
   python actuator.py    # Start actuators
   python gateway.py     # Start gateway and web server
   python visualize.py   # Optional: Real-time matplotlib charts
   ```

## 📊 Dashboard Features

### Real-time Monitoring
- Live sensor data updates every 2 seconds
- Color-coded status indicators
- Historical trend charts using Chart.js
- Comfort zone visualization

### Control Panel
- Manual light control with auto-mode toggle
- Climate control modes (Cool/Heat/Auto)
- Real-time notifications and alerts
- Study session tracking

### Analytics
- Comfort score calculation
- Environmental trend analysis
- Smart recommendations
- Energy usage insights

## 🏗️ System Architecture

```
┌─────────────┐     MQTT      ┌─────────────┐     WebSocket    ┌─────────────┐
│   Sensors   │ ──────────►   │   Gateway   │ ◄────────────►   │  Dashboard  │
└─────────────┘                └─────────────┘                   └─────────────┘
                                      │
                                      │ MQTT
                                      ▼
                               ┌─────────────┐
                               │  Actuators  │
                               └─────────────┘
```

### Data Flow
1. **Sensors** publish data to MQTT topics
2. **Gateway** subscribes to all topics and processes data
3. **Actuators** subscribe to sensor data and commands
4. **Dashboard** receives real-time updates via WebSocket

### MQTT Topics
- `smartroom/sensors/{type}` - Sensor data
- `smartroom/actuators/{type}` - Actuator states
- `smartroom/commands/{type}` - Control commands
- `smartroom/actuators/notifications` - System notifications

## 🎯 Key Features Explained

### Automatic Light Control
The smart light system adjusts brightness based on:
- Current ambient light levels
- Motion detection
- Time of day
- Manual override options

### Climate Management
Maintains optimal temperature and humidity:
- Target temperature: 22°C (adjustable)
- Comfort range: 20-24°C
- Automatic heating/cooling decisions
- Humidity alerts

### Focus Mode & Study Tracking
Enhances productivity:
- Noise level monitoring
- Study session detection
- 45-minute break reminders
- Session duration tracking

### Multi-Component Feedback Loops
1. **Light-Motion Loop**: Presence triggers lighting adjustments
2. **Temperature-Climate Loop**: Temperature changes trigger HVAC
3. **Noise-Focus Loop**: High noise triggers focus mode alerts
4. **Comfort-Notification Loop**: Multiple issues trigger consolidated alerts

## 🛠️ Customization

### Modify Sensor Behavior
Edit `sensor.py` to adjust:
- Data generation patterns
- Update frequencies
- Value ranges
- Noise/variation levels

### Adjust Actuator Logic
Edit `actuator.py` to change:
- Threshold values
- Response behaviors
- Notification messages
- Control algorithms

### Customize Dashboard
Edit `templates/dashboard.html` to:
- Change visual themes
- Add new widgets
- Modify chart types
- Adjust layouts

### Change MQTT Broker
To use a public broker, edit all Python files:
```python
MQTT_BROKER = "test.mosquitto.org"  # Instead of "localhost"
```

## 📈 Visualizer Modes

### Real-time Mode (Default)
```bash
python visualize.py realtime
```
- Live sensor data plots
- Comfort zone indicators
- Keyboard shortcuts:
  - `S`: Save snapshot
  - `R`: Generate report
  - `Q`: Quit

### Advanced Analytics Mode
```bash
python visualize.py advanced
```
- Temperature heatmap
- Comfort score gauge
- Energy distribution
- Activity timeline

## 🔧 Troubleshooting

### MQTT Connection Failed
- Ensure Mosquitto is running: `mosquitto`
- Check if port 1883 is available
- Try using a public broker

### Dashboard Not Loading
- Verify gateway is running
- Check port 5000 is free
- Try accessing `http://127.0.0.1:5000`

### No Sensor Data
- Confirm all components started successfully
- Check MQTT broker is accessible
- Verify no firewall blocking

## 📚 Educational Value

This project demonstrates:
- **IoT Architecture**: Multi-tier design with edge computing
- **Concurrent Programming**: Threading and process management
- **Protocol Implementation**: MQTT pub/sub pattern
- **Real-time Systems**: WebSocket for live updates
- **Data Visualization**: Multiple visualization techniques
- **System Integration**: Multiple components working together

## 🚦 Project Structure

- **sensor.py**: Simulates IoT sensors with realistic data patterns
- **actuator.py**: Implements intelligent actuators with feedback loops
- **gateway.py**: Central hub with MQTT broker, web server, and analytics
- **visualize.py**: Matplotlib-based real-time data visualization
- **start.py**: Automated startup script for the entire system
- **templates/dashboard.html**: Interactive web dashboard

## 🎓 Learning Extensions

1. **Add New Sensors**: CO2, pressure, or presence sensors
2. **Implement ML**: Predict optimal conditions based on patterns
3. **Mobile App**: Create a React Native companion app
4. **Voice Control**: Integrate with Alexa/Google Home
5. **Data Persistence**: Add database for historical data
6. **Security**: Implement MQTT authentication and SSL

## 📄 License

This project is created for educational purposes. Feel free to modify and extend it for your learning needs.