import json
import threading
import time
from datetime import datetime, timedelta
import paho.mqtt.client as mqtt

# MQTT Configuration
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_SENSOR_TOPIC = "smartroom/sensors/+"
MQTT_ACTUATOR_TOPIC = "smartroom/actuators"
MQTT_COMMAND_TOPIC = "smartroom/commands"

class Actuator:
    """Base actuator class"""
    def __init__(self, actuator_id, actuator_type):
        self.actuator_id = actuator_id
        self.actuator_type = actuator_type
        self.state = "OFF"
        self.mqtt_client = mqtt.Client(f"{actuator_type}_{actuator_id}")
        self.sensor_data = {}
        self.running = False
        
    def connect_mqtt(self):
        """Connect to MQTT broker and subscribe to topics"""
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        
        try:
            self.mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
            self.mqtt_client.loop_start()
            print(f"{self.actuator_type} actuator connected to MQTT broker")
        except Exception as e:
            print(f"Failed to connect {self.actuator_type} actuator: {e}")
    
    def on_connect(self, client, userdata, flags, rc):
        """Callback for MQTT connection"""
        print(f"{self.actuator_type} connected with result code {rc}")
        client.subscribe(MQTT_SENSOR_TOPIC)
        client.subscribe(f"{MQTT_COMMAND_TOPIC}/{self.actuator_type}")
    
    def on_message(self, client, userdata, msg):
        """Handle incoming MQTT messages"""
        try:
            if msg.topic.startswith("smartroom/sensors"):
                # Update sensor data
                data = json.loads(msg.payload.decode())
                self.sensor_data[data['type']] = data
            elif msg.topic.startswith("smartroom/commands"):
                # Handle manual commands
                command = json.loads(msg.payload.decode())
                self.handle_command(command)
        except Exception as e:
            print(f"Error processing message: {e}")
    
    def handle_command(self, command):
        """Handle manual control commands"""
        if command.get('actuator_id') == self.actuator_id:
            self.state = command.get('state', self.state)
            self.publish_state()
    
    def publish_state(self):
        """Publish actuator state"""
        data = {
            "actuator_id": self.actuator_id,
            "type": self.actuator_type,
            "state": self.state,
            "timestamp": datetime.now().isoformat()
        }
        
        topic = f"{MQTT_ACTUATOR_TOPIC}/{self.actuator_type}"
        self.mqtt_client.publish(topic, json.dumps(data))
        print(f"{self.actuator_type}: {self.state}")
    
    def run(self):
        """Main actuator loop"""
        self.running = True
        self.connect_mqtt()
        
        while self.running:
            self.process_sensor_data()
            time.sleep(5)  # Process every 5 seconds
    
    def process_sensor_data(self):
        """Override in subclasses to implement specific logic"""
        pass
    
    def stop(self):
        """Stop the actuator"""
        self.running = False
        self.mqtt_client.loop_stop()
        self.mqtt_client.disconnect()

class SmartLight(Actuator):
    """Smart lighting control based on ambient light and motion"""
    def __init__(self, actuator_id="light_01"):
        super().__init__(actuator_id, "smart_light")
        self.brightness = 0
        self.auto_mode = True
        
    def process_sensor_data(self):
        """Adjust lighting based on sensor data"""
        light_data = self.sensor_data.get('light', {})
        motion_data = self.sensor_data.get('motion', {})
        
        if not light_data or not self.auto_mode:
            return
        
        light_level = light_data.get('value', 500)
        motion_detected = motion_data.get('value', 0) if motion_data else 0
        
        # Determine optimal brightness
        if motion_detected:
            if light_level < 200:  # Dark room
                self.brightness = 100
                self.state = "ON"
            elif light_level < 400:  # Dim room
                self.brightness = 60
                self.state = "ON"
            elif light_level < 600:  # Moderate light
                self.brightness = 30
                self.state = "ON"
            else:  # Bright room
                self.brightness = 0
                self.state = "OFF"
        else:
            # No motion - turn off or dim lights
            if self.state == "ON":
                self.brightness = max(0, self.brightness - 20)
                if self.brightness == 0:
                    self.state = "OFF"
        
        self.publish_state()
    
    def publish_state(self):
        """Publish light state with brightness"""
        data = {
            "actuator_id": self.actuator_id,
            "type": self.actuator_type,
            "state": self.state,
            "brightness": self.brightness,
            "auto_mode": self.auto_mode,
            "timestamp": datetime.now().isoformat()
        }
        
        topic = f"{MQTT_ACTUATOR_TOPIC}/{self.actuator_type}"
        self.mqtt_client.publish(topic, json.dumps(data))
        print(f"Smart Light: {self.state} (Brightness: {self.brightness}%)")

class ClimateControl(Actuator):
    """HVAC control based on temperature and humidity"""
    def __init__(self, actuator_id="climate_01"):
        super().__init__(actuator_id, "climate_control")
        self.mode = "AUTO"  # OFF, COOL, HEAT, AUTO
        self.target_temp = 22
        self.target_humidity = 50
        
    def process_sensor_data(self):
        """Adjust climate based on sensor data"""
        temp_data = self.sensor_data.get('temperature', {})
        humidity_data = self.sensor_data.get('humidity', {})
        
        if not temp_data:
            return
        
        current_temp = temp_data.get('value', 22)
        current_humidity = humidity_data.get('value', 50) if humidity_data else 50
        
        # Temperature control logic
        if self.mode == "AUTO":
            if current_temp > self.target_temp + 2:
                self.state = "COOLING"
            elif current_temp < self.target_temp - 2:
                self.state = "HEATING"
            else:
                self.state = "IDLE"
        
        # Humidity alert
        if current_humidity < 30 or current_humidity > 70:
            self.publish_alert("Humidity out of comfort range!")
        
        self.publish_state()
    
    def publish_alert(self, message):
        """Publish climate alerts"""
        alert = {
            "actuator_id": self.actuator_id,
            "type": "alert",
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        self.mqtt_client.publish(f"{MQTT_ACTUATOR_TOPIC}/alerts", json.dumps(alert))

class FocusMode(Actuator):
    """Focus mode controller based on noise levels and study patterns"""
    def __init__(self, actuator_id="focus_01"):
        super().__init__(actuator_id, "focus_mode")
        self.noise_threshold = 50
        self.study_start = None
        self.break_reminder_sent = False
        
    def process_sensor_data(self):
        """Monitor study conditions and send notifications"""
        noise_data = self.sensor_data.get('noise', {})
        motion_data = self.sensor_data.get('motion', {})
        
        if not noise_data:
            return
        
        noise_level = noise_data.get('value', 40)
        motion_detected = motion_data.get('value', 0) if motion_data else 0
        
        # Noise level monitoring
        if noise_level > self.noise_threshold:
            self.state = "NOISY"
            self.publish_notification("High noise level detected! Consider using headphones.")
        else:
            self.state = "QUIET"
        
        # Study session tracking
        if motion_detected:
            if not self.study_start:
                self.study_start = datetime.now()
                self.break_reminder_sent = False
                self.publish_notification("Study session started. Good luck!")
            elif not self.break_reminder_sent and \
                 (datetime.now() - self.study_start) > timedelta(minutes=45):
                self.publish_notification("You've been studying for 45 minutes. Time for a break!")
                self.break_reminder_sent = True
        else:
            if self.study_start:
                duration = (datetime.now() - self.study_start).seconds // 60
                if duration > 5:  # Only log sessions longer than 5 minutes
                    self.publish_notification(f"Study session ended. Duration: {duration} minutes")
                self.study_start = None
        
        self.publish_state()
    
    def publish_notification(self, message):
        """Publish focus mode notifications"""
        notification = {
            "actuator_id": self.actuator_id,
            "type": "notification",
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        self.mqtt_client.publish(f"{MQTT_ACTUATOR_TOPIC}/notifications", json.dumps(notification))
        print(f"Focus Mode Notification: {message}")

class NotificationSystem(Actuator):
    """Central notification system for alerts and reminders"""
    def __init__(self, actuator_id="notify_01"):
        super().__init__(actuator_id, "notification_system")
        self.alert_history = []
        self.comfort_ranges = {
            'temperature': (20, 24),
            'humidity': (40, 60),
            'light': (300, 700),
            'noise': (0, 45)
        }
        
    def process_sensor_data(self):
        """Monitor all conditions and generate consolidated alerts"""
        alerts = []
        
        for sensor_type, (min_val, max_val) in self.comfort_ranges.items():
            sensor_data = self.sensor_data.get(sensor_type, {})
            if sensor_data:
                value = sensor_data.get('value', 0)
                if value < min_val or value > max_val:
                    alerts.append(f"{sensor_type.capitalize()} is outside comfort range: {value}")
        
        # Send consolidated alert if multiple issues
        if len(alerts) >= 2:
            self.state = "ALERT"
            message = "Multiple comfort issues detected:\n" + "\n".join(alerts)
            self.publish_notification(message)
        elif alerts:
            self.state = "WARNING"
        else:
            self.state = "OK"
        
        self.publish_state()
    
    def publish_notification(self, message):
        """Publish system-wide notifications"""
        notification = {
            "actuator_id": self.actuator_id,
            "type": "system_notification",
            "message": message,
            "severity": "warning" if self.state == "WARNING" else "alert",
            "timestamp": datetime.now().isoformat()
        }
        self.mqtt_client.publish(f"{MQTT_ACTUATOR_TOPIC}/system_notifications", json.dumps(notification))
        print(f"System Notification: {message}")

def run_all_actuators():
    """Run all actuators in separate threads"""
    actuators = [
        SmartLight(),
        ClimateControl(),
        FocusMode(),
        NotificationSystem()
    ]
    
    threads = []
    
    print("Starting Smart Study Room Actuators...")
    
    for actuator in actuators:
        thread = threading.Thread(target=actuator.run)
        thread.daemon = True
        thread.start()
        threads.append((thread, actuator))
        time.sleep(0.5)  # Stagger actuator starts
    
    try:
        # Keep running until interrupted
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down actuators...")
        for _, actuator in threads:
            actuator.stop()
        for thread, _ in threads:
            thread.join()
        print("All actuators stopped.")

if __name__ == "__main__":
    run_all_actuators()