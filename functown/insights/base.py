from typing import List

from functown.utils import BaseDecorator


class InsightsDecorator(BaseDecorator):
    """Base Class for Application insights decorators."""

    def __init__(self, instrumentation_key: str, added_kw: List[str], **kwargs):
        super().__init__(None, added_kw=added_kw, **kwargs)

        if instrumentation_key is None:
            raise ValueError("No instrumentation key provided.")

        self.instrumentation_key = instrumentation_key
