# import json
import struct
from ..const import CHEMISTRY, code, DATA, DEVICE_TYPE, ON_OFF, UNIT
from .utility import sendReceiveMessage, getSome

ADD_UNKNOWNS = False


def request_chemistry(gateway_socket, data):
    response = sendReceiveMessage(
        gateway_socket, code.CHEMISTRY_QUERY, struct.pack("<I", 0)
    )
    decode_chemistry(response, data)


def is_set(bits, mask) -> bool:
    return True if (bits & mask) == mask else False


# pylint: disable=unused-variable
def decode_chemistry(buff, data):
    # print(buff)

    if DATA.KEY_CHEMISTRY not in data:
        data[DATA.KEY_CHEMISTRY] = {}

    chemistry = data[DATA.KEY_CHEMISTRY]

    unit_txt = (
        UNIT.CELSIUS
        if DATA.KEY_CONFIG in data
        and "is_celsius" in data[DATA.KEY_CONFIG]
        and data[DATA.KEY_CONFIG]["is_celsius"]["value"]
        else UNIT.FAHRENHEIT
    )

    unknown = {}

    size, offset = getSome("I", buff, 0)
    unknown["size"] = size

    # skip an unknown value
    unknown1, offset = getSome("B", buff, offset)  # 0
    unknown["unknown1"] = unknown1

    pH, offset = getSome(">H", buff, offset)  # 1
    chemistry["current_ph"] = {"name": "Current pH", "value": (pH / 100), "unit": "pH"}

    orp, offset = getSome(">H", buff, offset)  # 3
    chemistry["current_orp"] = {"name": "Current ORP", "value": orp, "unit": "mV"}

    pHSetpoint, offset = getSome(">H", buff, offset)  # 5
    chemistry["ph_setpoint"] = {
        "name": "pH Setpoint",
        "value": (pHSetpoint / 100),
        "unit": "pH",
    }

    orpSetpoint, offset = getSome(">H", buff, offset)  # 7
    chemistry["orp_setpoint"] = {
        "name": "ORP Setpoint",
        "value": orpSetpoint,
        "unit": "mV",
    }
    # fast forward 12 bytes
    # Seems to be '>I' x2 and '>H' x2
    # Values change when pH and ORP dosing but I was unable to decode
    # offset += 12
    # Scratch above. Testing some values below.
    pHDoseTime, offset = getSome(">I", buff, offset)  # 9
    unknown["ph_dose_time"] = pHDoseTime
    orpDoseTime, offset = getSome(">I", buff, offset)  # 13
    unknown["orp_dose_time"] = orpDoseTime
    pHDoseVolume, offset = getSome(">H", buff, offset)  # 17
    unknown["ph_dose_volume"] = pHDoseVolume
    orpDoseVolume, offset = getSome(">H", buff, offset)  # 19
    unknown["orp_dose_volume"] = orpDoseVolume

    pHSupplyLevel, offset = getSome("B", buff, offset)  # 21 (20)
    chemistry["ph_supply_level"] = {"name": "pH Supply Level", "value": pHSupplyLevel}

    orpSupplyLevel, offset = getSome("B", buff, offset)  # 22 (21)
    chemistry["orp_supply_level"] = {
        "name": "ORP Supply Level",
        "value": orpSupplyLevel,
    }

    saturation, offset = getSome("B", buff, offset)  # 23
    chemistry["saturation"] = {
        "name": "Saturation Index",
        "value": (saturation - 256) / 100
        if is_set(saturation, 0x80)
        else saturation / 100,
        "unit": "lsi",
    }

    cal, offset = getSome(">H", buff, offset)  # 24
    chemistry["calcium_harness"] = {
        "name": "Calcium Hardness",
        "value": cal,
        "unit": "ppm",
    }

    cya, offset = getSome(">H", buff, offset)  # 26
    chemistry["cya"] = {"name": "Cyanuric Acid", "value": cya, "unit": "ppm"}

    alk, offset = getSome(">H", buff, offset)  # 28
    chemistry["total_alkalinity"] = {
        "name": "Total Alkalinity",
        "value": alk,
        "unit": "ppm",
    }

    saltPPM, offset = getSome("B", buff, offset)  # 30
    chemistry["salt_ppm"] = {"name": "Salt", "value": (saltPPM * 50), "unit": "ppm"}

    # Probe temp unit is Celsius?
    probIsC, offset = getSome("B", buff, offset)
    unknown["probe_is_celsius"] = probIsC

    waterTemp, offset = getSome("B", buff, offset)  # 32
    chemistry["ph_probe_water_temp"] = {
        "name": "pH Probe Water Temperature",
        "value": waterTemp,
        "unit": unit_txt,
        "device_type": DEVICE_TYPE.TEMPERATURE,
    }

    if DATA.KEY_ALERTS not in chemistry:
        chemistry[DATA.KEY_ALERTS] = {}

    alerts = chemistry[DATA.KEY_ALERTS]

    alarms, offset = getSome("B", buff, offset)  # 33 (32)
    alerts["flow_alarm"] = {
        "name": "Flow Alarm",
        "value": ON_OFF.from_bool(is_set(alarms, CHEMISTRY.FLAG_ALARM_FLOW)),
    }
    alerts["ph_alarm"] = {
        "name": "pH Alarm",
        "value": ON_OFF.from_bool(is_set(alarms, CHEMISTRY.FLAG_ALARM_PH)),
    }
    alerts["orp_alarm"] = {
        "name": "ORP Alarm",
        "value": ON_OFF.from_bool(is_set(alarms, CHEMISTRY.FLAG_ALARM_ORP)),
    }
    alerts["ph_supply_alarm"] = {
        "name": "pH Supply Alarm",
        "value": ON_OFF.from_bool(is_set(alarms, CHEMISTRY.FLAG_ALARM_PH_SUPPLY)),
    }
    alerts["orp_supply_alarm"] = {
        "name": "ORP Supply Alarm",
        "value": ON_OFF.from_bool(is_set(alarms, CHEMISTRY.FLAG_ALARM_ORP_SUPPLY)),
    }
    alerts["probe_fault_alarm"] = {
        "name": "Probe Fault",
        "value": ON_OFF.from_bool(is_set(alarms, CHEMISTRY.FLAG_ALARM_PROBE_FAULT)),
    }

    if DATA.KEY_NOTIFICATIONS not in chemistry:
        chemistry[DATA.KEY_NOTIFICATIONS] = {}

    notifications = chemistry[DATA.KEY_NOTIFICATIONS]

    warnings, offset = getSome("B", buff, offset)  # 34
    unknown["warnings"] = warnings
    notifications["ph_lockout"] = {
        "name": "pH Lockout",
        "value": ON_OFF.from_bool(is_set(warnings, CHEMISTRY.FLAG_WARNING_PH_LOCKOUT)),
    }
    notifications["ph_limit"] = {
        "name": "pH Daily Limit Reached",
        "value": ON_OFF.from_bool(is_set(warnings, CHEMISTRY.FLAG_WARNING_PH_LIMIT)),
    }
    notifications["orp_limit"] = {
        "name": "ORP Daily Limit Reached",
        "value": ON_OFF.from_bool(is_set(warnings, CHEMISTRY.FLAG_WARNING_ORP_LIMIT)),
    }

    status, offset = getSome("B", buff, offset)  # 35 (34)
    unknown["status"] = status
    # notifications["corrosive"] = {
    #    "name": "Corrosive",
    #    "value": ON_OFF.from_bool(is_set(status, CHEMISTRY.FLAG_STATUS_CORROSIVE)),
    # }
    # notifications["scaling"] = {
    #    "name": "Scaling",
    #    "value": ON_OFF.from_bool(is_set(status, CHEMISTRY.FLAG_STATUS_SCALING)),
    # }

    chemistry["ph_dosing_state"] = {
        "name": "pH Dosing State",
        "value": (status & CHEMISTRY.MASK_STATUS_PH_DOSING) >> 4,
    }
    chemistry["orp_dosing_state"] = {
        "name": "ORP Dosing State",
        "value": (status & CHEMISTRY.MASK_STATUS_ORP_DOSING) >> 6,
    }

    flags, offset = getSome("B", buff, offset)  # 36 (35)
    chemistry["flags"] = flags

    vMinor, offset = getSome("B", buff, offset)  # 37 (36)
    vMajor, offset = getSome("B", buff, offset)  # 38 (37)
    chemistry["firmware"] = {
        "name": "IntelliChem Firmware Version",
        "value": f"{vMajor}.{str(vMinor).zfill(3)}",
    }

    chemWarnings, offset = getSome("B", buff, offset)  # 39 (38)
    unknown["warnings"] = chemWarnings

    last2, offset = getSome("B", buff, offset)  # 40
    unknown["last2"] = last2
    last3, offset = getSome("B", buff, offset)  # 41
    unknown["last3"] = last3
    last4, offset = getSome("B", buff, offset)  # 42
    unknown["last4"] = last4

    if ADD_UNKNOWNS:
        chemistry["unknown"] = unknown

    # print(json.dumps(data, indent=4))
