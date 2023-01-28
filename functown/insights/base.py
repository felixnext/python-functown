from typing import List
import logging

from functown.utils import BaseDecorator


class InsightsDecorator(BaseDecorator):
    """Base Class for Application insights decorators."""

    def __init__(self, instrumentation_key: str, added_kw: List[str], **kwargs):
        super().__init__(None, added_kw=added_kw, **kwargs)

        if instrumentation_key is None:
            logging.warning(
                "No instrumentation key provided. "
                "No data will be sent to Application Insights "
                f"({self.__class__.__name__})."
            )

        self.instrumentation_key = instrumentation_key
