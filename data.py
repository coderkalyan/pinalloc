from dataclasses import dataclass
from enum import Enum, auto

from z3 import Int

class BankType(Enum):
    SYS = auto()
    RCC = auto()

    GPIO = auto()
    TIM = auto()
    RTC = auto()

    USART = auto()
    I2C = auto()
    SPI = auto()
    CAN = auto()
    USB = auto()
    I2S = auto()
    IR = auto()

    ADC = auto()
    DAC = auto()
    COMP = auto()
    OPAMP = auto()


class SysSignals(Enum):
    WKUP1 = auto()
    SWDIO = auto()
    SWCLK = auto()
    SWO = auto()
    JTMS = auto()
    JTCK = auto()
    JTDI = auto()
    JTDO = auto()
    JTRST = auto()


class RccSignals(Enum):
    OSC_IN = auto()
    OSC_OUT = auto()
    MCO = auto()


class TimSignals(Enum):
    CH1 = auto()
    CH2 = auto()
    CH3 = auto()
    CH4 = auto()

    CH5 = auto()
    CH6 = auto()

    CH1N = auto()
    CH2N = auto()
    CH3N = auto()
    CH4N = auto()

    BKIN = auto()
    BKIN2 = auto()
    ETR = auto()


class RtcSignals(Enum):
    TAMP2 = auto()
    REFIN = auto()


class UsartSignals(Enum):
    TX = auto()
    RX = auto()
    CTS = auto()
    RTS = auto()
    CK = auto()
    DE = auto()


class I2cSignals(Enum):
    SDA = auto()
    SCL = auto()
    SMBA = auto()


class SpiSignals(Enum):
    MOSI = auto()
    MISO = auto()
    SCK = auto()
    CS = auto()


class CanSignals(Enum):
    TX = auto()
    RX = auto()


class UsbSignals(Enum):
    DM = auto()
    DP = auto()


class I2sSignals(Enum):
    CKIN = auto()
    SD = auto()
    EXT_SD = auto()
    WS = auto()
    CK = auto()
    MCK = auto()


class IrSignals(Enum):
    OUT = auto()


class CompSignals(Enum):
    INM = auto()
    INP = auto()
    OUT = auto()


class OpampSignals(Enum):
    VINM = auto()
    VINP = auto()
    VINM_SEC = auto()
    VINP_SEC = auto()
    VOUT = auto()


@dataclass
class Signal:
    raw_name: str
    type: BankType
    bank: int
    signal: Enum | int


@dataclass
class Pin:
    id: int
    name: str
    position: int
    signals: [Signal]


@dataclass
class Feature:
    name: str
    type: BankType
    signals: [Enum | int]


REPLACEMENTS = (
    ("NJTRST", "JTRST"),
    ("NSS", "CS"),
    ("JTDO-TRACESWO", "SWO"),
    ("JTMS-SWDIO", "SWDIO"),
    ("JTCK-SWCLK", "SWCLK"),
)

EXCLUSIVE_BANK_TYPES = (BankType.GPIO, BankType.ADC, BankType.DAC)
