from __future__ import annotations

from typing import Literal

GL_ACCOUNTS: tuple[str, ...] = (
    "6000 - Cleaning Services",
    "6010 - Maintenance & Repairs",
    "6020 - Electrical Services",
    "6030 - Plumbing Services",
    "6040 - Equipment & Machinery",
    "6050 - Facility Supplies",
    "6060 - Utilities",
    "6070 - Fuel & Vehicle Expenses",
    "6080 - Professional Services",
    "6090 - Miscellaneous Facility Expenses",
)

GLAccount = Literal[*GL_ACCOUNTS]


class InvalidGLAccountError(ValueError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(f"{code!r} is not a valid Delta GL account code.")


def validate_gl_account_code(code: str) -> None:
    if code not in GL_ACCOUNTS:
        raise InvalidGLAccountError(code)
