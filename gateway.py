import json
import threading
import time
from datetime import datetime
from collections import defaultdict, deque
import paho.mqtt.client as mqtt
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS

# Configuration
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
WEB_PORT = 5000

# Flask app setup
app = Flask(__name__)
app.config['SECRET_KEY'] = 'smart-study-room-secret'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

class IoTGateway:
    """Central gateway for IoT data processing and routing"""
    def __init__(self):
        self.mqtt_client = mqtt.Client("gateway_main")
        self.sensor_data = defaultdict(dict)
        self.actuator_states = defaultdict(dict)
        self.data_history = defaultdict(lambda: deque(maxlen=100))
        self.notifications = deque(maxlen=50)
        self.running = False
        
        # Analytics
        self.study_sessions = []
        self.comfort_violations = defaultdict(int)
        
    def connect_mqtt(self):
        """Connect to MQTT broker"""
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        
        try:
            self.mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
            self.mqtt_client.loop_start()
            print("Gateway connected to MQTT broker")
        except Exception as e:
            print(f"Failed to connect gateway: {e}")
    
    def on_connect(self, client, userdata, flags, rc):
        """Callback for MQTT connection"""
        print(f"Gateway connected with result code {rc}")
        # Subscribe to all topics
        client.subscribe("smartroom/+/+")
    
    def on_message(self, client, userdata, msg):
        """Process incoming MQTT messages"""
        try:
            data = json.loads(msg.payload.decode())
            topic_parts = msg.topic.split('/')
            
            if len(topic_parts) >= 3:
                category = topic_parts[1]
                device_type = topic_parts[2]
                
                if category == "sensors":
                    self.process_sensor_data(device_type, data)
                elif category == "actuators":
                    self.process_actuator_data(device_type, data)
                
                # Emit to web dashboard via WebSocket
                socketio.emit('update', {
                    'category': category,
                    'type': device_type,
                    'data': data
                })
                
        except Exception as e:
            print(f"Error processing message: {e}")
    
    def process_sensor_data(self, sensor_type, data):
        """Process and store sensor data"""
        self.sensor_data[sensor_type] = data
        
        # Store history
        history_entry = {
            'timestamp': data.get('timestamp', datetime.now().isoformat()),
            'value': data.get('value')
        }
        self.data_history[sensor_type].append(history_entry)
        
        # Analytics
        self.analyze_comfort_levels(sensor_type, data.get('value'))
        
        # Edge processing - immediate responses
        self.edge_processing(sensor_type, data)
    
    def process_actuator_data(self, actuator_type, data):
        """Process actuator state updates"""
        self.actuator_states[actuator_type] = data
        
        # Handle notifications
        if actuator_type in ['notifications', 'system_notifications']:
            self.notifications.append({
                'timestamp': data.get('timestamp'),
                'message': data.get('message'),
                'type': actuator_type
            })
    
    def analyze_comfort_levels(self, sensor_type, value):
        """Track comfort level violations"""
        comfort_ranges = {
            'temperature': (20, 24),
            'humidity': (40, 60),
            'light': (300, 700),
            'noise': (0, 45)
        }
        
        if sensor_type in comfort_ranges:
            min_val, max_val = comfort_ranges[sensor_type]
            if value < min_val or value > max_val:
                self.comfort_violations[sensor_type] += 1
    
    def edge_processing(self, sensor_type, data):
        """Perform edge computing for immediate responses"""
        value = data.get('value')
        
        # Critical alerts
        if sensor_type == 'temperature' and (value < 16 or value > 30):
            self.send_alert("CRITICAL: Temperature out of safe range!")
        elif sensor_type == 'noise' and value > 70:
            self.send_alert("WARNING: Very high noise level detected!")
    
    def send_alert(self, message):
        """Send immediate alerts"""
        alert = {
            'type': 'gateway_alert',
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'severity': 'high'
        }
        
        # Emit to dashboard
        socketio.emit('alert', alert)
        
        # Store in notifications
        self.notifications.append(alert)
    
    def get_dashboard_data(self):
        """Compile data for dashboard"""
        return {
            'sensors': dict(self.sensor_data),
            'actuators': dict(self.actuator_states),
            'history': {k: list(v) for k, v in self.data_history.items()},
            'notifications': list(self.notifications),
            'analytics': {
                'comfort_violations': dict(self.comfort_violations),
                'study_sessions': self.study_sessions[-10:]  # Last 10 sessions
            }
        }
    
    def send_command(self, actuator_type, command):
        """Send control commands to actuators"""
        topic = f"smartroom/commands/{actuator_type}"
        self.mqtt_client.publish(topic, json.dumps(command))
        print(f"Command sent to {actuator_type}: {command}")

# Create global gateway instance
gateway = IoTGateway()

# Flask routes
@app.route('/')
def index():
    """Serve the main dashboard"""
    return render_template('dashboard.html')

@app.route('/api/data')
def get_data():
    """API endpoint for current data"""
    return jsonify(gateway.get_dashboard_data())

@app.route('/api/command', methods=['POST'])
def send_command():
    """API endpoint for sending commands"""
    data = request.json
    actuator_type = data.get('actuator_type')
    command = data.get('command')
    
    if actuator_type and command:
        gateway.send_command(actuator_type, command)
        return jsonify({'status': 'success'})
    
    return jsonify({'status': 'error', 'message': 'Invalid command'}), 400

@app.route('/api/analytics')
def get_analytics():
    """API endpoint for analytics data"""
    analytics = {
        'comfort_score': calculate_comfort_score(gateway.comfort_violations),
        'sensor_trends': analyze_trends(gateway.data_history),
        'recommendations': generate_recommendations(gateway.sensor_data)
    }
    return jsonify(analytics)

# WebSocket events
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print('Client connected')
    emit('connected', {'data': 'Connected to Smart Study Room Gateway'})
    
    # Send initial data
    emit('initial_data', gateway.get_dashboard_data())

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print('Client disconnected')

@socketio.on('request_update')
def handle_update_request():
    """Handle manual update requests"""
    emit('update_data', gateway.get_dashboard_data())

@socketio.on('send_command')
def handle_command(data):
    """Handle commands from web interface"""
    actuator_type = data.get('actuator_type')
    command = data.get('command')
    
    if actuator_type and command:
        gateway.send_command(actuator_type, command)
        emit('command_sent', {'status': 'success'})

# Analytics functions
def calculate_comfort_score(violations):
    """Calculate overall comfort score"""
    total_violations = sum(violations.values())
    if total_violations == 0:
        return 100
    
    # Deduct points for violations
    score = max(0, 100 - (total_violations * 2))
    return score

def analyze_trends(history):
    """Analyze sensor data trends"""
    trends = {}
    
    for sensor_type, data_points in history.items():
        if len(data_points) >= 10:
            values = [point['value'] for point in data_points[-10:]]
            avg = sum(values) / len(values)
            
            # Simple trend detection
            recent_avg = sum(values[-5:]) / 5
            older_avg = sum(values[:5]) / 5
            
            if recent_avg > older_avg * 1.1:
                trend = "increasing"
            elif recent_avg < older_avg * 0.9:
                trend = "decreasing"
            else:
                trend = "stable"
            
            trends[sensor_type] = {
                'current': values[-1],
                'average': round(avg, 2),
                'trend': trend
            }
    
    return trends

def generate_recommendations(sensor_data):
    """Generate smart recommendations based on current conditions"""
    recommendations = []
    
    # Temperature recommendations
    temp_data = sensor_data.get('temperature', {})
    if temp_data:
        temp = temp_data.get('value', 22)
        if temp < 20:
            recommendations.append("Room is too cold. Consider increasing temperature.")
        elif temp > 24:
            recommendations.append("Room is too warm. Consider cooling down.")
    
    # Light recommendations
    light_data = sensor_data.get('light', {})
    if light_data:
        light = light_data.get('value', 500)
        hour = datetime.now().hour
        
        if 9 <= hour <= 17 and light < 300:
            recommendations.append("Low light during study hours. Consider opening curtains or turning on lights.")
        elif hour >= 20 and light > 700:
            recommendations.append("Bright light in evening. Consider dimming for better sleep preparation.")
    
    # Noise recommendations
    noise_data = sensor_data.get('noise', {})
    if noise_data:
        noise = noise_data.get('value', 40)
        if noise > 50:
            recommendations.append("High noise levels. Consider using noise-cancelling headphones or finding a quieter space.")
    
    return recommendations

def run_gateway():
    """Run the gateway with MQTT and web server"""
    # Start MQTT connection
    gateway.connect_mqtt()
    
    # Start Flask-SocketIO server
    print(f"Starting web server on http://localhost:{WEB_PORT}")
    socketio.run(app, host='0.0.0.0', port=WEB_PORT, debug=False)

if __name__ == "__main__":
    try:
        run_gateway()
    except KeyboardInterrupt:
        print("\nShutting down gateway...")
        gateway.mqtt_client.loop_stop()
        gateway.mqtt_client.disconnect()