from fastapi import FastAPI

import pyads

app = FastAPI()

# ===============
# PLC SETUP
# ===============
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




def idle():
    # TODO if all other are off -> mark as idle
    return {"led_status": write_output(True)}


@app.get("/place-building-1")
def place_building_1():
    """Uses index offset `0x138`"""
    return { "led_status": write_output(value=True, index_offset=0x138) }


@app.get("/place-building-2")
def place_building_2():
    """Uses index offset `0x139`"""
    return { "led_status": write_output(value=True, index_offset=0x139) }


@app.get("/place-building-3")
def place_building_3():
    """Uses index offset `0x13A`"""
    return { "led_status": write_output(value=True, index_offset=0x13A) }


@app.get("/place-building-4")
def place_building_4():
    """Uses index offset `0x13B`"""
    return { "led_status": write_output(value=True, index_group=0x13B) }


@app.get("/celebrate")
def celebrate():
    """Uses index offset `0x13C`"""
    return { "led_status": write_output(value=True, index_group=0x13C) }


@app.get("/clean-buildings")
def clean_buildings():
    """Uses index offset `0x13D`"""
    return { "led_status": write_output(value=True, index_group=0x13D) }
