from collections import namedtuple
from dataclasses import dataclass, field
from enum import Enum, auto

from z3 import Int, Ints, IntSort, Distinct, And, Or, If, Sum, Array, ArraySort, Not, Solver

class BankType(Enum):
    GPIO = auto()
    UART = auto()
    SWD = auto()

class UartChannels(Enum):
    TX = auto()
    RX = auto()
    CTS = auto()
    RTS = auto()

class SwdChannels(Enum):
    SWDIO = auto()
    SWCLK = auto()

class GpioBanks(Enum):
    A = auto()
    B = auto()
    C = auto()
    D = auto()

@dataclass
class AlternateFunction:
    type: int
    bank: int
    channel: int

@dataclass
class Feature:
    name: str
    type: int
    channels: [int]
    channel_alloc: [(Int, Int)] = field(default_factory=lambda: list())

blank = AlternateFunction(-1, -1, -1)

af_table_data = [
    [AlternateFunction(BankType.GPIO.value, GpioBanks.A.value, 1), AlternateFunction(BankType.UART.value, 1, UartChannels.TX.value), AlternateFunction(BankType.SWD.value, 1, SwdChannels.SWDIO.value)],
    [AlternateFunction(BankType.GPIO.value, GpioBanks.A.value, 2), AlternateFunction(BankType.UART.value, 1, UartChannels.RX.value), AlternateFunction(BankType.SWD.value, 1, SwdChannels.SWCLK.value)],
    [AlternateFunction(BankType.GPIO.value, GpioBanks.B.value, 1), AlternateFunction(BankType.UART.value, 2, UartChannels.TX.value), blank],
    [AlternateFunction(BankType.GPIO.value, GpioBanks.B.value, 2), AlternateFunction(BankType.UART.value, 2, UartChannels.RX.value), blank],
    [AlternateFunction(BankType.GPIO.value, GpioBanks.C.value, 1), blank, blank],
    [AlternateFunction(BankType.GPIO.value, GpioBanks.C.value, 2), blank, blank],
    [AlternateFunction(BankType.GPIO.value, GpioBanks.D.value, 1), blank, blank],
    [AlternateFunction(BankType.GPIO.value, GpioBanks.D.value, 2), blank, blank],
]

features = [
    Feature("debug", BankType.SWD.value, (SwdChannels.SWDIO.value, SwdChannels.SWCLK.value)),
    Feature("console", BankType.UART.value, (UartChannels.TX.value, UartChannels.RX.value)),
    Feature("single_bank_gpio", BankType.GPIO.value, 2),
    Feature("random_gpio1", BankType.GPIO.value, 1),
    Feature("random_gpio2", BankType.GPIO.value, 1),
]

pin_indexes = list(range(0, 8))
afid_range = (0, 2)

Z = IntSort()

solver = Solver()

af_types = Array('af_types', Z, ArraySort(Z, Z))
af_banks = Array('af_banks', Z, ArraySort(Z, Z))
af_channels = Array('af_channels', Z, ArraySort(Z, Z))
for pin_id, functions in enumerate(af_table_data):
    for af_id, function in enumerate(functions):
        solver.add(af_types[pin_id][af_id] == function.type)
        solver.add(af_banks[pin_id][af_id] == function.bank)
        solver.add(af_channels[pin_id][af_id] == function.channel)

pins = []
for feature in features:
    # each channel in each feature is assigned a pin and an AFID
    explicit_channels = type(feature.channels) is tuple
    channels = feature.channels if explicit_channels else range(feature.channels)
    banks = []

    for channel in channels:
        pin = Int(f"pin_{feature.name}_{channel}")
        afid = Int(f"afid_{feature.name}_{channel}")

        feature.channel_alloc.append((pin, afid))
        # pin and afid must be valid for the package
        solver.add(Or([pin == index for index in pin_indexes]))
        solver.add(And(afid >= afid_range[0], afid <= afid_range[1]))

        solver.add(Not(af_types[pin][afid] == -1))
        solver.add(Not(af_banks[pin][afid] == -1))
        solver.add(Not(af_channels[pin][afid] == -1))

        solver.add(af_types[pin][afid] == feature.type)
        if explicit_channels:
            solver.add(af_channels[pin][afid] == channel)

        banks.append(af_banks[pin][afid])
        pins.append(pin)

    solver.add(And([bank == banks[0] for bank in banks[1:]]))

solver.add(Distinct(pins))

if solver.check():
    model = solver.model()

    for feature in features:
        print(f"{feature.name} ({BankType(feature.type).name}): ", end="")
        mappings = []
        explicit_channels = type(feature.channels) is tuple
        channels = feature.channels if explicit_channels else range(feature.channels)
        for channel, (pin, afid) in zip(channels, feature.channel_alloc):
            channel_name = str(channel)
            if BankType(feature.type) == BankType.UART:
                channel_name = UartChannels(channel).name
            elif BankType(feature.type) == BankType.SWD:
                channel_name = SwdChannels(channel).name

            mappings.append(f"{channel_name}={model[pin]}({model[afid]})")

        print(", ".join(mappings))
    # print(solver.model())
