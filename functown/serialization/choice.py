"""Decorator for Mime-Type Choice Handling.

Allows to provide multiple sub-decorators that are executed dependend on the mime-type
of the request.

Copyright (c) 2023 Felix Geilert
"""

from typing import Dict, Union


from functown.args import ContentTypes
from functown.utils import BaseDecorator, StackDecorator


class ChoiceDecorator(StackDecorator):
    def __init__(
        self,
        choices: Dict[Union[str, ContentTypes], BaseDecorator],
        use_singleton: bool,
        **kwargs
    ):
        # TODO: pass
        super().__init__(stack, added_kw, **kwargs)

    # TODO: apply the decorators based on mime-type
