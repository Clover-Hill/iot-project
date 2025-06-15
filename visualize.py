import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.dates import DateFormatter
import numpy as np
from datetime import datetime, timedelta
from collections import deque
import json
import paho.mqtt.client as mqtt
import threading
import time

# MQTT Configuration
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "smartroom/+/+"

class DataVisualizer:
    """Real-time data visualization for IoT sensors"""
    def __init__(self):
        try:
            # Try new version (2.0+) with callback API version
            self.mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, "visualizer")
        except AttributeError:
            # Fall back to old version
            self.mqtt_client = mqtt.Client("visualizer")
        self.data_buffers = {
            'temperature': deque(maxlen=50),
            'humidity': deque(maxlen=50),
            'light': deque(maxlen=50),
            'noise': deque(maxlen=50)
        }
        self.timestamps = deque(maxlen=50)
        self.running = False
        
        # Setup matplotlib
        plt.style.use('dark_background')
        self.fig, self.axes = plt.subplots(2, 2, figsize=(12, 8))
        self.fig.suptitle('Smart Study Room - Real-time Monitoring', fontsize=16)
        
        # Flatten axes for easier access
        self.axes = self.axes.flatten()
        
        # Configure each subplot
        self.plot_configs = [
            {'sensor': 'temperature', 'color': '#ff6b6b', 'ylabel': 'Temperature (°C)', 'ylim': (15, 30)},
            {'sensor': 'humidity', 'color': '#4ecdc4', 'ylabel': 'Humidity (%)', 'ylim': (20, 80)},
            {'sensor': 'light', 'color': '#ffe66d', 'ylabel': 'Light (lux)', 'ylim': (0, 1000)},
            {'sensor': 'noise', 'color': '#a8e6cf', 'ylabel': 'Noise (dB)', 'ylim': (20, 90)}
        ]
        
        self.lines = []
        self.comfort_zones = []
        
        # Initialize plots
        self.setup_plots()
        
    def connect_mqtt(self):
        """Connect to MQTT broker"""
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        
        try:
            self.mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
            self.mqtt_client.loop_start()
            print("Visualizer connected to MQTT broker")
        except Exception as e:
            print(f"Failed to connect visualizer: {e}")
    
    def on_connect(self, client, userdata, flags, rc):
        """Callback for MQTT connection"""
        print(f"Visualizer connected with result code {rc}")
        client.subscribe(MQTT_TOPIC)
    
    def on_message(self, client, userdata, msg):
        """Process incoming sensor data"""
        try:
            data = json.loads(msg.payload.decode())
            sensor_type = data.get('type')
            
            if sensor_type in self.data_buffers:
                value = data.get('value')
                timestamp = datetime.fromisoformat(data.get('timestamp'))
                
                # Add data to buffers
                self.data_buffers[sensor_type].append(value)
                
                # Ensure we have synchronized timestamps
                if len(self.timestamps) == 0 or timestamp > self.timestamps[-1]:
                    self.timestamps.append(timestamp)
                
        except Exception as e:
            print(f"Error processing visualization data: {e}")
    
    def setup_plots(self):
        """Initialize the plot layouts and styles"""
        comfort_ranges = {
            'temperature': (20, 24),
            'humidity': (40, 60),
            'light': (300, 700),
            'noise': (0, 45)
        }
        
        for idx, (ax, config) in enumerate(zip(self.axes, self.plot_configs)):
            # Create line plot
            line, = ax.plot([], [], color=config['color'], linewidth=2, 
                           marker='o', markersize=4, alpha=0.8)
            self.lines.append(line)
            
            # Add comfort zone
            sensor = config['sensor']
            if sensor in comfort_ranges:
                comfort_min, comfort_max = comfort_ranges[sensor]
                ax.axhspan(comfort_min, comfort_max, alpha=0.2, color='green', 
                          label='Comfort Zone')
            
            # Configure axes
            ax.set_ylabel(config['ylabel'])
            ax.set_ylim(config['ylim'])
            ax.grid(True, alpha=0.3)
            ax.set_title(f"{sensor.capitalize()} Sensor", fontsize=12)
            
            # Only show x-label for bottom plots
            if idx >= 2:
                ax.set_xlabel('Time')
    
    def animate(self, frame):
        """Animation function for real-time updates"""
        if len(self.timestamps) > 1:
            # Convert timestamps to matplotlib format
            time_data = self.timestamps
            
            for idx, (line, config) in enumerate(zip(self.lines, self.plot_configs)):
                sensor = config['sensor']
                data = list(self.data_buffers[sensor])
                
                if len(data) > 1 and len(data) == len(time_data):
                    line.set_data(time_data, data)
                    
                    # Auto-adjust x-axis
                    ax = self.axes[idx]
                    ax.relim()
                    ax.autoscale_view(scaley=False)
                    
                    # Format x-axis
                    ax.xaxis.set_major_formatter(DateFormatter('%H:%M:%S'))
                    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
                    
                    # Add current value annotation
                    if data:
                        current_val = data[-1]
                        ax.text(0.02, 0.95, f'Current: {current_val:.1f}', 
                               transform=ax.transAxes, fontsize=10,
                               verticalalignment='top',
                               bbox=dict(boxstyle='round', facecolor='black', alpha=0.5))
        
        plt.tight_layout()
        return self.lines
    
    def generate_report(self):
        """Generate a statistical report of sensor data"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {}
        }
        
        for sensor, data in self.data_buffers.items():
            if len(data) > 0:
                data_array = np.array(data)
                report['summary'][sensor] = {
                    'current': float(data[-1]) if data else None,
                    'average': float(np.mean(data_array)),
                    'min': float(np.min(data_array)),
                    'max': float(np.max(data_array)),
                    'std_dev': float(np.std(data_array)),
                    'trend': self.calculate_trend(data_array)
                }
        
        # Save report
        with open(f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Report generated: {report['timestamp']}")
        return report
    
    def calculate_trend(self, data):
        """Calculate trend direction of data"""
        if len(data) < 5:
            return "insufficient_data"
        
        # Simple linear regression
        x = np.arange(len(data))
        coefficients = np.polyfit(x, data, 1)
        slope = coefficients[0]
        
        if abs(slope) < 0.1:
            return "stable"
        elif slope > 0:
            return "increasing"
        else:
            return "decreasing"
    
    def save_snapshot(self):
        """Save current visualization as image"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"snapshot_{timestamp}.png"
        self.fig.savefig(filename, dpi=150, bbox_inches='tight')
        print(f"Snapshot saved: {filename}")
    
    def run(self):
        """Run the visualizer"""
        self.running = True
        self.connect_mqtt()
        
        # Create animation
        ani = animation.FuncAnimation(
            self.fig, self.animate, interval=1000, blit=True, cache_frame_data=False
        )
        
        # Setup keyboard shortcuts
        def on_key(event):
            if event.key == 's':
                self.save_snapshot()
            elif event.key == 'r':
                self.generate_report()
            elif event.key == 'q':
                self.stop()
                plt.close('all')
        
        self.fig.canvas.mpl_connect('key_press_event', on_key)
        
        # Add instructions
        self.fig.text(0.5, 0.02, 'Press: [S] Save snapshot | [R] Generate report | [Q] Quit', 
                     ha='center', fontsize=10, color='gray')
        
        print("Visualizer started. Press 'Q' to quit.")
        plt.show()
    
    def stop(self):
        """Stop the visualizer"""
        self.running = False
        self.mqtt_client.loop_stop()
        self.mqtt_client.disconnect()
        print("Visualizer stopped.")

class AdvancedVisualizer:
    """Advanced visualization with multiple views"""
    def __init__(self):
        self.mqtt_client = mqtt.Client("advanced_visualizer")
        self.sensor_data = {}
        self.actuator_data = {}
        
        # Setup figure with subplots
        self.fig = plt.figure(figsize=(15, 10))
        self.fig.suptitle('Smart Study Room - Advanced Analytics', fontsize=16)
        
        # Create grid layout
        gs = self.fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
        
        # Define subplot areas
        self.ax_heatmap = self.fig.add_subplot(gs[0:2, 0:2])
        self.ax_comfort = self.fig.add_subplot(gs[0, 2])
        self.ax_energy = self.fig.add_subplot(gs[1, 2])
        self.ax_timeline = self.fig.add_subplot(gs[2, :])
        
        plt.style.use('dark_background')
        
    def create_heatmap(self):
        """Create hourly heatmap of sensor data"""
        # Generate sample data for demonstration
        hours = np.arange(24)
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        
        # Create random data for demonstration
        data = np.random.rand(7, 24) * 30 + 20  # Temperature data
        
        im = self.ax_heatmap.imshow(data, cmap='RdYlBu_r', aspect='auto')
        
        # Set ticks
        self.ax_heatmap.set_xticks(np.arange(24))
        self.ax_heatmap.set_yticks(np.arange(7))
        self.ax_heatmap.set_xticklabels(hours)
        self.ax_heatmap.set_yticklabels(days)
        
        # Labels
        self.ax_heatmap.set_xlabel('Hour of Day')
        self.ax_heatmap.set_ylabel('Day of Week')
        self.ax_heatmap.set_title('Temperature Heatmap (°C)')
        
        # Add colorbar
        cbar = plt.colorbar(im, ax=self.ax_heatmap)
        cbar.set_label('Temperature (°C)')
    
    def create_comfort_gauge(self):
        """Create comfort score gauge"""
        # Create pie chart as gauge
        comfort_score = 85  # Example score
        
        sizes = [comfort_score, 100 - comfort_score]
        colors = ['#4caf50', '#333333']
        
        self.ax_comfort.pie(sizes, colors=colors, startangle=90, counterclock=False)
        
        # Add center circle to create donut
        centre_circle = plt.Circle((0, 0), 0.70, fc='black')
        self.ax_comfort.add_artist(centre_circle)
        
        # Add score text
        self.ax_comfort.text(0, 0, f'{comfort_score}%', 
                            ha='center', va='center', fontsize=24, fontweight='bold')
        self.ax_comfort.set_title('Comfort Score')
    
    def create_energy_usage(self):
        """Create energy usage chart"""
        categories = ['Lighting', 'HVAC', 'Other']
        values = [30, 55, 15]  # Example percentages
        colors = ['#ffe66d', '#4ecdc4', '#a8e6cf']
        
        bars = self.ax_energy.barh(categories, values, color=colors)
        
        # Add value labels
        for bar in bars:
            width = bar.get_width()
            self.ax_energy.text(width + 1, bar.get_y() + bar.get_height()/2, 
                               f'{width}%', ha='left', va='center')
        
        self.ax_energy.set_xlabel('Energy Usage (%)')
        self.ax_energy.set_title('Energy Distribution')
        self.ax_energy.set_xlim(0, 100)
    
    def create_timeline(self):
        """Create activity timeline"""
        # Sample events
        events = [
            {'time': 8, 'duration': 2, 'type': 'study', 'label': 'Morning Study'},
            {'time': 11, 'duration': 1, 'type': 'break', 'label': 'Break'},
            {'time': 13, 'duration': 3, 'type': 'study', 'label': 'Afternoon Study'},
            {'time': 17, 'duration': 1, 'type': 'break', 'label': 'Break'},
            {'time': 19, 'duration': 2, 'type': 'study', 'label': 'Evening Study'}
        ]
        
        colors = {'study': '#4a90e2', 'break': '#e94b3c'}
        
        for event in events:
            self.ax_timeline.barh(0, event['duration'], left=event['time'], 
                                 height=0.5, color=colors[event['type']], 
                                 label=event['label'])
            
            # Add label
            self.ax_timeline.text(event['time'] + event['duration']/2, 0, 
                                 event['label'], ha='center', va='center', 
                                 fontsize=9, color='white')
        
        self.ax_timeline.set_xlim(0, 24)
        self.ax_timeline.set_ylim(-0.5, 0.5)
        self.ax_timeline.set_xlabel('Hour of Day')
        self.ax_timeline.set_title('Today\'s Activity Timeline')
        self.ax_timeline.set_yticks([])
        
        # Add grid
        self.ax_timeline.grid(True, axis='x', alpha=0.3)
    
    def show(self):
        """Display the advanced visualization"""
        self.create_heatmap()
        self.create_comfort_gauge()
        self.create_energy_usage()
        self.create_timeline()
        
        plt.tight_layout()
        plt.show()

def run_visualizer(mode='realtime'):
    """Run the selected visualizer"""
    if mode == 'realtime':
        visualizer = DataVisualizer()
        visualizer.run()
    elif mode == 'advanced':
        visualizer = AdvancedVisualizer()
        visualizer.show()
    else:
        print("Invalid mode. Choose 'realtime' or 'advanced'")

if __name__ == "__main__":
    import sys
    
    mode = sys.argv[1] if len(sys.argv) > 1 else 'realtime'
    run_visualizer(mode)