# import json
import struct
from .utility import sendReceiveMessage, getSome
from ..const import code, DATA, DEVICE_TYPE


def request_pump_status(gateway_socket, data, pumpID):
    response = sendReceiveMessage(
        gateway_socket, code.PUMPSTATUS_QUERY, struct.pack("<II", 0, pumpID)
    )
    decode_pump_status(response, data, pumpID)


# pylint: disable=unused-variable
def decode_pump_status(buff, data, pumpID):
    # print(buff)
    if DATA.KEY_PUMPS not in data:
        data[DATA.KEY_PUMPS] = {}

    if pumpID not in data[DATA.KEY_PUMPS]:
        data[DATA.KEY_PUMPS][pumpID] = {}

    pump = data[DATA.KEY_PUMPS][pumpID]
    pump["name"] = ""
    pump["pumpType"], offset = getSome("I", buff, 0)
    pump["state"], offset = getSome("I", buff, offset)

    curW, offset = getSome("I", buff, offset)
    pump["currentWatts"] = {}
    curR, offset = getSome("I", buff, offset)
    pump["currentRPM"] = {}

    unknown1, offset = getSome("I", buff, offset)

    curG, offset = getSome("I", buff, offset)
    pump["currentGPM"] = {}

    unknown2, offset = getSome("I", buff, offset)

    pump["presets"] = {}
    name = "Default"
    for i in range(8):
        pump["presets"][i] = {}
        pump["presets"][i]["cid"], offset = getSome("I", buff, offset)
        if DATA.KEY_CIRCUITS in data:
            for num, circuit in data[DATA.KEY_CIRCUITS].items():
                if (
                    pump["presets"][i]["cid"] == circuit["device_id"]
                    and name == "Default"
                ):
                    name = circuit["name"]
                    break
        pump["presets"][i]["setPoint"], offset = getSome("I", buff, offset)
        pump["presets"][i]["isRPM"], offset = getSome("I", buff, offset)

    name = name.strip().strip(",") + " Pump"
    pump["name"] = name

    pump["currentWatts"] = {
        "name": pump["name"] + " Current Watts",
        "value": curW,
        "unit": "W",
        "device_type": DEVICE_TYPE.ENERGY,
    }

    pump["currentRPM"] = {
        "name": pump["name"] + " Current RPM",
        "value": curR,
        "unit": "rpm",
    }

    pump["currentGPM"] = {
        "name": pump["name"] + " Current GPM",
        "value": curG,
        "unit": "gpm",
    }
    # print(json.dumps(data, indent=4))
