#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import struct
from datetime import datetime

accepted_profiles = [
    {
        "profile_id": 0,
        "versions" : [{"profile_version" : 1, "length" : 50}]
    },
    {
        "profile_id": 1,
        "versions" : [{"profile_version" : 1, "length" : 50}]
    },
    {
        "profile_id": 2,
        "versions" : [{"profile_version" : 1, "length" : 50}]
    },
    {
        "profile_id": 3,
        "versions" : [{"profile_version" : 1, "length" : 50}]
    },
    {
        "profile_id": 4,
        "versions" : [{"profile_version" : 1, "length" : 50}]
    },
    {
        "profile_id": 5,
        "versions" : [{"profile_version" : 1, "length" : 44}]
    },
    {
        "profile_id": 6,
        "versions" : [{"profile_version" : 1, "length" : 50}]
    },
    {
        "profile_id": 7,
        "versions" : [{"profile_version" : 1, "length" : 50}]
    }
]

def read_bytes(bytes, from_index, count):
    return int.from_bytes(bytes[from_index:from_index + count], byteorder='big')

def u32_to_s32(number):
    if number > 2**31:
        number -= 2**32
    return number

def u32_to_s16(number):
    if number > 2**15:
        number -= 2**16
    return number

def is_default_u32(value):
    return value == 2**32 - 1

def is_default_s32(value):
    return value == 2**31 - 1

def is_default_u16(value):
    return value == 2**16 - 1

def is_default_s16(value):
    return value == 2**15 - 1

def decodeUplink(input):

    output = {
        'codec': {
            'codecName': "SOCOMEC PYTHON B-10L codec",
            'codecVersion': "v1.1",
            'codecDate': "2024-03-05"
        },
        'executionTime': datetime.utcnow().isoformat(),
        'input' : {
            "bytes": input["bytes"],
            "fPort": input["fPort"],
            "recvTime": input["recvTime"]
        },
        'data' : {},
        'warnings':[],
        'errors':[]
    }

    try:
        Payload_Byte = bytearray.fromhex(input["bytes"])
    except ValueError:
        output['errors'] = "Frame should be an hexadecimal string"
        return output
    
    if input["fPort"]==0:
        output['warnings'].append("Void message, no data")
        return output
    
    if input["fPort"]!=2:
        fPort = input["fPort"]
        output['errors'].append(f'No frame shoud be sent on port {input["fPort"]}')
        return output

    if len(Payload_Byte) >= 1:
        msg_type = Payload_Byte[0]

    if msg_type == 0x11:  # Alarms
        index = 1
        nb_second = read_bytes(Payload_Byte, index, 4)
        index += 4
        logic_combi_alarm = Payload_Byte[index]
        analogic_alarm = Payload_Byte[index + 1]
        system_alarm = Payload_Byte[index + 2]
        protection_alarm = Payload_Byte[index + 3]

        output['data'] = {
            'frame': {
                'frame_type': msg_type,
                'frame_type_label': "Alarm"
            },
            'ILogicalAlarmValue1': 1 if (logic_combi_alarm & 0x01) else 0,
            'ILogicalAlarmValue2': 1 if (logic_combi_alarm & 0x02) else 0,
            'ILogicalAlarmValue3': 1 if (logic_combi_alarm & 0x04) else 0,
            'ILogicalAlarmValue4': 1 if (logic_combi_alarm & 0x08) else 0,
            'ICombiAlarmValue1': 1 if (logic_combi_alarm & 0x10) else 0,
            'ICombiAlarmValue2': 1 if (logic_combi_alarm & 0x20) else 0,
            'ICombiAlarmValue3': 1 if (logic_combi_alarm & 0x40) else 0,
            'ICombiAlarmValue4': 1 if (logic_combi_alarm & 0x80) else 0,
            'IAnalogAlarmValue1': 1 if (analogic_alarm & 0x01) else 0,
            'IAnalogAlarmValue2': 1 if (analogic_alarm & 0x02) else 0,
            'IAnalogAlarmValue3': 1 if (analogic_alarm & 0x04) else 0,
            'IAnalogAlarmValue4': 1 if (analogic_alarm & 0x08) else 0,
            'ISystemAlarmValue1': 1 if (system_alarm & 0x01) else 0,
            'ISystemAlarmValue2': 1 if (system_alarm & 0x02) else 0,
            'ISystemAlarmValue3': 1 if (system_alarm & 0x04) else 0,
            'ISystemAlarmValue4': 1 if (system_alarm & 0x08) else 0,
            'IProtectionAlarmValue1': 1 if (protection_alarm & 0x01) else 0,
            'IProtectionAlarmValue2': 1 if (protection_alarm & 0x02) else 0,
            'IProtectionAlarmValue3': 1 if (protection_alarm & 0x04) else 0,
            'IProtectionAlarmValue4': 1 if (protection_alarm & 0x08) else 0
        }
        if nb_second == 0:
            output['warnings'].append("Datetime is not set correctly")
        output['data'] = {
                **output['data'],
                'timestamp': None if nb_second == 0 else datetime.utcfromtimestamp(nb_second+datetime(2000, 1, 1).timestamp())
            }
            
    if msg_type == 2:  # Données périodiques
        if len(Payload_Byte) >= 2:
            Profile = (Payload_Byte[1] & 0xF0) >> 4
            Profile_version = Payload_Byte[1] & 0x0F
        else:
            output['errors'] = "Data periodic frame should be larger than 1 byte"
            return output
        
        for profile in accepted_profiles:
            if profile["profile_id"] == Profile:
                versions = profile["versions"]
        if not 'versions' in locals():
            output['errors'] = f"Periodic data profile {Profile} is not managed"
            return output

        for version in versions:
            if version["profile_version"] == Profile_version:
                frameLength = version["length"]
        if not 'frameLength' in locals():
            output['errors'] = f"Version {Profile_version} of periodic data profile {Profile} is not managed"
            return output

        if len(Payload_Byte) != frameLength:
            output['errors'] = f"Frame in version {Profile_version} of periodic data profile {Profile} should be {frameLength} bytes long"
            return output

        output['data'] = {
            'frame': {
                'frame_type': msg_type,
                'frame_type_label': "Periodical data",
                'profileId': Profile,
                'profileVersion': Profile_version
            }
        }

        # Autres traitements spécifiques au profil ici
        
        if Profile == 0:
            output['warings'] = "Profile 0 (custom) is not managed"

        if Profile == 1:  # Single-load – Energies (consumption/production)
            output['data']['frame']['profileLabel'] = "1 - Single Load energies (consumption/production)"

            NbSecond = read_bytes(Payload_Byte, 2, 4)
            Ea_plus = read_bytes(Payload_Byte, 6, 8)
            Ea_moins = read_bytes(Payload_Byte, 14, 8)
            Er_plus = read_bytes(Payload_Byte, 22, 8)
            Er_moins = read_bytes(Payload_Byte, 30, 8)
            PulseMeter = read_bytes(Payload_Byte, 38, 8)

            DIaVM = read_bytes(Payload_Byte, 46, 2)
            Decode_DIaVM = True
            CounterStatus = read_bytes(Payload_Byte, 48, 2)
            Decode_CounterStatus = True

            output['data'] = {
                **output['data'],
                'IEaPInst': Ea_plus / 10000,
                'IEaPInst_Unit': "kWh",
                'IEaNInst': Ea_moins / 10000,
                'IEaNInst_Unit': "kWh",
                'IErPInst': Er_plus / 10000,
                'IErPInst_Unit': "kVar",
                'IErNInst': Er_moins / 10000,
                'IErNInst_Unit': "kVar",
                'ITotalMeter': PulseMeter / 10000,
                'ITotalMeter_Unit': "pulse"
            }

        if Profile == 2:  # Profile 2: Multi-load – Energies (consumption)
            output['data']['frame']['profileLabel'] = "2- Multi-load & Energies (consumption)"

            NbSecond = read_bytes(Payload_Byte, 2, 4)
            Ea_plus_Load1 = read_bytes(Payload_Byte, 6, 4)
            Er_plus_Load1 = read_bytes(Payload_Byte, 10, 4)
            Ea_plus_Load2 = read_bytes(Payload_Byte, 14, 4)
            Er_plus_Load2 = read_bytes(Payload_Byte, 18, 4)
            Ea_plus_Load3 = read_bytes(Payload_Byte, 22, 4)
            Er_plus_Load3 = read_bytes(Payload_Byte, 16, 4)
            Ea_plus_Load4 = read_bytes(Payload_Byte, 30, 4)
            Er_plus_Load4 = read_bytes(Payload_Byte, 34, 4)
            PulseMeter = read_bytes(Payload_Byte, 38, 8)

            DIaVM = read_bytes(Payload_Byte, 46, 2)
            Decode_DIaVM = True
            CounterStatus = read_bytes(Payload_Byte, 48, 2)
            Decode_CounterStatus = True

            output['data'] = {
                **output['data'],
                'IEaPInst1': Ea_plus_Load1,
                'IEaPInst1_Unit': "kWh",
                'IErPInst1': Er_plus_Load1,
                'IErPInst1_Unit': "kVar",

                'IEaPInst2': Ea_plus_Load2,
                'IEaPInst2_Unit': "kWh",
                'IErPInst2': Er_plus_Load2,
                'IErPInst2_Unit': "kVar",

                'IEaPInst3': Ea_plus_Load3,
                'IEaPInst3_Unit': "kWh",
                'IErPInst3': Er_plus_Load3,
                'IErPInst3_Unit': "kVar",

                'IEaPInst4': Ea_plus_Load4,
                'IEaPInst4_Unit': "kWh",
                'IErPInst4': Er_plus_Load4,
                'IErPInst4_Unit': "kVar",
            }

        if Profile == 3:  # Profile 3: Multi-load – Energies (consumption/production)
            output['data']['frame']['profileLabel'] = "3 - Multi-load energies (consumption/production)"

            NbSecond = read_bytes(Payload_Byte, 2, 4)
            Ea_plus_Load1 = read_bytes(Payload_Byte, 6, 4)
            Ea_moins_Load1 = read_bytes(Payload_Byte, 10, 4)
            Ea_plus_Load2 = read_bytes(Payload_Byte, 14, 4)
            Ea_moins_Load2 = read_bytes(Payload_Byte, 18, 4)
            Ea_plus_Load3 = read_bytes(Payload_Byte, 22, 4)
            Ea_moins_Load3 = read_bytes(Payload_Byte, 16, 4)
            Ea_plus_Load4 = read_bytes(Payload_Byte, 30, 4)
            Ea_moins_Load4 = read_bytes(Payload_Byte, 34, 4)
            PulseMeter = read_bytes(Payload_Byte, 38, 8)

            DIaVM = read_bytes(Payload_Byte, 46, 2)
            Decode_DIaVM = True
            CounterStatus = read_bytes(Payload_Byte, 48, 2)
            Decode_CounterStatus = True

            output['data'] = {
                **output['data'],
                'IEaPInst1': Ea_plus_Load1,
                'IEaPInst1_Unit': "kWh",
                'IEaNInst1': Ea_moins_Load1,
                'IEaNInst1_Unit': "kWh",

                'IEaPInst2': Ea_plus_Load2,
                'IEaPInst2_Unit': "kWh",
                'IEaNInst2': Ea_moins_Load2,
                'IEaNInst2_Unit': "kWh",

                'IEaPInst3': Ea_plus_Load3,
                'IEaPInst3_Unit': "kWh",
                'IEaNInst3': Ea_moins_Load3,
                'IEaNInst3_Unit': "kWh",

                'IEaPInst4': Ea_plus_Load4,
                'IEaPInst4_Unit': "kWh",
                'IEaNInst4': Ea_moins_Load4,
                'IEaNInst4_Unit': "kWh",
            }

        if Profile == 4:  # Profile 4: Single-load – Monitoring
            output['data']['frame']['profileLabel'] = "4 - Single load Monitoring"

            NbSecond = read_bytes(Payload_Byte, 2, 4)
            Pmoy = None if is_default_s32(read_bytes(Payload_Byte, 6, 4)) else u32_to_s32(read_bytes(Payload_Byte, 6, 4)) / 1000
            Qmoy = None if is_default_s32(read_bytes(Payload_Byte, 10, 4)) else u32_to_s32(read_bytes(Payload_Byte, 10, 4)) / 1000
            Smoy = None if is_default_u32(read_bytes(Payload_Byte, 14, 4)) else read_bytes(Payload_Byte, 14, 4) / 1000
            Pf_Moy = None if is_default_s16(read_bytes(Payload_Byte, 18, 2)) else u32_to_s16(read_bytes(Payload_Byte, 18, 2))
            Pf_Type = read_bytes(Payload_Byte, 20, 2)
            I1_Moy = None if is_default_u32(read_bytes(Payload_Byte, 22, 4)) else read_bytes(Payload_Byte, 22, 4) / 1000
            I2_Moy = None if is_default_u32(read_bytes(Payload_Byte, 26, 4)) else read_bytes(Payload_Byte, 26, 4) / 1000
            I3_Moy = None if is_default_u32(read_bytes(Payload_Byte, 30, 4)) else read_bytes(Payload_Byte, 30, 4) / 1000
            F_moy = None if is_default_u32(read_bytes(Payload_Byte, 34, 4)) else read_bytes(Payload_Byte, 34, 4) / 1000
            DIaVM = read_bytes(Payload_Byte, 38, 2)
            Decode_DIaVM = True
            Temp_1 = None if is_default_s16(read_bytes(Payload_Byte, 40, 2)) else u32_to_s16(read_bytes(Payload_Byte, 40, 2)) / 100
            Temp_2 = None if is_default_s16(read_bytes(Payload_Byte, 42, 2)) else u32_to_s16(read_bytes(Payload_Byte, 42, 2)) / 100
            Temp_3 = None if is_default_s16(read_bytes(Payload_Byte, 44, 2)) else u32_to_s16(read_bytes(Payload_Byte, 44, 2)) / 100
            CounterStatus2 = read_bytes(Payload_Byte, 46, 2)
            CounterStatus = read_bytes(Payload_Byte, 48, 2)
            Decode_CounterStatus = True

            output['data'] = {
                **output['data'],
                'IPSumAvgInst': Pmoy,
                'IPSumAvgInst_Unit': "kW",
                'IQSumAvgInst': Qmoy,
                'IQSumAvgInst_Unit': "kVar",
                'ISSumAvgInst': Smoy,
                'ISSumAvgInst_Unit': "kVar",

                'IpFSumAvgInst': Pf_Moy,
                'IpFSumAvgInst_Unit': None,
                'IpFSumTypeAvg': Pf_Type,
                'IpFSumTypeAvg_Unit': None,

                'II1AvgInst': I1_Moy,
                'II1AvgInst_Unit': "A",
                'II2AvgInst': I2_Moy,
                'II2AvgInst_Unit': "A",
                'II3AvgInst': I3_Moy,
                'II3AvgInst_Unit': "A",

                'IFreqAvgInst': F_moy,
                'IFreqAvgInst_Unit': "Hz",

                'IInstTemperature1': Temp_1,
                'IInstTemperature2': Temp_2,
                'IInstTemperature3': Temp_3,

                'IInstTemperature1_unit': "°C",
                'IInstTemperature2_unit': "°C",
                'IInstTemperature3_unit': "°C",

                'CT1Cpt': CounterStatus2 & 0x000F,
                'CT2Cpt': (CounterStatus2 & 0x00F0) >> 4,
                'CT3Cpt': (CounterStatus2 & 0x0F00) >> 8,
                'CT4Cpt': (CounterStatus2 & 0xF000) >> 12
            }

        if Profile == 5:  # Profile 5 - Multi-load – Monitoring
            output['data']['frame']['profileLabel'] = "5 - Multi-load monitoring"

            NbSecond = read_bytes(Payload_Byte, 2, 4)
            Pmoy_Load1 = None if is_default_s32(read_bytes(Payload_Byte, 6, 4)) else u32_to_s32(read_bytes(Payload_Byte, 6, 4)) / 1000
            Qmoy_Load1 = None if is_default_s32(read_bytes(Payload_Byte, 10, 4)) else u32_to_s32(read_bytes(Payload_Byte, 10, 4)) / 1000
            Pmoy_Load2 = None if is_default_s32(read_bytes(Payload_Byte, 14, 4)) else u32_to_s32(read_bytes(Payload_Byte, 14, 4)) / 1000
            Qmoy_Load2 = None if is_default_s32(read_bytes(Payload_Byte, 18, 4)) else u32_to_s32(read_bytes(Payload_Byte, 18, 4)) / 1000
            Pmoy_Load3 = None if is_default_s32(read_bytes(Payload_Byte, 22, 4)) else u32_to_s32(read_bytes(Payload_Byte, 22, 4)) / 1000
            Qmoy_Load3 = None if is_default_s32(read_bytes(Payload_Byte, 26, 4)) else u32_to_s32(read_bytes(Payload_Byte, 26, 4)) / 1000
            Pmoy_Load4 = None if is_default_s32(read_bytes(Payload_Byte, 30, 4)) else u32_to_s32(read_bytes(Payload_Byte, 30, 4)) / 1000
            Qmoy_Load4 = None if is_default_s32(read_bytes(Payload_Byte, 34, 4)) else u32_to_s32(read_bytes(Payload_Byte, 34, 4)) / 1000

            DIaVM = read_bytes(Payload_Byte, 38, 2)
            Decode_DIaVM = True
            CounterStatus = read_bytes(Payload_Byte, 40, 2)
            Decode_CounterStatus = True

            output['data'] = {
                **output['data'],
                "IPSumAvgInst1": Pmoy_Load1,
                "IPSumAvgInst1_Unit": "kW",
                "IQSumAvgInst1": Qmoy_Load1,
                "IQSumAvgInst1_Unit": "kVar",

                "IPSumAvgInst2": Pmoy_Load2,
                "IPSumAvgInst2_Unit": "kW",
                "IQSumAvgInst2": Qmoy_Load2,
                "IQSumAvgInst2_Unit": "kVar",

                "IPSumAvgInst3": Pmoy_Load3,
                "IPSumAvgInst3_Unit": "kW",
                "IQSumAvgInst3": Qmoy_Load3,
                "IQSumAvgInst3_Unit": "kVar",

                "IPSumAvgInst4": Pmoy_Load4,
                "IPSumAvgInst4_Unit": "kW",
                "IQSumAvgInst4": Qmoy_Load4,
                "IQSumAvgInst4_Unit": "kVar",
            }

        if Profile == 6:  # Profile 6 - Single-load - Load curves
            output['data']['frame']['profileLabel'] = "6 - Single load - Load curves"

            Date_t0 = None
            if is_default_u32(read_bytes(Payload_Byte, 2, 4)):
                output['warnings'].append("t0 values are not available")
            elif read_bytes(Payload_Byte, 2, 4) < 20*365*24*60*60:
                output['warnings'].append("Datetime t0 is not set correctly")
            else:
                Date_t0 = datetime.fromtimestamp(read_bytes(Payload_Byte, 2, 4) + datetime(2000, 1, 1).timestamp()).strftime('%Y-%m-%d %H:%M:%S')
            P_Plus_t0 = None if is_default_u32(read_bytes(Payload_Byte, 6, 4)) else read_bytes(Payload_Byte, 6, 4) / 1000
            P_Moins_t0 = None if is_default_u32(read_bytes(Payload_Byte, 10, 4)) else read_bytes(Payload_Byte, 10, 4) / 1000
            Q_Plus_t0 = None if is_default_u32(read_bytes(Payload_Byte, 14, 4)) else read_bytes(Payload_Byte, 14, 4) / 1000
            Q_Moins_t0 = None if is_default_u32(read_bytes(Payload_Byte, 18, 4)) else read_bytes(Payload_Byte, 18, 4) / 1000
            type_t0 = None if is_default_u16(read_bytes(Payload_Byte, 22, 2)) else read_bytes(Payload_Byte, 22, 2)

            Date_t1 = None
            if is_default_u32(read_bytes(Payload_Byte, 24, 4)):
                output['warnings'].append("t-1 values are not available")
            elif read_bytes(Payload_Byte, 24, 4) < 20*365*24*60*60:
                output['warnings'].append("Datetime t-1 is not set correctly")
            else:
                Date_t1 = datetime.fromtimestamp(read_bytes(Payload_Byte, 24, 4) + datetime(2000, 1, 1).timestamp()).strftime('%Y-%m-%d %H:%M:%S')
            P_Plus_t1 = None if is_default_u32(read_bytes(Payload_Byte, 28, 4)) else read_bytes(Payload_Byte, 28, 4) / 1000
            P_Moins_t1 = None if is_default_u32(read_bytes(Payload_Byte, 32, 4)) else read_bytes(Payload_Byte, 32, 4) / 1000
            Q_Plus_t1 = None if is_default_u32(read_bytes(Payload_Byte, 36, 4)) else read_bytes(Payload_Byte, 36, 4) / 1000
            Q_Moins_t1 = None if is_default_u32(read_bytes(Payload_Byte, 40, 4)) else read_bytes(Payload_Byte, 40, 4) / 1000
            type_t1 = None if is_default_u16(read_bytes(Payload_Byte, 44, 2)) else read_bytes(Payload_Byte, 44, 2)

            DIaVM = read_bytes(Payload_Byte, 46, 2)
            Decode_DIaVM = True
            CounterStatus = read_bytes(Payload_Byte, 48, 2)
            Decode_CounterStatus = True

            output['data'] = {
                **output['data'],
                "timestamp_t0": Date_t0,
                "ILastP10ActivePower": P_Plus_t0,
                "ILastP10ActivePower_Unit": "kW",
                "ILastP10ActivePowerNeg": P_Moins_t0,
                "ILastP10ActivePowerNeg_Unit": "kW",

                "ILastP10ReactivePower": Q_Plus_t0,
                "ILastP10ReactivePower_Unit": "kVar",
                "ILastP10ReactivePowerNeg": Q_Moins_t0,
                "ILastP10ReactivePowerNeg_Unit": "kVar",

                "Type_P10": type_t0,

                "timestamp_t-1": Date_t1,
                "ILastP10ActivePower_t-1": P_Plus_t1,
                "ILastP10ActivePower_t-1_Unit": "kW",
                "ILastP10ActivePowerNeg_t-1": P_Moins_t1,
                "ILastP10ActivePowerNeg_t-1_Unit": "kW",

                "ILastP10ReactivePower_t-1": Q_Plus_t1,
                "ILastP10ReactivePower_t-1_Unit": "kVar",
                "ILastP10ReactivePowerNeg_t-1": Q_Moins_t1,
                "ILastP10ReactivePowerNeg_t-1_Unit": "kVar",

                "Type_P10_t-1": type_t1,
            }

        if Profile == 7:  # Profile 7 - Multi-load - Load curves
            output['data']['frame']['profileLabel'] = "7 - Multi load - Load curves"

            Date_t0 = None
            if is_default_u32(read_bytes(Payload_Byte, 2, 4)):
                output['warnings'].append("t0 values are not available")
            elif read_bytes(Payload_Byte, 2, 4) < 20*365*24*60*60:
                output['warnings'].append("Datetime t0 is not set correctly")
            else:
                Date_t0 = datetime.fromtimestamp(read_bytes(Payload_Byte, 2, 4) + datetime(2000, 1, 1).timestamp()).strftime('%Y-%m-%d %H:%M:%S')
            P_Plus_t0_load1 = None if is_default_u32(read_bytes(Payload_Byte, 6, 4)) else read_bytes(Payload_Byte, 6, 4) / 1000
            P_Plus_t0_load2 = None if is_default_u32(read_bytes(Payload_Byte, 10, 4)) else read_bytes(Payload_Byte, 10, 4) / 1000
            P_Plus_t0_load3 = None if is_default_u32(read_bytes(Payload_Byte, 14, 4)) else read_bytes(Payload_Byte, 14, 4) / 1000
            P_Plus_t0_load4 = None if is_default_u32(read_bytes(Payload_Byte, 18, 4)) else read_bytes(Payload_Byte, 18, 4) / 1000
            type_t0 = None if is_default_u16(read_bytes(Payload_Byte, 22, 2)) else read_bytes(Payload_Byte, 22, 2)

            Date_t1 = None
            if is_default_u32(read_bytes(Payload_Byte, 24, 4)):
                output['warnings'].append("t-1 values are not available")
            elif read_bytes(Payload_Byte, 24, 4) < 20*365*24*60*60:
                output['warnings'].append("Datetime t-1 is not set correctly")
            else:
                Date_t1 = datetime.fromtimestamp(read_bytes(Payload_Byte, 24, 4) + datetime(2000, 1, 1).timestamp()).strftime('%Y-%m-%d %H:%M:%S')
            P_Plus_t1_load1 = None if is_default_u32(read_bytes(Payload_Byte, 28, 4)) else read_bytes(Payload_Byte, 28, 4) / 1000
            P_Plus_t1_load2 = None if is_default_u32(read_bytes(Payload_Byte, 32, 4)) else read_bytes(Payload_Byte, 32, 4) / 1000
            P_Plus_t1_load3 = None if is_default_u32(read_bytes(Payload_Byte, 36, 4)) else read_bytes(Payload_Byte, 36, 4) / 1000
            P_Plus_t1_load4 = None if is_default_u32(read_bytes(Payload_Byte, 40, 4)) else read_bytes(Payload_Byte, 40, 4) / 1000
            type_t1 = None if is_default_u16(read_bytes(Payload_Byte, 44, 2)) else read_bytes(Payload_Byte, 44, 2)

            DIaVM = read_bytes(Payload_Byte, 46, 2)
            Decode_DIaVM = True
            CounterStatus = read_bytes(Payload_Byte, 48, 2)
            Decode_CounterStatus = True

            output['data'] = {
                **output['data'],
                "timestamp_t0": Date_t0,
                "ILastP10ActivePower_Load1": P_Plus_t0_load1,
                "ILastP10ActivePower_Load1_Unit": "kW",
                "ILastP10ActivePower_Load2": P_Plus_t0_load2,
                "ILastP10ActivePower_Load2_Unit": "kW",
                "ILastP10ActivePower_Load3": P_Plus_t0_load3,
                "ILastP10ActivePower_Load3_Unit": "kW",
                "ILastP10ActivePower_Load4": P_Plus_t0_load4,
                "ILastP10ActivePower_Load4_Unit": "kW",

                "timestamp_t-1": Date_t1,
                "ILastP10ActivePower_Load1_t-1": P_Plus_t1_load1,
                "ILastP10ActivePower_Load1_t-1_Unit": "kW",
                "ILastP10ActivePower_Load2_t-1": P_Plus_t1_load2,
                "ILastP10ActivePower_Load2_t-1_Unit": "kW",
                "ILastP10ActivePower_Load3_t-1": P_Plus_t1_load3,
                "ILastP10ActivePower_Load3_t-1_Unit": "kW",
                "ILastP10ActivePower_Load4_t-1": P_Plus_t1_load4,
                "ILastP10ActivePower_Load4_t-1_Unit": "kW",
            }

        # Continue with other profiles in a similar manner...

        # Common part of some profiles
        if Decode_DIaVM:  # Digital Inputs and VirtualMonitor (iTR)
            output['data'] = {
                **output['data'],
                'IInputFct01': int((DIaVM & 0x0001) != 0),
                'IInputFct02': int((DIaVM & 0x0002) != 0),
                'IInputFct03': int((DIaVM & 0x0004) != 0),
                'IInputFct04': int((DIaVM & 0x0008) != 0),
                'IInputFct05': int((DIaVM & 0x0010) != 0),
                'IInputFct06': int((DIaVM & 0x0020) != 0),
                'IInputFct07': int((DIaVM & 0x0040) != 0),
                'IInputFct08': int((DIaVM & 0x0080) != 0),
                'IInputFct09': int((DIaVM & 0x0100) != 0),
                'IInputFct10': int((DIaVM & 0x0200) != 0),
                'CT1': int((DIaVM & 0x0400) != 0),
                'CT2': int((DIaVM & 0x0800) != 0),
                'CT3': int((DIaVM & 0x1000) != 0),
                'CT4': int((DIaVM & 0x2000) != 0)
            }

        if Decode_CounterStatus:  # Digital Inputs and VirtualMonitor (iTR)
            output['data'] = {
                **output['data'],
                'Input1Cpt': CounterStatus & 0x000F,
                'Input2Cpt': (CounterStatus & 0x00F0) >> 4,
                'Input3Cpt': (CounterStatus & 0x0F00) >> 8,
                'Input4Cpt': (CounterStatus & 0xF000) >> 12
            }
        
        if Profile not in [0, 6, 7]:
            if NbSecond == 0:
                output['warnings'].append("Datetime is not set correctly")
            output['data'] = {
                **output['data'],
                'timestamp': None if NbSecond == 0 else datetime.utcfromtimestamp(NbSecond+datetime(2000, 1, 1).timestamp())
            }

    if msg_type == 1:  # configuration
        output['data'] = {
            'frame' : {
                'frame_type': 1,
                'frame_type_label': "Configuration settings"
            }
        }

        if len(Payload_Byte) == 2:
            if Payload_Byte[1] == 1:
                output['data'] = {
                    **output['data'],
                    'Config_settings_content': "B-10L ask the date & hour"
                }
        else:
            output['errors'] = "error, payload length must be 2 bytes"
        return output

    return output

# Example usage:
# Replace the 'your_bytes_here' with the actual bytes you want to decode.
# bytes_to_decode = bytes.fromhex('your_bytes_here')
# result = decode(bytes_to_decode)
# print(result)
