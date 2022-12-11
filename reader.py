from enum import Enum

from bs4 import BeautifulSoup

from data import *


def parse_pin_data(filename: str) -> Pin:
    with open(filename, 'r') as f:
        data = f.read()

    bs = BeautifulSoup(data, "xml")
    mcu = bs.find("Mcu")
    xml_pins = mcu.find_all("Pin")
    
    pins = []
    for id, xml_pin in enumerate(xml_pins):
        if xml_pin.get("Type") != "I/O":
            continue

        pin_name = xml_pin.get("Name")
        position = int(xml_pin.get("Position"))

        signals = []
        for xml_signal in xml_pin.find_all("Signal"):
            name = xml_signal.get('Name')
            type, bank, signal = parse_signal_name(pin_name.split("-")[0], name)

            signal = Signal(name, type, bank, signal)
            signals.append(signal)

        pin = Pin(id, pin_name, position, signals)
        pins.append(pin)

    return pins


def parse_signal_name(pin_name: str, name: str) -> (BankType, int, Enum | int):
    for before, after in REPLACEMENTS:
        name = name.replace(before, after)

    for enum in BankType:
        if name.startswith(enum.name):
            type = enum
            break
    else:
        return -1, -1, -1

    name = name.lstrip(enum.name)
    if type == BankType.GPIO:
        bank = ord(pin_name[1]) - ord("A") + 1
        signal = int(pin_name[2:])
    elif type == BankType.ADC:
        bank = int(name[0]) if name[0].isdigit() else 1
        if "EXTI" in name:
            signal = 64 + int(name.split("EXTI")[1]) # TODO: change this the day adcs have more than 64 channels
        else:
            signal = int(name.split("IN")[1])
    elif type == BankType.DAC:
        bank = int(name[0]) if name[0].isdigit() else 1
        if "EXTI" in name:
            signal = 64 + int(name.split("EXTI")[1]) # TODO: change this the day dacs have more than 64 channels
        else:
            signal = int(name.split("OUT")[1])
    else:
        # TODO: adc, dac
        signals_enum = eval(f"{type.name.capitalize()}Signals") # TODO: evals are bad but maps are annoying
        bank = int(name[0]) if name[0].isdigit() else 1
        signal_name = name.split("_", 1)[1].upper()
        if signal_name in signals_enum.__members__:
            signal = signals_enum[signal_name]
        else:
            print(signal_name, signals_enum, signals_enum.__members__)
            return -1, -1, -1

    return type, bank, signal


def parse_config(filename: str) -> [Feature]:
    features = []
    with open(filename, 'r') as f:
        for line in f:
            feature = parse_feature(line)
            if feature is not None:
                features.append(feature)

    return features


def parse_feature(feature: str) -> Feature | None:
    name, feature = feature.strip().split(" ", 1)

    if not feature.startswith("uses "):
        return None
    _, feature = feature.split(" ", 1)

    type, feature = feature.split("(", 1)
    if type.upper() not in BankType.__members__:
        return None
    type = BankType[type.upper()]

    signals, feature = feature.split(")", 1)
    if type == BankType.GPIO or type == BankType.ADC or type == BankType.DAC:
        signals = list(range(int(signals)))
    else:
        signals_enum = eval(f"{type.name.capitalize()}Signals") # TODO: evals are bad but maps are annoying
        signals = list(map(lambda signal: signals_enum[signal.strip().upper()], signals.split(",")))

    ret = Feature(name, type, signals)
    return ret
