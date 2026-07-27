from dataclasses import dataclass
from typing import Optional
from enum import Enum, auto


class Resolution(Enum):
    HD = (1920, 1080)
    QHD = (2560, 1440)
    UHD = (3840, 2160)


class BitsPerPixel(Enum):
    ONE = 1
    TWO = 2
    THREE = 3


class Browser(Enum):
    CHROME = auto()
    FIREFOX = auto()
    OPERA = auto()
    EDGE = auto()
    CHROMIUM = auto()
    BRAVE = auto()


@dataclass
class Settings:
    _resolution: Resolution = Resolution.HD
    _bits_per_pixel: BitsPerPixel = BitsPerPixel.ONE
    _ecc_symbols: int = 32
    _constant_rate_factor: int = 18
    _null_frames: bool = False
    _browser: Optional[Browser] = None
    _encryption_password: Optional[str] = None

    def __init__(
        self,
        resolution: Resolution = Resolution.HD,
        bits_per_pixel: BitsPerPixel = BitsPerPixel.ONE,
        ecc_symbols: int = 32,
        constant_rate_factor: int = 18,
        null_frames: bool = False,
        browser: Optional[Browser] = None,
        encryption_password: Optional[str] = None,
    ) -> None:
        self.resolution = resolution
        self.bits_per_pixel = bits_per_pixel
        self.ecc_symbols = ecc_symbols
        self.constant_rate_factor = constant_rate_factor
        self.null_frames = null_frames
        self.browser = browser
        self.encryption_password = encryption_password

    @property
    def resolution(self) -> Resolution:
        return self._resolution

    @resolution.setter
    def resolution(self, value: Resolution) -> None:
        if not isinstance(value, Resolution):
            raise ValueError("Value must be a Resolution object.")
        self._resolution = value

    @property
    def bits_per_pixel(self) -> BitsPerPixel:
        return self._bits_per_pixel

    @bits_per_pixel.setter
    def bits_per_pixel(self, value: BitsPerPixel) -> None:
        if not isinstance(value, BitsPerPixel):
            raise ValueError("Value must be a BitsPerPixel object.")
        self._bits_per_pixel = value

    @property
    def ecc_symbols(self) -> int:
        return self._ecc_symbols

    @ecc_symbols.setter
    def ecc_symbols(self, value: int) -> None:
        if not 0 <= value < 255:
            raise ValueError("Value must be between 0 and 254 inclusive.")
        self._ecc_symbols = value

    @property
    def constant_rate_factor(self) -> int:
        return self._constant_rate_factor

    @constant_rate_factor.setter
    def constant_rate_factor(self, value: int) -> None:
        if not 0 <= value <= 52:
            raise ValueError("Value must be between 0 and 52 inclusive.")
        self._constant_rate_factor = value

    @property
    def null_frames(self) -> bool:
        return self._null_frames

    @null_frames.setter
    def null_frames(self, value: Optional[bool]) -> None:
        if not isinstance(value, bool):
            raise ValueError("Value must be a boolean.")
        self._null_frames = value

    @property
    def browser(self) -> Browser:
        return self._browser

    @browser.setter
    def browser(self, value: Browser) -> None:
        if not isinstance(value, Browser) and value is not None:
            raise ValueError("Value must be a Browser or None.")
        self._browser = value

    @property
    def encryption_password(self) -> Optional[str]:
        return self._encryption_password

    @encryption_password.setter
    def encryption_password(self, value: Optional[str]) -> None:
        if not isinstance(value, str) and value is not None:
            raise ValueError("Value must be a string or None.")
        if isinstance(value, str) and not value:
            raise ValueError("Encryption password cannot be an empty string.")
        self._encryption_password = value

    @property
    def encryption_enabled(self) -> bool:
        """Returns True if encryption is enabled."""
        return self._encryption_password is not None
