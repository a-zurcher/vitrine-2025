import asyncio
from enum import Enum
import logging

import fastapi

import pyads


app = fastapi.FastAPI()
logger = logging.getLogger(__name__)

# ===============
# PLC CONFIG & HELPERS
# ===============
class OffsetKey(Enum):
    BUILDING_1 = 0x138
    BUILDING_2 = 0x139
    BUILDING_3 = 0x13A
    BUILDING_4 = 0x13B
    CELEBRATE = 0x13C
    CLEAN_BUILDINGS = 0x13D

def write_output(value: bool, index_group: int = 0xF021, index_offset: int = 0x138) -> bool:
    """Writes a boolean to the output symbol and returns the readback."""
    ams_net_id = "5.98.172.87.1.1"
    ams_port = 27905

    with pyads.Connection(ams_net_id, ams_port) as plc:
        symbol = plc.get_symbol(
            index_group=index_group,
            index_offset=index_offset,
            plc_datatype=pyads.PLCTYPE_BOOL,
        )

        symbol.write(value)
        return symbol.read()

def activate_only(target: OffsetKey):
    """Stop idle and activate the target output."""
    idle_stop_event.set()  # stop idle loop immediately
    for key in OffsetKey:
        write_output(key == target, index_offset=key.value)
    return {"led_status": True}



# ===============
# IDLE MANAGEMENT
# ===============
idle_stop_event = asyncio.Event()
idle_started = False

async def idle_loop():
    """Continuously turns off all outputs until stopped."""
    global idle_started

    if not idle_stop_event.is_set(): logger.warning("Idle state - action started")

    while not idle_stop_event.is_set():
        logger.warning("Idle state - action triggered")

        for key in OffsetKey:
            write_output(False, index_offset=key.value)
        await asyncio.sleep(1)  # small sleep to avoid blocking the event loop

    logger.warning("Idle state - stopped")
    idle_started = False  # allow it to be started again if needed




# ===============
# MIDDLEWARE
# ===============
@app.middleware("http")
async def stop_idle_for_other_endpoints(request: fastapi.Request, call_next):
    """Stops the idle loop for ANY endpoint except /idle."""
    if request.url.path != "/idle":
        idle_stop_event.set()
    response = await call_next(request)
    return response



# ===============
# ROUTES
# ===============
@app.get("/idle")
async def idle(background_tasks: fastapi.BackgroundTasks):
    """Start idle loop in background (can only run once)."""
    global idle_started

    if idle_started: return { "status": "idle already running" }

    idle_started = True
    idle_stop_event.clear()
    background_tasks.add_task(idle_loop)

    return { "status": "idle started" }


@app.get("/place-building-1")
def place_building_1():
    return activate_only(OffsetKey.BUILDING_1)


@app.get("/place-building-2")
def place_building_2():
    return activate_only(OffsetKey.BUILDING_2)


@app.get("/place-building-3")
def place_building_3():
    return activate_only(OffsetKey.BUILDING_3)


@app.get("/place-building-4")
def place_building_4():
    return activate_only(OffsetKey.BUILDING_4)


@app.get("/celebrate")
def celebrate():
    return activate_only(OffsetKey.CELEBRATE)


@app.get("/clean-buildings")
def clean_buildings():
    return activate_only(OffsetKey.CLEAN_BUILDINGS)