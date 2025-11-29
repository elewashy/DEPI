#!/usr/bin/env python3
"""
Smart City Real-time Data Producer
Simulates API data for all Smart City IoT sensors and sends to Kafka
Generates data matching the SmartCity database schema
"""

import json
import time
import random
from datetime import datetime, timedelta
from kafka import KafkaProducer
from kafka.errors import KafkaError
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
KAFKA_BROKER = 'kafka:9092'
BATCH_SIZE = 5
DELAY_SECONDS = 2

# Kafka Topics
TOPICS = {
    'energy': 'energy',
    'traffic': 'traffic',
    'bus_gps': 'bus_gps',
    'waste': 'waste',
    'emergency': 'emergency'
}

# ========================
# Reference Data (Dimension Tables)
# ========================

# Zones (10 zones in the city)
ZONES = [
    {"zone_id": "Z001", "zone_name": "Downtown", "lat_min": 40.7100, "lat_max": 40.7200, "lon_min": -74.0100, "lon_max": -74.0000},
    {"zone_id": "Z002", "zone_name": "Midtown", "lat_min": 40.7200, "lat_max": 40.7300, "lon_min": -74.0000, "lon_max": -73.9900},
    {"zone_id": "Z003", "zone_name": "Uptown", "lat_min": 40.7300, "lat_max": 40.7400, "lon_min": -73.9900, "lon_max": -73.9800},
    {"zone_id": "Z004", "zone_name": "Eastside", "lat_min": 40.7150, "lat_max": 40.7250, "lon_min": -73.9800, "lon_max": -73.9700},
    {"zone_id": "Z005", "zone_name": "Westside", "lat_min": 40.7150, "lat_max": 40.7250, "lon_min": -74.0200, "lon_max": -74.0100},
    {"zone_id": "Z006", "zone_name": "Industrial", "lat_min": 40.7000, "lat_max": 40.7100, "lon_min": -74.0200, "lon_max": -74.0100},
    {"zone_id": "Z007", "zone_name": "Residential North", "lat_min": 40.7400, "lat_max": 40.7500, "lon_min": -73.9950, "lon_max": -73.9850},
    {"zone_id": "Z008", "zone_name": "Residential South", "lat_min": 40.7000, "lat_max": 40.7100, "lon_min": -73.9950, "lon_max": -73.9850},
    {"zone_id": "Z009", "zone_name": "Commercial Hub", "lat_min": 40.7250, "lat_max": 40.7350, "lon_min": -74.0050, "lon_max": -73.9950},
    {"zone_id": "Z010", "zone_name": "Tech Park", "lat_min": 40.7350, "lat_max": 40.7450, "lon_min": -74.0100, "lon_max": -74.0000}
]

# Buildings (20 buildings across zones)
BUILDINGS = [
    {"building_id": "B001", "building_name": "City Hall", "zone_id": "Z001", "building_type": "Government", "status": "Active"},
    {"building_id": "B002", "building_name": "Central Mall", "zone_id": "Z001", "building_type": "Commercial", "status": "Active"},
    {"building_id": "B003", "building_name": "Tech Tower", "zone_id": "Z010", "building_type": "Office", "status": "Active"},
    {"building_id": "B004", "building_name": "Green Apartments", "zone_id": "Z007", "building_type": "Residential", "status": "Active"},
    {"building_id": "B005", "building_name": "Hospital Central", "zone_id": "Z002", "building_type": "Healthcare", "status": "Active"},
    {"building_id": "B006", "building_name": "University Main", "zone_id": "Z003", "building_type": "Education", "status": "Active"},
    {"building_id": "B007", "building_name": "Factory Alpha", "zone_id": "Z006", "building_type": "Industrial", "status": "Active"},
    {"building_id": "B008", "building_name": "Sports Arena", "zone_id": "Z004", "building_type": "Recreation", "status": "Active"},
    {"building_id": "B009", "building_name": "Business Center", "zone_id": "Z009", "building_type": "Office", "status": "Active"},
    {"building_id": "B010", "building_name": "Sunset Towers", "zone_id": "Z008", "building_type": "Residential", "status": "Active"},
    {"building_id": "B011", "building_name": "Data Center", "zone_id": "Z010", "building_type": "Technology", "status": "Active"},
    {"building_id": "B012", "building_name": "Police Station", "zone_id": "Z001", "building_type": "Government", "status": "Active"},
    {"building_id": "B013", "building_name": "Fire Station", "zone_id": "Z002", "building_type": "Emergency", "status": "Active"},
    {"building_id": "B014", "building_name": "School District HQ", "zone_id": "Z003", "building_type": "Education", "status": "Active"},
    {"building_id": "B015", "building_name": "Warehouse Complex", "zone_id": "Z006", "building_type": "Industrial", "status": "Active"},
    {"building_id": "B016", "building_name": "Retail Plaza", "zone_id": "Z009", "building_type": "Commercial", "status": "Active"},
    {"building_id": "B017", "building_name": "Luxury Condos", "zone_id": "Z005", "building_type": "Residential", "status": "Active"},
    {"building_id": "B018", "building_name": "Convention Center", "zone_id": "Z004", "building_type": "Event", "status": "Active"},
    {"building_id": "B019", "building_name": "Research Lab", "zone_id": "Z010", "building_type": "Technology", "status": "Active"},
    {"building_id": "B020", "building_name": "Transit Hub", "zone_id": "Z001", "building_type": "Transportation", "status": "Active"}
]

# Devices (Smart meters, traffic sensors, etc.)
DEVICES = []
device_types = ["SmartMeter", "TrafficSensor", "EnvironmentSensor", "SecurityCamera"]
manufacturers = ["Siemens", "ABB", "Schneider", "GE", "Honeywell"]
for i in range(1, 51):
    DEVICES.append({
        "device_id": f"D{i:03d}",
        "device_type": random.choice(device_types),
        "building_id": random.choice(BUILDINGS)["building_id"],
        "manufacturer": random.choice(manufacturers),
        "status": "Active"
    })

# Trucks for waste collection
TRUCKS = [
    {"truck_id": "T001", "truck_type": "Compactor", "capacity_tons": 10, "fuel_type": "Diesel", "status": "Active"},
    {"truck_id": "T002", "truck_type": "Recycling", "capacity_tons": 8, "fuel_type": "Electric", "status": "Active"},
    {"truck_id": "T003", "truck_type": "Compactor", "capacity_tons": 12, "fuel_type": "Hybrid", "status": "Active"},
    {"truck_id": "T004", "truck_type": "Organic", "capacity_tons": 6, "fuel_type": "CNG", "status": "Active"},
    {"truck_id": "T005", "truck_type": "Hazardous", "capacity_tons": 5, "fuel_type": "Diesel", "status": "Active"},
    {"truck_id": "T006", "truck_type": "Compactor", "capacity_tons": 10, "fuel_type": "Electric", "status": "Active"},
    {"truck_id": "T007", "truck_type": "Recycling", "capacity_tons": 8, "fuel_type": "Diesel", "status": "Active"},
    {"truck_id": "T008", "truck_type": "Compactor", "capacity_tons": 14, "fuel_type": "Hybrid", "status": "Active"}
]

# Bus Routes
BUS_ROUTES = [
    {"route_id": "R001", "route_name": "Downtown Express", "start_point": "Transit Hub", "end_point": "Uptown Terminal", "distance_km": 15.5, "active_status": "Active"},
    {"route_id": "R002", "route_name": "East-West Line", "start_point": "Eastside Station", "end_point": "Westside Plaza", "distance_km": 12.3, "active_status": "Active"},
    {"route_id": "R003", "route_name": "Industrial Route", "start_point": "Transit Hub", "end_point": "Industrial Park", "distance_km": 8.7, "active_status": "Active"},
    {"route_id": "R004", "route_name": "Campus Shuttle", "start_point": "University Main", "end_point": "Tech Park", "distance_km": 5.2, "active_status": "Active"},
    {"route_id": "R005", "route_name": "Hospital Line", "start_point": "Downtown", "end_point": "Hospital Central", "distance_km": 6.8, "active_status": "Active"},
    {"route_id": "R006", "route_name": "Residential Loop", "start_point": "Transit Hub", "end_point": "Residential North", "distance_km": 18.4, "active_status": "Active"},
    {"route_id": "R007", "route_name": "Commercial Circuit", "start_point": "Central Mall", "end_point": "Retail Plaza", "distance_km": 9.1, "active_status": "Active"},
    {"route_id": "R008", "route_name": "Night Owl", "start_point": "Transit Hub", "end_point": "Entertainment District", "distance_km": 11.2, "active_status": "Active"}
]

# Buses
BUSES = [f"BUS{i:03d}" for i in range(1, 21)]

# Containers for waste
CONTAINERS = [f"C{i:03d}" for i in range(1, 101)]

# Event Types
EVENT_TYPES = [
    {"event_type_id": "E001", "event_type_name": "Fire", "description": "Fire emergency"},
    {"event_type_id": "E002", "event_type_name": "Medical", "description": "Medical emergency"},
    {"event_type_id": "E003", "event_type_name": "Traffic Accident", "description": "Vehicle collision"},
    {"event_type_id": "E004", "event_type_name": "Crime", "description": "Criminal activity"},
    {"event_type_id": "E005", "event_type_name": "Utility Failure", "description": "Power/water outage"},
    {"event_type_id": "E006", "event_type_name": "Natural Disaster", "description": "Weather emergency"},
    {"event_type_id": "E007", "event_type_name": "Public Disturbance", "description": "Crowd control"},
    {"event_type_id": "E008", "event_type_name": "Infrastructure", "description": "Building/road issue"}
]

PRIORITY_LEVELS = ["Critical", "High", "Medium", "Low"]


def get_date_key():
    """Generate date_key in YYYYMMDD format"""
    return int(datetime.now().strftime("%Y%m%d"))


def get_time_key():
    """Generate time_key in HHMMSS format"""
    return datetime.now().strftime("%H%M%S")


def get_zone_coords(zone_id):
    """Get random coordinates within a zone"""
    zone = next((z for z in ZONES if z["zone_id"] == zone_id), ZONES[0])
    lat = round(random.uniform(zone["lat_min"], zone["lat_max"]), 6)
    lon = round(random.uniform(zone["lon_min"], zone["lon_max"]), 6)
    return lat, lon


# ========================
# Data Generators
# ========================

def generate_energy_consumption():
    """Generate energy consumption data"""
    now = datetime.now()
    hour = now.hour
    
    # Simulate realistic patterns based on time
    if 8 <= hour <= 18:  # Business hours
        base_kwh = random.uniform(5.0, 20.0)
    elif 18 <= hour <= 22:  # Evening peak
        base_kwh = random.uniform(8.0, 25.0)
    else:  # Night
        base_kwh = random.uniform(1.0, 8.0)
    
    building = random.choice(BUILDINGS)
    device = random.choice([d for d in DEVICES if d["device_type"] == "SmartMeter"] or DEVICES)
    
    # Add building type variations
    multiplier = {
        "Industrial": 3.0,
        "Commercial": 2.0,
        "Healthcare": 2.5,
        "Office": 1.5,
        "Residential": 1.0,
        "Technology": 2.8,
        "Education": 1.3
    }.get(building["building_type"], 1.0)
    
    kwh = round(base_kwh * multiplier, 4)
    voltage = round(random.gauss(230.0, 5.0), 2)
    current = round(kwh * 1000 / voltage / 240 if voltage > 0 else 0, 4)  # Approximate
    
    # Add anomalies occasionally (5% chance)
    if random.random() < 0.05:
        kwh = round(kwh * random.uniform(2.5, 4.0), 4)  # Spike
        
    quality_flag = "GOOD" if 210 <= voltage <= 250 else "WARNING"
    
    return {
        "date_key": get_date_key(),
        "time_key": get_time_key(),
        "building_id": building["building_id"],
        "device_id": device["device_id"],
        "kwh": kwh,
        "voltage": voltage,
        "current": current,
        "quality_flag": quality_flag,
        "timestamp": datetime.utcnow().isoformat()
    }


def generate_traffic():
    """Generate traffic sensor data"""
    now = datetime.now()
    hour = now.hour
    
    zone = random.choice(ZONES)
    device = random.choice([d for d in DEVICES if d["device_type"] == "TrafficSensor"] or DEVICES)
    
    # Traffic patterns by time
    if 7 <= hour <= 9 or 17 <= hour <= 19:  # Rush hours
        vehicle_count = random.randint(80, 150)
        avg_speed = round(random.uniform(15.0, 35.0), 2)
    elif 10 <= hour <= 16:  # Midday
        vehicle_count = random.randint(40, 90)
        avg_speed = round(random.uniform(35.0, 55.0), 2)
    elif 20 <= hour <= 23:  # Evening
        vehicle_count = random.randint(30, 70)
        avg_speed = round(random.uniform(40.0, 60.0), 2)
    else:  # Night
        vehicle_count = random.randint(5, 30)
        avg_speed = round(random.uniform(50.0, 70.0), 2)
    
    # Zone-based adjustments
    if zone["zone_name"] in ["Downtown", "Commercial Hub"]:
        vehicle_count = int(vehicle_count * 1.3)
        avg_speed = avg_speed * 0.8
    elif zone["zone_name"] in ["Industrial", "Tech Park"]:
        vehicle_count = int(vehicle_count * 0.7)
        avg_speed = avg_speed * 1.1
    
    return {
        "date_key": get_date_key(),
        "time_key": get_time_key(),
        "zone_id": zone["zone_id"],
        "device_id": device["device_id"],
        "vehicle_count": vehicle_count,
        "avg_speed_kmh": round(avg_speed, 2),
        "timestamp": datetime.utcnow().isoformat()
    }


def generate_bus_gps():
    """Generate bus GPS tracking data"""
    bus_id = random.choice(BUSES)
    route = random.choice(BUS_ROUTES)
    zone = random.choice(ZONES)
    lat, lon = get_zone_coords(zone["zone_id"])
    
    hour = datetime.now().hour
    # Speed varies by time
    if 7 <= hour <= 9 or 17 <= hour <= 19:
        speed_kmh = round(random.uniform(10.0, 25.0), 2)
    else:
        speed_kmh = round(random.uniform(25.0, 45.0), 2)
    
    # Occupancy estimation
    if 7 <= hour <= 9:  # Morning rush
        occupancy_est = random.randint(50, 100)
    elif 17 <= hour <= 19:  # Evening rush
        occupancy_est = random.randint(60, 100)
    elif 10 <= hour <= 16:  # Midday
        occupancy_est = random.randint(20, 60)
    else:
        occupancy_est = random.randint(5, 30)
    
    return {
        "date_key": get_date_key(),
        "time_key": get_time_key(),
        "bus_id": bus_id,
        "route_id": route["route_id"],
        "zone_id": zone["zone_id"],
        "lat": lat,
        "lon": lon,
        "speed_kmh": speed_kmh,
        "occupancy_est": occupancy_est,
        "timestamp": datetime.utcnow().isoformat()
    }


def generate_waste():
    """Generate waste collection data"""
    zone = random.choice(ZONES)
    building = random.choice([b for b in BUILDINGS if b["zone_id"] == zone["zone_id"]] or BUILDINGS)
    container_id = random.choice(CONTAINERS)
    truck = random.choice(TRUCKS)
    
    hour = datetime.now().hour
    day_of_week = datetime.now().weekday()
    
    # Fill level simulation - increases during day, resets after collection
    base_fill = random.randint(20, 60)
    if 6 <= hour <= 18:
        base_fill += (hour - 6) * 3  # Fills up during day
    
    # Weekend patterns
    if day_of_week >= 5:  # Weekend
        base_fill = int(base_fill * 1.2)
    
    fill_level = min(100, max(0, base_fill + random.randint(-10, 10)))
    
    return {
        "date_key": get_date_key(),
        "time_key": get_time_key(),
        "zone_id": zone["zone_id"],
        "building_id": building["building_id"],
        "container_id": container_id,
        "fill_level_percent": fill_level,
        "truck_id": truck["truck_id"] if fill_level > 80 else None,  # Truck assigned if full
        "timestamp": datetime.utcnow().isoformat()
    }


emergency_counter = 0

def generate_emergency():
    """Generate emergency call data"""
    global emergency_counter
    emergency_counter += 1
    
    zone = random.choice(ZONES)
    building = random.choice([b for b in BUILDINGS if b["zone_id"] == zone["zone_id"]] or BUILDINGS)
    event_type = random.choice(EVENT_TYPES)
    priority = random.choice(PRIORITY_LEVELS)
    
    now = datetime.utcnow()
    reported_at = now
    
    # Response time based on priority
    response_minutes = {
        "Critical": random.randint(3, 10),
        "High": random.randint(8, 20),
        "Medium": random.randint(15, 40),
        "Low": random.randint(30, 90)
    }.get(priority, random.randint(15, 45))
    
    resolved_at = now + timedelta(minutes=response_minutes + random.randint(10, 60))
    
    return {
        "call_id": f"CALL{emergency_counter:06d}",
        "date_key": get_date_key(),
        "time_key": get_time_key(),
        "zone_id": zone["zone_id"],
        "building_id": building["building_id"],
        "event_type_id": event_type["event_type_id"],
        "priority_level": priority,
        "reported_at": reported_at.isoformat(),
        "resolved_at": resolved_at.isoformat(),
        "response_time_minutes": response_minutes,
        "timestamp": datetime.utcnow().isoformat()
    }


def create_producer():
    """Create and configure Kafka producer"""
    max_retries = 10
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            producer = KafkaProducer(
                bootstrap_servers=[KAFKA_BROKER],
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all',
                retries=3,
                max_in_flight_requests_per_connection=1
            )
            logger.info(f"✓ Connected to Kafka broker: {KAFKA_BROKER}")
            return producer
        except Exception as e:
            retry_count += 1
            logger.warning(f"Retry {retry_count}/{max_retries}: {e}")
            time.sleep(5)
    
    raise Exception("Failed to connect to Kafka after maximum retries")


def send_data(producer, topic, data):
    """Send data to Kafka topic"""
    try:
        future = producer.send(topic, value=data)
        future.get(timeout=10)
        return True
    except KafkaError as e:
        logger.error(f"Failed to send to {topic}: {e}")
        return False


def main():
    """Main producer loop"""
    logger.info("=" * 80)
    logger.info("🏙️  Smart City Real-time Data Producer")
    logger.info("=" * 80)
    logger.info(f"Kafka Broker: {KAFKA_BROKER}")
    logger.info(f"Topics: {list(TOPICS.values())}")
    logger.info(f"Batch Size: {BATCH_SIZE}, Delay: {DELAY_SECONDS}s")
    logger.info("")
    
    producer = create_producer()
    
    generators = {
        'energy': generate_energy_consumption,
        'traffic': generate_traffic,
        'bus_gps': generate_bus_gps,
        'waste': generate_waste,
        'emergency': generate_emergency
    }
    
    counters = {topic: 0 for topic in TOPICS}
    
    try:
        logger.info("Starting data generation...")
        logger.info("")
        
        while True:
            for topic_name, generator in generators.items():
                for _ in range(BATCH_SIZE):
                    data = generator()
                    if send_data(producer, TOPICS[topic_name], data):
                        counters[topic_name] += 1
            
            producer.flush()
            
            total = sum(counters.values())
            if total % 100 == 0 and total > 0:
                logger.info(f"📊 Messages sent - Energy: {counters['energy']}, Traffic: {counters['traffic']}, "
                          f"Bus GPS: {counters['bus_gps']}, Waste: {counters['waste']}, Emergency: {counters['emergency']}")
            
            time.sleep(DELAY_SECONDS)
            
    except KeyboardInterrupt:
        logger.info("\n⏹️  Shutting down producer...")
    except Exception as e:
        logger.error(f"Error in producer loop: {e}")
    finally:
        producer.close()
        logger.info("")
        logger.info("=" * 80)
        logger.info("Final counts:")
        for topic, count in counters.items():
            logger.info(f"  {topic}: {count:,} messages")
        logger.info(f"  Total: {sum(counters.values()):,} messages")
        logger.info("=" * 80)


if __name__ == "__main__":
    main()
