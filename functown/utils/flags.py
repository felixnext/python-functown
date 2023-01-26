"""Helper Functions to retrieve flags from Azure Environments.

Copyright (c) 2023, Felix Geilert
"""

import os
from distutils.util import strtobool
from typing import Optional


def get_config(name: str, default: Optional[str] = None) -> Optional[str]:
    """Retrieves a configuration value from the Azure Function Environment.

    Args:
        name (str): Name of the configuration value.
        default (Optional[str], optional): Default value if the configuration value is
            not set. Defaults to `None`.
    """
    return os.environ.get(name, default)


def get_flag(name: str, default: bool = False) -> bool:
    """Retrieves a flag from the Azure Function Environment.

    Args:
        name (str): Name of the flag.
        default (bool, optional): Default value if the flag is not set. Defaults to
            `False`.
    """
    return bool(strtobool(os.environ.get(name, str(default))))
