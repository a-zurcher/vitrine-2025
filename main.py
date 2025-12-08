import random
import time
from enum import Enum
import logging
from typing import Literal
from urllib.request import urlopen

import fastapi

import pyads
from pyads import ADSError

app = fastapi.FastAPI()
logger = logging.getLogger(__name__)

# ===============
# LIGHTS MGMT
# ===============
class Light(Enum):
    BUILDING_1      = "http://172.22.22.11"
    BUILDING_2      = "http://172.22.22.12"
    BUILDING_3      = "http://172.22.22.13"
    BUILDING_4      = "http://172.22.22.14"

def manage_light(action: Literal['On', 'Off', 'TOGGLE'], light: Light):
    urlopen(f"{light.value}/cm?cmnd=Power%20{action}").read()


# ===============
# PLC CONFIG & HELPERS
# ===============
class OffsetKey(Enum):
    BUILDING_1      = 0x138
    BUILDING_2      = 0x139
    BUILDING_3      = 0x13A
    BUILDING_4      = 0x13B
    CELEBRATE       = 0x13C
    CLEAN_BUILDINGS = 0x13D
    IDLE            = 0x13E

def write_output(value: bool, index_group: int = 0xF021, index_offset: int = 0x138):
    """Writes a boolean to the output symbol and returns the readback."""
    ams_net_id = "5.98.172.87.1.1"
    ams_port = 27905

    with pyads.Connection(ams_net_id, ams_port) as plc:
        try:
            symbol = plc.get_symbol(
                index_group=index_group,
                index_offset=index_offset,
                plc_datatype=pyads.PLCTYPE_BOOL,
            )

            symbol.write(value)
            time.sleep(3)
            symbol.write(False)

        except ADSError as e:
            logger.error(f"Error writing output to index group '{index_group} at index offset '{index_offset}': {e}")

def activate_only(target: OffsetKey):
    """Activate the target output."""
    for key in OffsetKey:
        write_output(key == target, index_offset=key.value)

    return {"led_status": True}



def desactivate_only(target: OffsetKey):
    """Desactivate the target output."""
    for key in OffsetKey:
        write_output(key == target, index_offset=key.value)
    return {"led_status": False}




# ===============
# ROUTES
# ===============
@app.get("/place-building-1")
def place_building_1():
    activate_only(OffsetKey.BUILDING_1)
    manage_light('On', Light.BUILDING_1)


@app.get("/place-building-2")
def place_building_2():
    activate_only(OffsetKey.BUILDING_2)
    manage_light('On', Light.BUILDING_2)


@app.get("/place-building-3")
def place_building_3():
    activate_only(OffsetKey.BUILDING_3)
    manage_light('On', Light.BUILDING_3)



@app.get("/place-building-4")
def place_building_4():
    activate_only(OffsetKey.BUILDING_4)
    manage_light('On', Light.BUILDING_4)


@app.get("/celebrate")
def celebrate():
    activate_only(OffsetKey.CELEBRATE)

    # lights animation
    for i in range(3):
        for light in Light:
            manage_light("Off", light)
            time.sleep(0.25)  # stagger by half a second
            manage_light("On", light)

    # reset
    for light in Light: manage_light("On", light)

@app.get("/celebrate-2")
def celebrate_special():
    activate_only(OffsetKey.CELEBRATE)

    # lights animation
    for i in range(20):
        for j in range(len(Light)):
            # get a random light
            light = random.choice(list(Light))
            manage_light("Off", light)
            time.sleep(0.025)  # stagger by half a second
            manage_light("On", light)

    # reset
    for light in Light: manage_light("On", light)

@app.get("/clean-buildings")
def clean_buildings():
    activate_only(OffsetKey.CLEAN_BUILDINGS)
    manage_light('Off', Light.BUILDING_1)
    manage_light('Off', Light.BUILDING_2)
    manage_light('Off', Light.BUILDING_3)
    manage_light('Off', Light.BUILDING_4)

@app.get("/idle")
async def idle():
    """Start the idle loop action, managed by the robot directly"""
    return activate_only(OffsetKey.IDLE)