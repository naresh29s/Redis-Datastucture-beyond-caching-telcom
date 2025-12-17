#!/usr/bin/env python3
"""
AT&T Network Operations Data Simulator
Generates realistic telecommunications network data for Redis Enterprise demo

Simulates:
1. Network assets (cell towers, service vehicles, network equipment)
2. IoT telemetry data from network infrastructure
3. Network metrics and alerts
"""

import redis
import json
import time
import random
import math
import threading
from datetime import datetime, timedelta
import logging
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Redis Cloud connection configuration
# Credentials are loaded from .env file (see .env.example for template)
REDIS_HOST = os.getenv('REDIS_HOST')
REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
REDIS_USERNAME = os.getenv('REDIS_USERNAME', 'default')
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')

# Validate required environment variables
if not REDIS_HOST:
    logger.error("❌ REDIS_HOST environment variable is not set!")
    logger.error("Please copy .env.example to .env and configure your Redis credentials.")
    exit(1)

if not REDIS_PASSWORD:
    logger.error("❌ REDIS_PASSWORD environment variable is not set!")
    logger.error("Please copy .env.example to .env and configure your Redis credentials.")
    exit(1)

try:
    # Connect to Redis Cloud with authentication
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        username=REDIS_USERNAME,
        password=REDIS_PASSWORD,
        decode_responses=True,
        socket_connect_timeout=10,
        socket_timeout=10
    )

    # Test connection
    redis_client.ping()
    logger.info(f"✅ Connected to Redis Cloud at {REDIS_HOST}:{REDIS_PORT}")
except Exception as e:
    logger.error(f"❌ Failed to connect to Redis Cloud: {e}")
    exit(1)

# ============================================================================
# NETWORK ASSET SIMULATION
# ============================================================================

class AssetSimulator:
    def __init__(self):
        # Dallas-Fort Worth Metro Area coordinates
        self.base_lat = 32.7767
        self.base_lon = -96.7970
        self.field_radius = 0.5  # degrees (~50km)

        self.asset_types = [
            'cell_tower', 'service_vehicle', 'base_station', 'router',
            'switch', 'fiber_node', 'antenna', 'repeater'
        ]

        self.assets = {}
        self.initialize_assets()

    def initialize_assets(self):
        """Initialize network assets with comprehensive JSON data using RedisJSON"""
        import json
        from datetime import datetime, timedelta

        # Asset configurations with enhanced data and diverse types - 14 assets distributed across 100-mile radius
        # Base location: Dallas-Fort Worth Metro Area (32.78°N, -96.80°W)
        # Geographic distribution: ~100-mile radius (approximately 1.5 degrees lat/lon)
        asset_configs = [
            # Cell Towers (3 assets) - Primary network infrastructure
            {'id': 'TOWER-001', 'name': 'Cell Tower Downtown-001', 'type': 'cell_tower', 'lat': 32.78, 'lon': -96.80, 'manufacturer': 'Ericsson', 'model': 'AIR-6488'},
            {'id': 'TOWER-002', 'name': 'Cell Tower North-002', 'type': 'cell_tower', 'lat': 33.12, 'lon': -96.65, 'manufacturer': 'Nokia', 'model': 'AirScale-5G'},
            {'id': 'TOWER-003', 'name': 'Cell Tower West-003', 'type': 'cell_tower', 'lat': 32.95, 'lon': -97.25, 'manufacturer': 'Samsung', 'model': 'Compact-Macro'},

            # Base Stations (3 assets) - Various station types
            {'id': 'BASE-001', 'name': 'Base Station Alpha', 'type': 'base_station', 'lat': 32.45, 'lon': -96.92, 'manufacturer': 'Ericsson', 'model': 'RBS-6000'},
            {'id': 'BASE-002', 'name': 'Base Station Beta', 'type': 'base_station', 'lat': 32.89, 'lon': -97.15, 'manufacturer': 'Nokia', 'model': 'Flexi-Zone'},
            {'id': 'BASE-003', 'name': 'Base Station Gamma', 'type': 'base_station', 'lat': 33.15, 'lon': -96.78, 'manufacturer': 'Samsung', 'model': 'Compact-Base'},

            # Routers (2 assets) - Network routing equipment
            {'id': 'RTR-ALPHA', 'name': 'Core Router Alpha', 'type': 'router', 'lat': 32.67, 'lon': -96.85, 'manufacturer': 'Cisco', 'model': 'ASR-9000'},
            {'id': 'RTR-BETA', 'name': 'Edge Router Beta', 'type': 'router', 'lat': 32.56, 'lon': -97.05, 'manufacturer': 'Cisco', 'model': 'ASR-1000'},

            # Switches (2 assets) - Network switching stations
            {'id': 'SWH-001', 'name': 'Distribution Switch 001', 'type': 'switch', 'lat': 33.01, 'lon': -96.89, 'manufacturer': 'Cisco', 'model': 'Catalyst-9500'},
            {'id': 'SWH-002', 'name': 'Access Switch 002', 'type': 'switch', 'lat': 32.34, 'lon': -96.67, 'manufacturer': 'Cisco', 'model': 'Catalyst-9300'},

            # Fiber Nodes (2 assets) - Fiber optic distribution
            {'id': 'FIBER-001', 'name': 'Fiber Node 001', 'type': 'fiber_node', 'lat': 32.78, 'lon': -96.95, 'manufacturer': 'Nokia', 'model': 'FN-7500'},
            {'id': 'FIBER-002', 'name': 'Fiber Node 002', 'type': 'fiber_node', 'lat': 32.89, 'lon': -96.72, 'manufacturer': 'Ericsson', 'model': 'FN-6200'},

            # Antenna (1 asset) - Signal transmission
            {'id': 'ANT-001', 'name': 'Antenna Array 001', 'type': 'antenna', 'lat': 32.98, 'lon': -96.88, 'manufacturer': 'Ericsson', 'model': 'AIR-32'},

            # Service Vehicle (1 asset) - Mobile service equipment
            {'id': 'SVC-001', 'name': 'Field Service Vehicle 001', 'type': 'service_vehicle', 'lat': 32.82, 'lon': -96.82, 'manufacturer': 'Ford', 'model': 'F-350-Tech'}
        ]

        maintenance_teams = ['Network Ops A', 'Network Ops B', 'Network Ops C', 'Field Service Alpha', 'Tower Maintenance Team']
        contacts = [
            {'name': 'John Doe', 'email': 'john.doe@att.com'},
            {'name': 'Sarah Johnson', 'email': 'sarah.johnson@att.com'},
            {'name': 'Mike Wilson', 'email': 'mike.wilson@att.com'},
            {'name': 'Lisa Chen', 'email': 'lisa.chen@att.com'},
            {'name': 'David Rodriguez', 'email': 'david.rodriguez@att.com'}
        ]

        for config in asset_configs:
            lat, lon = config['lat'], config['lon']

            # Generate realistic dates
            install_date = datetime.now() - timedelta(days=random.randint(365, 1095))  # 1-3 years ago
            last_service = datetime.now() - timedelta(days=random.randint(1, 90))  # 1-90 days ago
            next_service = last_service + timedelta(days=random.randint(30, 120))  # 30-120 days from last service
            last_fault = datetime.now() - timedelta(days=random.randint(1, 30))  # 1-30 days ago

            # Create comprehensive asset JSON document
            asset_json = {
                "asset": {
                    "id": config['id'],
                    "name": config['name'],
                    "type": config['type'],
                    "group": "DFW Metro Network A",
                    "model": {
                        "manufacturer": config['manufacturer'],
                        "model_number": config['model'],
                        "serial_number": f"SN-{random.randint(10000000, 99999999)}",
                        "install_date": install_date.strftime("%Y-%m-%d")
                    },
                    "status": {
                        "state": random.choice(['active', 'maintenance', 'standby', 'offline']),
                        "last_update": datetime.now().isoformat(),
                        "health_score": random.randint(85, 99),
                        "runtime_hours": random.randint(1000, 8000)
                    },
                    "location": {
                        "latitude": lat,
                        "longitude": lon,
                        "elevation_ft": random.randint(500, 800),
                        "zone": f"DFW Metro Zone {random.randint(1, 6)}",
                        "region_code": f"TX-DFW{random.randint(1, 6)}"
                    },
                    "metrics": self._generate_asset_metrics(config['type']),
                    "maintenance": {
                        "last_service_date": last_service.strftime("%Y-%m-%d"),
                        "next_service_due": next_service.strftime("%Y-%m-%d"),
                        "total_downtime_hours": random.randint(50, 300),
                        "last_fault": {
                            "code": f"E-{random.randint(100, 999)}",
                            "timestamp": last_fault.isoformat() + "Z"
                        },
                        "maintenance_team": random.choice(maintenance_teams),
                        "contact": random.choice(contacts)
                    },
                    "connectivity": {
                        "sensor_id": f"SENSOR-{config['id'].replace('-', '')}",
                        "communication_status": random.choice(['online', 'online', 'online', 'degraded']),  # Mostly online
                        "data_source": random.choice(['Modbus/TCP', 'OPC-UA', 'MQTT', 'LoRaWAN']),
                        "data_frequency": random.choice(['1s', '5s', '10s', '30s']),
                        "last_data_received": (datetime.now() - timedelta(seconds=random.randint(1, 300))).isoformat() + "Z"
                    },
                    "analytics": {
                        "avg_uptime_pct": round(random.uniform(95.0, 99.5), 1),
                        "maintenance_cost_to_date": round(random.uniform(5000, 25000), 2)
                    },
                    "metadata": {
                        "created_by": "system",
                        "created_at": install_date.isoformat() + "Z",
                        "updated_by": "Naresh Sanodariya",
                        "version": f"v1.{random.randint(1, 5)}.{random.randint(0, 9)}"
                    }
                }
            }

            # Store in memory for simulator use (simplified version)
            metrics = asset_json['asset']['metrics']
            self.assets[config['id']] = {
                'id': config['id'],
                'name': config['name'],
                'type': config['type'],
                'status': asset_json['asset']['status']['state'],
                'latitude': str(lat),
                'longitude': str(lon),
                'location': config['id'],  # For sensor data correlation
                'temperature': metrics['temperature_c'],
                'signal_strength': metrics.get('signal_strength_dbm', 0),
                'bandwidth': metrics.get('bandwidth_mbps', metrics.get('throughput_gbps', 0)),
                'vibration': metrics['vibration_mm_s'],
                'last_update': datetime.now().isoformat()
            }

            # Store in Redis using RedisJSON
            redis_client.execute_command('JSON.SET', f'telcom:asset:{config["id"]}', '.', json.dumps(asset_json))

            # Maintain geospatial index for map display
            redis_client.geoadd('telcom:assets:locations', (lon, lat, config['id']))

        logger.info(f"✅ Initialized {len(self.assets)} network assets with comprehensive JSON data")

    def _generate_asset_metrics(self, asset_type):
        """Generate asset-specific metrics based on equipment type"""
        if asset_type == 'cell_tower':
            return {
                "temperature_c": round(random.uniform(25, 45), 1),
                "signal_strength_dbm": round(random.uniform(-85, -45), 1),
                "bandwidth_mbps": round(random.uniform(100, 500), 1),
                "vibration_mm_s": round(random.uniform(0.1, 0.5), 2),
                "power_kwh": round(random.uniform(5.0, 15.0), 1),
                "active_connections": random.randint(50, 500)
            }
        elif asset_type == 'base_station':
            return {
                "temperature_c": round(random.uniform(30, 50), 1),
                "signal_strength_dbm": round(random.uniform(-80, -40), 1),
                "bandwidth_mbps": round(random.uniform(80, 400), 1),
                "vibration_mm_s": round(random.uniform(0.1, 0.8), 2),
                "power_kwh": round(random.uniform(3.0, 10.0), 1),
                "active_connections": random.randint(30, 300)
            }
        elif asset_type == 'router':
            return {
                "temperature_c": round(random.uniform(35, 55), 1),
                "signal_strength_dbm": round(random.uniform(-75, -35), 1),
                "bandwidth_mbps": round(random.uniform(500, 2000), 1),
                "vibration_mm_s": round(random.uniform(0.05, 0.3), 2),
                "power_kwh": round(random.uniform(10, 30), 1),
                "packet_loss_pct": round(random.uniform(0.01, 0.5), 2),
                "latency_ms": round(random.uniform(5, 25), 1)
            }
        elif asset_type == 'switch':
            return {
                "temperature_c": round(random.uniform(30, 50), 1),
                "signal_strength_dbm": round(random.uniform(-70, -30), 1),
                "bandwidth_mbps": round(random.uniform(200, 1000), 1),
                "vibration_mm_s": round(random.uniform(0.05, 0.4), 2),
                "power_kwh": round(random.uniform(5, 20), 1),
                "port_utilization_pct": round(random.uniform(40, 85), 1),
                "throughput_gbps": round(random.uniform(1, 10), 1)
            }
        elif asset_type == 'fiber_node':
            return {
                "temperature_c": round(random.uniform(25, 40), 1),
                "signal_strength_dbm": round(random.uniform(-65, -25), 1),
                "bandwidth_mbps": round(random.uniform(1000, 5000), 1),
                "vibration_mm_s": round(random.uniform(0.02, 0.2), 2),
                "power_kwh": round(random.uniform(2, 8), 1),
                "optical_power_dbm": round(random.uniform(-15, -5), 1),
                "link_quality_pct": round(random.uniform(90, 99.9), 1)
            }
        elif asset_type == 'antenna':
            return {
                "temperature_c": round(random.uniform(20, 40), 1),
                "signal_strength_dbm": round(random.uniform(-90, -50), 1),
                "bandwidth_mbps": round(random.uniform(50, 300), 1),
                "vibration_mm_s": round(random.uniform(0.1, 1.0), 2),
                "power_kwh": round(random.uniform(1, 5), 1),
                "gain_dbi": round(random.uniform(12, 20), 1),
                "vswr": round(random.uniform(1.1, 1.5), 2)
            }
        elif asset_type == 'service_vehicle':
            return {
                "temperature_c": round(random.uniform(20, 35), 1),
                "signal_strength_dbm": round(random.uniform(-95, -55), 1),
                "bandwidth_mbps": round(random.uniform(10, 100), 1),
                "vibration_mm_s": round(random.uniform(0.5, 2.0), 2),
                "power_kwh": round(random.uniform(5, 20), 1),
                "fuel_level_pct": round(random.uniform(30, 90), 1),
                "operating_hours": round(random.uniform(100, 2000), 0)
            }
        elif asset_type == 'repeater':
            return {
                "temperature_c": round(random.uniform(25, 45), 1),
                "signal_strength_dbm": round(random.uniform(-85, -45), 1),
                "bandwidth_mbps": round(random.uniform(50, 250), 1),
                "vibration_mm_s": round(random.uniform(0.05, 0.3), 2),
                "power_kwh": round(random.uniform(1, 6), 1),
                "amplification_db": round(random.uniform(15, 30), 1)
            }
        else:
            # Default metrics for unknown asset types
            return {
                "temperature_c": round(random.uniform(25, 45), 1),
                "signal_strength_dbm": round(random.uniform(-85, -45), 1),
                "bandwidth_mbps": round(random.uniform(100, 500), 1),
                "vibration_mm_s": round(random.uniform(0.1, 0.5), 2),
                "power_kwh": round(random.uniform(2.0, 8.0), 1)
            }
    
    def simulate_asset_movement(self):
        """Simulate asset movement (mainly service vehicles)"""
        while True:
            try:
                # Only move service vehicles and some equipment
                mobile_assets = [aid for aid, asset in self.assets.items()
                               if asset['type'] in ['service_vehicle', 'router']]
                
                for asset_id in mobile_assets:
                    asset = self.assets[asset_id]

                    # Small random movement
                    lat_delta = random.uniform(-0.01, 0.01)  # ~1km
                    lon_delta = random.uniform(-0.01, 0.01)

                    new_lat = float(asset['latitude']) + lat_delta
                    new_lon = float(asset['longitude']) + lon_delta

                    # Update asset location
                    asset['latitude'] = str(new_lat)
                    asset['longitude'] = str(new_lon)
                    asset['last_update'] = datetime.now().isoformat()

                    # Update in Redis
                    redis_client.geoadd('telcom:assets:locations', (new_lon, new_lat, asset_id))
                    # Update JSON document with new location
                    redis_client.execute_command('JSON.SET', f'telcom:asset:{asset_id}', '.latitude', json.dumps(str(new_lat)))
                    redis_client.execute_command('JSON.SET', f'telcom:asset:{asset_id}', '.longitude', json.dumps(str(new_lon)))
                    redis_client.execute_command('JSON.SET', f'telcom:asset:{asset_id}', '.last_update', json.dumps(datetime.now().isoformat()))
                
                time.sleep(30)  # Update every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in asset movement simulation: {e}")
                time.sleep(5)

# ============================================================================
# SENSOR DATA SIMULATION
# ============================================================================

class SensorSimulator:
    def __init__(self):
        self.sensors = {
            'TEMP-001': {'type': 'temperature', 'location': 'RIG-ALPHA', 'base_value': 85},
            'TEMP-002': {'type': 'temperature', 'location': 'RIG-BRAVO', 'base_value': 78},
            'PRESS-001': {'type': 'pressure', 'location': 'WELL-001', 'base_value': 2500},
            'PRESS-002': {'type': 'pressure', 'location': 'WELL-002', 'base_value': 2800},
            'FLOW-001': {'type': 'flow_rate', 'location': 'PUMP-001', 'base_value': 150},
            'FLOW-002': {'type': 'flow_rate', 'location': 'PUMP-002', 'base_value': 180},
            'VIB-001': {'type': 'vibration', 'location': 'COMP-001', 'base_value': 2.5},
            'VIB-002': {'type': 'vibration', 'location': 'SEP-001', 'base_value': 1.8},
        }
    
    def generate_sensor_reading(self, sensor_id, sensor_config):
        """Generate realistic sensor reading"""
        base_value = sensor_config['base_value']
        sensor_type = sensor_config['type']
        
        # Add realistic variations
        if sensor_type == 'temperature':
            # Temperature in Fahrenheit, varies ±10°F
            value = base_value + random.uniform(-10, 10)
        elif sensor_type == 'pressure':
            # Pressure in PSI, varies ±200 PSI
            value = base_value + random.uniform(-200, 200)
        elif sensor_type == 'flow_rate':
            # Flow rate in barrels/day, varies ±20
            value = max(0, base_value + random.uniform(-20, 20))
        elif sensor_type == 'vibration':
            # Vibration in mm/s, varies ±0.5
            value = max(0, base_value + random.uniform(-0.5, 0.5))
        else:
            value = base_value + random.uniform(-base_value*0.1, base_value*0.1)
        
        return round(value, 2)
    
    def simulate_sensor_data(self):
        """Continuously generate sensor data"""
        while True:
            try:
                for sensor_id, config in self.sensors.items():
                    # Generate reading
                    reading = {
                        'sensor_id': sensor_id,
                        'timestamp': str(time.time()),
                        'temperature': str(self.generate_sensor_reading(sensor_id, config) if config['type'] == 'temperature' else 0),
                        'pressure': str(self.generate_sensor_reading(sensor_id, config) if config['type'] == 'pressure' else 0),
                        'flow_rate': str(self.generate_sensor_reading(sensor_id, config) if config['type'] == 'flow_rate' else 0),
                        'vibration': str(self.generate_sensor_reading(sensor_id, config) if config['type'] == 'vibration' else 0),
                        'location': config['location']
                    }
                    
                    # Add to Redis Stream
                    stream_key = f'telcom:sensors:{sensor_id}'
                    redis_client.xadd(stream_key, reading)

                    # Update latest reading
                    redis_client.hset(f'telcom:sensor:latest:{sensor_id}', mapping=reading)
                    
                    # Check for alerts
                    self.check_alerts(sensor_id, reading)

                # Generate system alerts occasionally
                self.generate_system_alerts()

                time.sleep(5)  # Generate data every 5 seconds
                
            except Exception as e:
                logger.error(f"Error in sensor simulation: {e}")
                time.sleep(5)
    
    def check_alerts(self, sensor_id, reading):
        """Check for alert conditions"""
        alerts = []

        # Convert string values back to float for comparison
        temp = float(reading['temperature'])
        pressure = float(reading['pressure'])
        vibration = float(reading['vibration'])
        flow_rate = float(reading['flow_rate']) if reading['flow_rate'] != '0' else None

        # Get asset location for this sensor
        location = reading.get('location', 'UNKNOWN')

        # Temperature alerts
        if temp > 95:  # Lowered threshold to generate more alerts
            severity = 'critical' if temp > 110 else ('high' if temp > 105 else 'warning')
            alerts.append({
                'id': f'TEMP_HIGH_{sensor_id}_{int(time.time())}',
                'type': 'temperature_high',
                'message': f'High Temperature Detected',
                'details': f'{temp:.1f}°F exceeds normal operating range',
                'location': location,
                'sensor_id': sensor_id,
                'severity': severity,
                'timestamp': time.time()
            })

        # Pressure alerts
        if pressure > 2800:  # Lowered threshold to generate more alerts
            severity = 'critical' if pressure > 3200 else ('high' if pressure > 3000 else 'warning')
            alerts.append({
                'id': f'PRESS_HIGH_{sensor_id}_{int(time.time())}',
                'type': 'pressure_high',
                'message': f'Pressure Threshold Exceeded',
                'details': f'{pressure:.0f} PSI above safe operating limits',
                'location': location,
                'sensor_id': sensor_id,
                'severity': severity,
                'timestamp': time.time()
            })

        # Vibration alerts
        if vibration > 2.5:  # New vibration alert
            severity = 'critical' if vibration > 4.0 else ('high' if vibration > 3.0 else 'warning')
            alerts.append({
                'id': f'VIB_HIGH_{sensor_id}_{int(time.time())}',
                'type': 'vibration_high',
                'message': f'Excessive Vibration Detected',
                'details': f'{vibration:.1f} mm/s indicates potential equipment issue',
                'location': location,
                'sensor_id': sensor_id,
                'severity': severity,
                'timestamp': time.time()
            })

        # Flow rate alerts (low flow) - only for flow sensors
        if flow_rate is not None and flow_rate < 15:  # New low flow alert
            severity = 'high' if flow_rate < 10 else 'warning'
            alerts.append({
                'id': f'FLOW_LOW_{sensor_id}_{int(time.time())}',
                'type': 'flow_low',
                'message': f'Low Flow Rate Alert',
                'details': f'{flow_rate:.1f} GPM below expected production levels',
                'location': location,
                'sensor_id': sensor_id,
                'severity': severity,
                'timestamp': time.time()
            })

        # Add alerts to Redis
        for alert in alerts:
            redis_client.zadd('telcom:alerts:active', {json.dumps(alert): alert['timestamp']})
            redis_client.incr('telcom:alerts:count')
            logger.info(f"Generated alert: {alert['message']} at {alert['location']}")

        # Clean up old alerts (keep only last 50)
        redis_client.zremrangebyrank('telcom:alerts:active', 0, -51)

    def generate_system_alerts(self):
        """Generate periodic system-level alerts"""
        try:
            # Generate system alerts every 30-60 seconds
            if random.random() < 0.3:  # 30% chance each cycle
                alert_types = [
                    {
                        'type': 'maintenance_due',
                        'message': 'Scheduled Maintenance Due',
                        'details': 'Preventive maintenance window approaching',
                        'severity': 'warning'
                    },
                    {
                        'type': 'communication_issue',
                        'message': 'Communication Timeout',
                        'details': 'Intermittent connection to remote sensors',
                        'severity': 'warning'
                    },
                    {
                        'type': 'production_anomaly',
                        'message': 'Production Rate Anomaly',
                        'details': 'Output variance detected across multiple wells',
                        'severity': 'high'
                    },
                    {
                        'type': 'weather_warning',
                        'message': 'Weather Advisory',
                        'details': 'High winds forecasted - secure equipment',
                        'severity': 'warning'
                    }
                ]

                alert_info = random.choice(alert_types)
                location = random.choice(['FIELD-NORTH', 'FIELD-SOUTH', 'FIELD-CENTRAL', 'OPERATIONS-HQ'])

                alert = {
                    'id': f'SYS_{alert_info["type"].upper()}_{int(time.time())}',
                    'type': alert_info['type'],
                    'message': alert_info['message'],
                    'details': alert_info['details'],
                    'location': location,
                    'sensor_id': 'SYSTEM',
                    'severity': alert_info['severity'],
                    'timestamp': time.time()
                }

                redis_client.zadd('telcom:alerts:active', {json.dumps(alert): alert['timestamp']})
                redis_client.incr('telcom:alerts:count')
                logger.info(f"Generated system alert: {alert['message']} at {alert['location']}")

        except Exception as e:
            logger.error(f"Error generating system alerts: {e}")

# ============================================================================
# DASHBOARD METRICS SIMULATION
# ============================================================================

class MetricsSimulator:
    def __init__(self):
        pass
    
    def update_dashboard_metrics(self):
        """Update dashboard KPIs"""
        while True:
            try:
                # Calculate metrics from sensor data
                sensor_keys = redis_client.keys('telcom:sensor:latest:*')
                
                total_temp = 0
                total_pressure = 0
                temp_count = 0
                pressure_count = 0
                
                for key in sensor_keys:
                    data = redis_client.hgetall(key)
                    if data.get('temperature'):
                        total_temp += float(data['temperature'])
                        temp_count += 1
                    if data.get('pressure'):
                        total_pressure += float(data['pressure'])
                        pressure_count += 1
                
                # Update averages
                if temp_count > 0:
                    redis_client.set('telcom:metrics:avg_temperature', round(total_temp / temp_count, 1))
                if pressure_count > 0:
                    redis_client.set('telcom:metrics:avg_pressure', round(total_pressure / pressure_count, 1))

                # Simulate production metrics
                redis_client.set('telcom:metrics:total_production', random.randint(8500, 9500))
                redis_client.set('telcom:system:uptime', int(time.time()))
                
                time.sleep(10)  # Update every 10 seconds
                
            except Exception as e:
                logger.error(f"Error updating metrics: {e}")
                time.sleep(10)

# ============================================================================
# MAIN SIMULATION CONTROLLER
# ============================================================================

def main():
    """Start all simulators"""
    logger.info("🚀 Starting AT&T Network Operations Data Simulator")

    try:
        # Test Redis connection
        redis_client.ping()
        logger.info("✅ Connected to Redis Enterprise")
    except Exception as e:
        logger.error(f"❌ Failed to connect to Redis: {e}")
        return
    
    # Initialize simulators
    asset_sim = AssetSimulator()
    sensor_sim = SensorSimulator()
    metrics_sim = MetricsSimulator()
    
    # Start simulation threads
    threads = [
        threading.Thread(target=asset_sim.simulate_asset_movement, daemon=True),
        threading.Thread(target=sensor_sim.simulate_sensor_data, daemon=True),
        threading.Thread(target=metrics_sim.update_dashboard_metrics, daemon=True)
    ]
    
    for thread in threads:
        thread.start()
    
    logger.info("✅ All simulators started")
    logger.info("📊 Generating realistic network telemetry data...")
    logger.info("🔄 Press Ctrl+C to stop")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("🛑 Stopping simulators...")

if __name__ == '__main__':
    main()
