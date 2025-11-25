from fastapi import FastAPI

import pyads


app = FastAPI()

# ===============
# PLC SETUP
# ===============
def write_output(value: bool, index_group: int = 0xF021, index_offset: int = 0xD0) -> bool:
    ams_net_id = "5.98.172.87.1.1"
    ams_port = 27905

    """Writes a boolean to the output symbol and returns the readback."""
    with pyads.Connection(ams_net_id, ams_port) as plc:
        symbol = plc.get_symbol(
            index_group=index_group,
            index_offset=index_offset,
            plc_datatype=pyads.PLCTYPE_BOOL,
        )
        symbol.write(value)
        return symbol.read()


@app.get("/on")
def on():
    return {"led_status": write_output(True)}


@app.get("/off")
def off():
    return { "led_status": write_output(False) }
