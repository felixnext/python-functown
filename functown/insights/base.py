from functown.utils import BaseDecorator


class InsightsDecorator(BaseDecorator):
    """Base Class for Application insights decorators."""

    def __init__(self, instrumentation_key: str, **kwargs):
        super().__init__(None, **kwargs)
        self.instrumentation_key = instrumentation_key
