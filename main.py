import random
import threading
import time
from enum import IntEnum, StrEnum
import logging
from urllib.request import urlopen

import fastapi

import pyads
from fastapi import BackgroundTasks
from pyads import ADSError

app = fastapi.FastAPI()
logger = logging.getLogger(__name__)

app.state.BUILDINGS_PLACED = []
app.state.ROBOT_IS_MOVING = False


# ===============
# LIGHTS MGMT
# ===============
class LightAction(StrEnum):
    On = "On"
    Off = "Off"
    TOGGLE = "TOGGLE"

class Light(StrEnum):
    BUILDING_1      = "http://172.22.22.11"
    BUILDING_2      = "http://172.22.22.12"
    BUILDING_3      = "http://172.22.22.13"
    BUILDING_4      = "http://172.22.22.14"

    @classmethod
    def get_building_from_number(cls, num: int):
        if num not in range(1, 5):
            raise ValueError("Number must be between 1 and 4.")
        return getattr(cls, f"BUILDING_{num}")

def manage_light(action: LightAction, light: Light, blocking: bool = True):
    def callback():
        logger.warning(f"Managing light '{light.name}' with action '{action.value}'")
        urlopen(f"{light.value}/cm?cmnd=Power%20{action.value}").read()

    if blocking:
        callback()
    else:
        thread = threading.Thread(
            target=callback,
            daemon=True
        )
        thread.start()


# ===============
# PLC CONFIG & HELPERS
# ===============
AMS_NET_ID = "5.98.172.87.1.1"
AMS_PORT = 27905
WRITE_INDEX_GROUP = 0xF021
READ_INDEX_GROUP = 0xF031


class ReadOffsetKey(IntEnum):
    ACTION_FINISHED     = 0x1A8


class WriteOffsetKey(IntEnum):
    BUILDING_1          = 0x138
    BUILDING_2          = 0x139
    BUILDING_3          = 0x13A
    BUILDING_4          = 0x13B
    CELEBRATE           = 0x13C
    IDLE                = 0x13E
    CLEAN_BUILDING_1    = 0x13F
    CLEAN_BUILDING_2    = 0x140
    CLEAN_BUILDING_3    = 0x141
    CLEAN_BUILDING_4    = 0x142


    @classmethod
    def get_building_from_number(cls, num: int):
        if num not in range(1, 5):
            raise ValueError("Number must be between 1 and 4.")
        return getattr(cls, f"BUILDING_{num}")

    @classmethod
    def get_clean_buildings_from_number(cls, num: int):
        if num not in range(1, 5):
            raise ValueError("Number must be between 1 and 4.")
        return getattr(cls, f"CLEAN_BUILDING_{num}")


def wait_for_plc_action_to_finish(index_offset: ReadOffsetKey = ReadOffsetKey.ACTION_FINISHED):
    action_is_finished = False

    try:
        with pyads.Connection(AMS_NET_ID, AMS_PORT) as plc:
            symbol = plc.get_symbol(
                index_group=READ_INDEX_GROUP,
                index_offset=index_offset.value,
                plc_datatype=pyads.PLCTYPE_BOOL,
            )

            logger.warning(f"Index group '{READ_INDEX_GROUP}' at index offset '{index_offset.name}' ({index_offset.value}) - waiting for action to finish")

            while not action_is_finished:
                # listen for the action to finish
                action_is_finished = symbol.read()
                time.sleep(0.5)

            logger.warning(f"Index group '{READ_INDEX_GROUP}' at index offset '{index_offset.name}' ({index_offset.value}) - action finished")


    except ADSError as e:
        logger.error(f"Error writing output to index group '{WRITE_INDEX_GROUP} at index offset '{index_offset.name}' ({index_offset.value}): {e}")



def write_output(
        value: bool,
        index_offset: WriteOffsetKey | ReadOffsetKey,
        wait_until_finish: bool = False
):
    """Writes a boolean to the output symbol and returns the readback."""

    try:
        with pyads.Connection(AMS_NET_ID, AMS_PORT) as plc:
            logger.warning(f"Index group '{WRITE_INDEX_GROUP}' at index offset '{index_offset.name}' ({index_offset.value}) - writing output '{value}'")

            symbol = plc.get_symbol(
                index_group=WRITE_INDEX_GROUP,
                index_offset=index_offset.value,
                plc_datatype=pyads.PLCTYPE_BOOL,
            )

            symbol.write(value)

            # if the value was set to 'True', it needs to be reset to 'False' to avoid an infinite loop
            if value:
                if wait_until_finish: wait_for_plc_action_to_finish()
                symbol.write(False)
                logger.warning(f"Index group '{WRITE_INDEX_GROUP}' at index offset '{index_offset.name}' ({index_offset.value}) - writing output 'False'")

    except ADSError as e:
        logger.error(f"Error writing output to index group '{WRITE_INDEX_GROUP} at index offset '{index_offset.name}' ({index_offset.value}): {e}")

def activate_only(target: WriteOffsetKey, wait_until_finish: bool = False):
    """Activate the target output."""
    for key in WriteOffsetKey:
        if key == target:
            write_output(value=True, index_offset=key, wait_until_finish=wait_until_finish)
        else:
            write_output(value=False, index_offset=key)






# ===============
# ROUTES
# ===============
def create_building_route(building_id: int, write_key, light):
    def route(background_tasks: BackgroundTasks):
        if app.state.ROBOT_IS_MOVING:
            logger.warning("The robot is currently moving. Please wait until it finishes.")
            return

        def callback():
            app.state.ROBOT_IS_MOVING = True

            activate_only(write_key, wait_until_finish=True)
            manage_light(LightAction.On, light)
            app.state.BUILDINGS_PLACED.append(building_id)

            app.state.ROBOT_IS_MOVING = False

        background_tasks.add_task(callback)

    return route

app.get("/place-building-1")(create_building_route(1, WriteOffsetKey.BUILDING_1, Light.BUILDING_1))
app.get("/place-building-2")(create_building_route(2, WriteOffsetKey.BUILDING_2, Light.BUILDING_2))
app.get("/place-building-3")(create_building_route(3, WriteOffsetKey.BUILDING_3, Light.BUILDING_3))
app.get("/place-building-4")(create_building_route(4, WriteOffsetKey.BUILDING_4, Light.BUILDING_4))

@app.get("/lights-off")
def lights_off(background_tasks: BackgroundTasks):
    def callback():
        for light in Light: manage_light(LightAction.Off, light, blocking=False)

    background_tasks.add_task(callback)

@app.get("/celebrate")
def celebrate(background_tasks: BackgroundTasks):
    def callback():
        # robot used to be moving for this
        # activate_only(WriteOffsetKey.CELEBRATE)

        # lights animation
        for i in range(3):
            for light in Light:
                manage_light(LightAction.Off, light)
                time.sleep(0.25)  # stagger by half a second
                manage_light(LightAction.On, light)

        # reset
        for light in Light: manage_light(LightAction.On, light)

    background_tasks.add_task(callback)

@app.get("/celebrate-2")
def celebrate_special(background_tasks: BackgroundTasks):
    def callback():
        # robot used to be moving for this
        # activate_only(WriteOffsetKey.CELEBRATE)

        # lights animation
        for i in range(20):
            for j in range(len(Light)):
                # get a random light
                light = random.choice(list(Light))
                manage_light(LightAction.Off, light)
                time.sleep(0.025)  # stagger by half a second
                manage_light(LightAction.On, light)

        # reset
        for light in Light: manage_light(LightAction.On, light)

    background_tasks.add_task(callback)


@app.get("/clean-buildings")
def clean_buildings(background_tasks: BackgroundTasks):
    """
    Clean the buildings that were placed automatically.
    """

    if len(app.state.BUILDINGS_PLACED) == 0:
        logger.warning("No buildings were placed yet.")
        return

    if app.state.ROBOT_IS_MOVING:
        logger.warning("The robot is currently moving. Please wait until it finishes.")
        return

    app.state.BUILDINGS_PLACED.sort()
    logger.warning(f"Cleaning buildings: {app.state.BUILDINGS_PLACED}")

    def callback():
        """
        build the lights and offset_keys arrays
        """

        app.state.ROBOT_IS_MOVING = True

        for i in app.state.BUILDINGS_PLACED:
            light = Light.get_building_from_number(i)
            offset_key = WriteOffsetKey.get_clean_buildings_from_number(i)

            write_output(True, index_offset=offset_key, wait_until_finish=True)
            manage_light(LightAction.Off, light, blocking=False)

            # wait for the input to be reset to 'False', otherwise the next clean action will be
            # skipped (as the output is still 'True')
            time.sleep(2)

        # reset the BUILDINGS_PLACED array
        app.state.BUILDINGS_PLACED = []
        app.state.ROBOT_IS_MOVING = False

    background_tasks.add_task(callback)
