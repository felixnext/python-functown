"""Callbacks for filtering and modifying Azure Application Insights."""

import os
import sys
from typing import Callable

from opencensus.ext.azure.log_exporter import Envelope


def modify_system_info(envelop: Envelope) -> bool:
    """Appends System information (os, python, cpu, memory) to the message.

    Args:
        envelop (Envelope): The telemetry item.

    Returns:
        bool: Whether to keep the item.
    """
    system_info = (
        f"System: {sys.platform} {sys.version} {os.cpu_count()} {os.getloadavg()}"
    )
    envelop.data.base_data.message = f"{envelop.data.base_data.message} {system_info}"

    return True


def filter_debug(envelop: Envelope) -> bool:
    """Filter to remove debug messages from Azure Application Insights.

    Args:
        envelop (Envelope): The telemetry item.

    Returns:
        bool: Whether to keep the item.
    """
    if envelop.data.base_data.severity_level == 1:
        return False
    return True


def create_filter_ids(cur_id, ids: list) -> Callable[[Envelope], bool]:
    """Create a filter to remove specific ids from Azure Application Insights.

    Args:
        cur_id (str): The current id of the function.
        ids (list): A list of ids to remove.

    Returns:
        Callable[[Envelope], bool]: A filter function.
    """

    def filter_ids(envelop: Envelope) -> bool:
        """Filter to remove specific ids from Azure Application Insights.

        Args:
            envelop (Envelope): The telemetry item.

        Returns:
            bool: Whether to keep the item.
        """
        if cur_id in ids:
            return False
        return True

    return filter_ids


def create_filter_keywords(keywords: list) -> Callable[[Envelope], bool]:
    """Create a filter to remove specific keywords from Azure Application Insights.

    Args:
        keywords (list): A list of keywords to remove.

    Returns:
        Callable[[Envelope], bool]: A filter function.
    """

    def filter_keywords(envelop: Envelope) -> bool:
        """Filter to remove specific keywords from Azure Application Insights.

        Args:
            envelop (Envelope): The telemetry item.

        Returns:
            bool: Whether to keep the item.
        """
        for keyword in keywords:
            if keyword in envelop.data.base_data.message:
                return False
        return True

    return filter_keywords
