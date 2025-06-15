#!/usr/bin/env python3
"""
Smart Study Room IoT System
Main startup script for the complete IoT application
"""

import subprocess
import sys
import time
import os
import signal
from datetime import datetime

class SmartStudyRoomStarter:
    def __init__(self):
        self.processes = []
        self.running = False
    
    def start_mqtt_broker(self):
        """Start Mosquitto MQTT broker"""
        print("\nStarting MQTT Broker...")
        
        # Check if mosquitto is installed
        try:
            # Try to start mosquitto
            if sys.platform == "win32":
                broker_process = subprocess.Popen(['mosquitto'], 
                                                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
            else:
                broker_process = subprocess.Popen(['mosquitto'])
            
            self.processes.append(('MQTT Broker', broker_process))
            time.sleep(2)  # Give broker time to start
            print("✓ MQTT Broker started")
            return True
            
        except FileNotFoundError:
            print("⚠ Mosquitto MQTT broker not found!")
            print("\nPlease install Mosquitto:")
            print("  - Ubuntu/Debian: sudo apt-get install mosquitto")
            print("  - macOS: brew install mosquitto")
            print("  - Windows: Download from https://mosquitto.org/download/")
            print("\nAlternatively, you can use a public MQTT broker by modifying MQTT_BROKER in all files")
            return False
    
    def start_component(self, name, script):
        """Start an individual component"""
        print(f"\nStarting {name}...")
        
        try:
            if sys.platform == "win32":
                process = subprocess.Popen([sys.executable, script],
                                         creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
            else:
                process = subprocess.Popen([sys.executable, script])
            
            self.processes.append((name, process))
            time.sleep(1)  # Give component time to initialize
            print(f"✓ {name} started")
            return True
            
        except Exception as e:
            print(f"✗ Failed to start {name}: {e}")
            return False
    
    def start_all_components(self):
        """Start all IoT system components"""
        components = [
            ("Sensors", "sensor.py"),
            ("Actuators", "actuator.py"),
            ("Gateway & Dashboard", "gateway.py")
        ]
        
        for name, script in components:
            if not os.path.exists(script):
                print(f"\n✗ Error: {script} not found!")
                print("Make sure all component files are in the same directory.")
                return False
            
            if not self.start_component(name, script):
                return False
        
        return True
    
    def start_visualizer(self):
        """Optionally start the matplotlib visualizer"""
        print("\nWould you like to start the real-time visualizer? (y/n): ", end='')
        response = input().strip().lower()
        
        if response == 'y':
            self.start_component("Visualizer", "visualize.py")
    
    def display_status(self):
        """Display system status and instructions"""
        print("\n" + "="*60)
        print("🏠 SMART STUDY ROOM IoT SYSTEM RUNNING")
        print("="*60)
        print("\n📊 Dashboard URL: http://localhost:5000")
        print("\n🔧 System Components:")
        
        for name, process in self.processes:
            status = "Running" if process.poll() is None else "Stopped"
            print(f"  - {name}: {status}")
        
        print("\n📝 Instructions:")
        print("  - Open the dashboard URL in your web browser")
        print("  - Monitor real-time sensor data")
        print("  - Control actuators from the dashboard")
        print("  - Press Ctrl+C to stop all components")
        
        print("\n💡 Tips:")
        print("  - Sensors generate realistic data patterns")
        print("  - Actuators respond automatically to sensor data")
        print("  - Check notifications for study break reminders")
        print("  - The system tracks comfort levels and study sessions")
        
        print("\n" + "="*60)
    
    def cleanup(self):
        """Stop all processes gracefully"""
        print("\n\nShutting down Smart Study Room...")
        
        for name, process in self.processes:
            if process.poll() is None:
                print(f"Stopping {name}...")
                
                try:
                    if sys.platform == "win32":
                        process.send_signal(signal.CTRL_BREAK_EVENT)
                    else:
                        process.terminate()
                    
                    # Wait for graceful shutdown
                    process.wait(timeout=5)
                    
                except:
                    # Force kill if necessary
                    process.kill()
                
                print(f"✓ {name} stopped")
        
        print("\nAll components stopped. Goodbye! 👋")
    
    def run(self):
        """Main execution flow"""
        print("="*60)
        print("🏠 SMART STUDY ROOM IoT SYSTEM")
        print("="*60)
        print(f"\nStartup Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Start MQTT broker
        if not self.start_mqtt_broker():
            print("\n✗ Cannot proceed without MQTT broker.")
            print("You can use a public broker by changing MQTT_BROKER = 'test.mosquitto.org' in all files")
            return
        
        # Start all components
        if not self.start_all_components():
            print("\n✗ Failed to start all components.")
            self.cleanup()
            return
        
        # Optionally start visualizer
        self.start_visualizer()
        
        # Display status
        self.display_status()
        
        # Keep running until interrupted
        self.running = True
        try:
            while self.running:
                # Check if all processes are still running
                for name, process in self.processes:
                    if process.poll() is not None:
                        print(f"\n⚠ Warning: {name} has stopped unexpectedly!")
                
                time.sleep(5)
                
        except KeyboardInterrupt:
            self.running = False
        
        finally:
            self.cleanup()

def main():
    """Entry point"""
    starter = SmartStudyRoomStarter()
    
    # Handle Ctrl+C gracefully
    def signal_handler(sig, frame):
        starter.running = False
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Run the system
    starter.run()

if __name__ == "__main__":
    main()