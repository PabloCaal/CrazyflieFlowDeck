"""
Script de Python con la librería Cflib de Bitcraze y funciones básicas 
para el control de los drones Crazyflie. Esto forma parte del trabajo de 
graduación titulado "Desarrollo de herramientas de software para el 
control individual y seguro del cuadricóptero Crazyflie 2.1 utilizando 
la placa de expansión de posicionamiento con odometría visual Flow
Deck".
"""
 
import logging
import sys
import time
from threading import Event

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.positioning.motion_commander import MotionCommander
from cflib.crazyflie.high_level_commander import HighLevelCommander

cflib.crtp.init_drivers(enable_debug_driver=False)

logging.basicConfig(level=logging.CRITICAL)
   
def error_callback(error):
    print(f"Link error: {error}")

def connect(uri):
    try:
        # Attempt to create a SyncCrazyflie instance and open a link to the Crazyflie
        scf = SyncCrazyflie(uri, cf=Crazyflie(rw_cache='./cache'))
        scf.open_link()
        return scf
    
    except Exception as e:
        # Handle specific error cases and return a corresponding numeric code
        if 'Cannot find a Crazyradio Dongle' in str(e):
            return 1  # Error code 1: Crazyradio Dongle not found
        elif 'Connection refused' in str(e):
            return 2  # Error code 2: Connection refused
        elif 'Timeout' in str(e):
            return 3  # Error code 3: Connection timed out
        else:
            return 0  # Error code 0: General error


def disconnect_crazyflie(scf):
    scf.close_link()

def takeoff(scf, height, duration):
    commander = HighLevelCommander(scf.cf)
    commander.takeoff(absolute_height_m=height, duration_s=duration)
    time.sleep(duration) 
    return True

def takeoff2(scf, height, velocity):
    with MotionCommander(scf) as mc:
        mc.move_distance(0, 0, height, velocity)
    return True

def land(scf, height, duration):
    commander = HighLevelCommander(scf.cf)
    commander.land(absolute_height_m=height, duration_s=duration)

    time.sleep(duration)

    commander.stop()
    return True

def send_position(scf, x, y, z):
    commander = scf.cf.high_level_commander
    commander.go_to(x, y, z, 0.0, 3.0)  
    time.sleep(1) 
    return True

def send_position_2(scf, x, y, z, duration):
    commander = scf.cf.high_level_commander
    commander.go_to(x, y, z, 0.0, duration)  
    time.sleep(duration) 
    return True

def get_position(scf):
    position_log_config = LogConfig(name='Position', period_in_ms=100)
    position_log_config.add_variable('stateEstimate.x', 'float')
    position_log_config.add_variable('stateEstimate.y', 'float')
    position_log_config.add_variable('stateEstimate.z', 'float')

    position = {'x': 0.0, 'y': 0.0, 'z': 0.0}
    new_data = Event()

    def position_callback(timestamp, data, logconf):
        position['x'] = data['stateEstimate.x']
        position['y'] = data['stateEstimate.y']
        position['z'] = data['stateEstimate.z']
        new_data.set()

    position_log_config.data_received_cb.add_callback(position_callback)

    try:
        existing_configs = scf.cf.log.log_blocks
        for config in existing_configs:
            if config.name == 'Position':
                config.stop()
                config.delete()
    except AttributeError:
        pass  

    scf.cf.log.add_config(position_log_config)
    position_log_config.start()
    new_data.wait()
    position_log_config.stop()

    return [position['x'], position['y'], position['z']]

def update_position(scf, x, y, z):
    scf.cf.extpos.send_extpos(x, y, z)
    time.sleep(0.1) 
    return True


# No funciona:
def move_to(scf, x, y, z, velocity):
    """
    Move the Crazyflie to the specified position (x, y, z) using MotionCommander.
    
    Parameters:
    scf (SyncCrazyflie): The SyncCrazyflie object representing the connection to the Crazyflie.
    x (float): The target x-coordinate in meters.
    y (float): The target y-coordinate in meters.
    z (float): The target z-coordinate in meters.
    velocity (float): The velocity of the movement in meters per second (default is 0.5 m/s).
    
    Returns:
    int: A numeric code indicating the result of the position command.
         0 - Successful position command
         1 - Invalid position or velocity parameters
         2 - General error occurred during movement
    """
    try:
        # Validate input parameters
        if not all(isinstance(coord, (int, float)) for coord in [x, y, z]) or velocity <= 0.0:
            return 1  # Error code 1: Invalid input parameters

        # Use MotionCommander to move to the specified position
        with MotionCommander(scf) as mc:
            mc.move_distance(x, y, z, velocity)

        return 0  # Success: Position command completed successfully

    except Exception as e:
        # Handle any unexpected errors during the position command
        print(f"ERROR: An error occurred during the position command: {str(e)}")
        return 2  # Error code 2: General error