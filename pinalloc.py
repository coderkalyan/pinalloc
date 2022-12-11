from enum import Enum
# from z3 import Int, Ints, IntSort, Distinct, And, Or, If, Sum, Array, ArraySort, Not, Solver
from z3 import *

import data
import reader

Z = IntSort()

Signal = Datatype("Signal")
Signal.declare("func", ("type", Z), ("bank", Z), ("signal", Z))
Signal = Signal.create()

Pin = Datatype("Pin")
Pin.declare("active", ("id", Z), ("position", Z), ("signal", Signal))
Pin.declare("inactive")
Pin = Pin.create()

pins_data = reader.parse_pin_data("/home/kalyan/Documents/src/STM32_open_pin_data/mcu/STM32F302K(6-8)Ux.xml")
features = reader.parse_config("config")

solver = Solver()

pins = []
for pin_data in pins_data:
    signals = []
    for signal_data in pin_data.signals:
        if signal_data.type == -1:
            continue

        signal = Signal.func(
            signal_data.type.value,
            signal_data.bank,
            signal_data.signal if type(signal_data.signal) is int else signal_data.signal.value
        )
        signals.append(signal)
    
    pin = Const(f"pin_{pin_data.name}", Pin)
    pins.append(pin)

    choices = Or([Pin.signal(pin) == signal for signal in signals])
    active = And(Pin.id(pin) == pin_data.id, Pin.position(pin) == pin_data.position, choices)
    solver.add(Or(Pin == Pin.inactive, active))

active_pins = []
pin_banks = dict()
for feature in features:
    feature.pins = []
    for signal_req in feature.signals:
        signal_name = str(signal_req) if type(signal_req) is int else signal_req.name
        signal_value = signal_req if type(signal_req) is int else signal_req.value
        pin = Const(f"pin_assign_{feature.name}_{signal_name}", Pin)
        feature.pins.append(pin)
        active_pins.append(pin)

        solver.add(Not(pin == Pin.inactive))
        solver.add(Or([pin == p for p in pins]))
        if type(signal_req) is not int:
            solver.add(Signal.signal(Pin.signal(pin)) == signal_value)

    # print(feature.name, feature.type.value)
    solver.add([Signal.type(Pin.signal(pin)) == feature.type.value for pin in feature.pins])

    bank = Signal.bank(Pin.signal(feature.pins[0]))
    solver.add([Signal.bank(Pin.signal(pin)) == bank for pin in feature.pins[1:]])
    
    if feature.type not in data.EXCLUSIVE_BANK_TYPES:
        if feature.type not in pin_banks:
            pin_banks[feature.type] = []
        pin_banks[feature.type].append(bank)

for _, banks in pin_banks.items():
    solver.add(Distinct(banks))

solver.add(Distinct(active_pins))
# print(active_pins)

# for pin in pins:
#     solver.add(If(Not(Or([pin == p for p in active_pins])), pin == Pin.inactive, True))
    # if pin not in active_pins:
    #     solver.add([pin == Pin.inactive])

# solver.add(Sum([If(pin == Pin.inactive, 0, 1) for pin in pins]) == len(active_pins))

solver.check()
model = solver.model()

positions = model[Pin.position].as_list()
position_mapping = dict([(pin.position, pin.name) for pin in pins_data])

for feature in features:
    print(f"{feature.name}:")
    for signal, pin in zip(feature.signals, feature.pins):
        signal = str(signal) if type(signal) is int else signal.name
        for entry in positions:
            try:
                if entry[0] == model[pin]:
                    pos = entry[1]
                    break
            except:
                pass
        else:
            pos = model[Pin.position].else_value()

        print(f"{signal} = {position_mapping[pos.as_long()]}")
