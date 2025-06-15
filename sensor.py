import random
import time
import json
import threading
import paho.mqtt.client as mqtt
from datetime import datetime

# MQTT Configuration
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC_PREFIX = "smartroom/sensors"

class Sensor:
    """Base sensor class"""
    def __init__(self, sensor_id, sensor_type, unit, min_val, max_val):
        self.sensor_id = sensor_id
        self.sensor_type = sensor_type
        self.unit = unit
        self.min_val = min_val
        self.max_val = max_val
        self.current_value = (min_val + max_val) / 2
        self.mqtt_client = mqtt.Client(f"{sensor_type}_{sensor_id}")
        self.running = False
        
    def connect_mqtt(self):
        """Connect to MQTT broker"""
        try:
            self.mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
            self.mqtt_client.loop_start()
            print(f"{self.sensor_type} sensor connected to MQTT broker")
        except Exception as e:
            print(f"Failed to connect {self.sensor_type} sensor: {e}")
    
    def generate_data(self):
        """Generate realistic sensor data with some randomness"""
        # Add realistic fluctuations
        change = random.uniform(-2, 2)
        self.current_value += change
        
        # Keep within bounds
        self.current_value = max(self.min_val, min(self.max_val, self.current_value))
        
        # Add some noise
        noise = random.uniform(-0.5, 0.5)
        return round(self.current_value + noise, 2)
    
    def publish_data(self, value):
        """Publish sensor data to MQTT"""
        data = {
            "sensor_id": self.sensor_id,
            "type": self.sensor_type,
            "value": value,
            "unit": self.unit,
            "timestamp": datetime.now().isoformat()
        }
        
        topic = f"{MQTT_TOPIC_PREFIX}/{self.sensor_type}"
        self.mqtt_client.publish(topic, json.dumps(data))
        print(f"{self.sensor_type}: {value}{self.unit}")
    
    def run(self):
        """Main sensor loop"""
        self.running = True
        self.connect_mqtt()
        
        while self.running:
            value = self.generate_data()
            self.publish_data(value)
            time.sleep(2)  # Send data every 2 seconds
    
    def stop(self):
        """Stop the sensor"""
        self.running = False
        self.mqtt_client.loop_stop()
        self.mqtt_client.disconnect()

class TemperatureSensor(Sensor):
    """Temperature sensor with realistic patterns"""
    def __init__(self, sensor_id="temp_01"):
        super().__init__(sensor_id, "temperature", "°C", 18, 28)
        self.time_of_day_effect = 0
    
    def generate_data(self):
        """Generate temperature data with day/night patterns"""
        # Simulate day/night temperature variations
        hour = datetime.now().hour
        if 6 <= hour <= 18:  # Daytime
            self.time_of_day_effect = min(3, self.time_of_day_effect + 0.1)
        else:  # Nighttime
            self.time_of_day_effect = max(-2, self.time_of_day_effect - 0.1)
        
        base_value = super().generate_data()
        return round(base_value + self.time_of_day_effect, 2)

class HumiditySensor(Sensor):
    """Humidity sensor"""
    def __init__(self, sensor_id="hum_01"):
        super().__init__(sensor_id, "humidity", "%", 30, 70)

class LightSensor(Sensor):
    """Light sensor with day/night patterns"""
    def __init__(self, sensor_id="light_01"):
        super().__init__(sensor_id, "light", "lux", 0, 1000)
    
    def generate_data(self):
        """Generate light data based on time of day"""
        hour = datetime.now().hour
        
        # Simulate natural light patterns
        if 6 <= hour <= 8:  # Early morning
            self.current_value = random.uniform(100, 300)
        elif 9 <= hour <= 17:  # Daytime
            self.current_value = random.uniform(400, 800)
        elif 18 <= hour <= 20:  # Evening
            self.current_value = random.uniform(200, 400)
        else:  # Night
            self.current_value = random.uniform(0, 100)
        
        # Add random fluctuations (clouds, etc.)
        return round(self.current_value + random.uniform(-50, 50), 2)

class NoiseSensor(Sensor):
    """Noise level sensor"""
    def __init__(self, sensor_id="noise_01"):
        super().__init__(sensor_id, "noise", "dB", 30, 80)
    
    def generate_data(self):
        """Generate noise data with occasional spikes"""
        # Normal ambient noise
        base_noise = super().generate_data()
        
        # Occasional noise spikes (10% chance)
        if random.random() < 0.1:
            spike = random.uniform(10, 30)
            return round(min(self.max_val, base_noise + spike), 2)
        
        return round(base_noise, 2)

class MotionSensor(Sensor):
    """Motion detection sensor"""
    def __init__(self, sensor_id="motion_01"):
        super().__init__(sensor_id, "motion", "detected", 0, 1)
        self.motion_duration = 0
    
    def generate_data(self):
        """Generate motion detection data"""
        # Simulate study sessions with breaks
        hour = datetime.now().hour
        
        # More likely to detect motion during study hours
        if 9 <= hour <= 22:
            motion_probability = 0.7
        else:
            motion_probability = 0.1
        
        # Simulate continuous presence with occasional breaks
        if self.motion_duration > 0:
            self.motion_duration -= 1
            return 1
        elif random.random() < motion_probability:
            # Start a new presence period
            self.motion_duration = random.randint(10, 30)  # 20-60 seconds
            return 1
        
        return 0

def run_all_sensors():
    """Run all sensors in separate threads"""
    sensors = [
        TemperatureSensor(),
        HumiditySensor(),
        LightSensor(),
        NoiseSensor(),
        MotionSensor()
    ]
    
    threads = []
    
    print("Starting Smart Study Room Sensors...")
    
    for sensor in sensors:
        thread = threading.Thread(target=sensor.run)
        thread.daemon = True
        thread.start()
        threads.append((thread, sensor))
        time.sleep(0.5)  # Stagger sensor starts
    
    try:
        # Keep running until interrupted
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down sensors...")
        for _, sensor in threads:
            sensor.stop()
        for thread, _ in threads:
            thread.join()
        print("All sensors stopped.")

if __name__ == "__main__":
    run_all_sensors()