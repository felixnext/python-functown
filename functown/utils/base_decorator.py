"""Decorator base class.

Used for stackable decorators to avoid boilerplate and clean at the out layer.

Copyright (c) 2023, Felix Geilert
"""


import logging
from inspect import Signature, Parameter, signature
from typing import Dict, Any, Union, List

from uuid import uuid4 as uuid


ADDRESS_PARAM = "_address"


class BaseDecorator(object):
    """Base Decorator class.

    This decorator can either be used without init or with init:
    - without init: @BaseDecorator
    - with init: @BaseDecorator()

    Note that the variant with init is advised, as it preserves the signature of the inner function.

    You can disable the non-init variant by removing the func parameter from the init.

    ```python
    class MyDecorator(BaseDecorator):
        def __init__(self, *args, **kwargs):
            super().__init__(None, *args, **kwargs)

        # ...
    ```

    In order to properly mask the signature, each implementation has to pass the addded_kw
    parameter for each added keyword to the function signature.
    """

    # internal counter to keep track of the decorator level per function
    # NOTE: this has to be done on a class level, since each decorator is a new instance
    __decorator_count: Dict[int, int] = {}
    # last seen signature
    # NOTE: this is used to clean up the outer function layer
    __inner_signature: Dict[int, Signature] = {}

    def __init__(
        self,
        func=None,
        added_kw: List[str] = None,
        mask_signature: bool = True,
        **kwargs,
    ):
        # check if a function is passed (in case of @BaseDecorator)
        self.func = func
        self.is_outer = True
        self.mask_signature = mask_signature
        self.added_kw = added_kw if added_kw else []
        self.__address = None

    @property
    def level(self) -> int:
        """Returns the level of the decorator (i.e. how many other decorators have been called before).

        First decorator is level 0, second is level 1, etc.
        """
        return self.__class__.__decorator_count[self.__address] - 1

    def _get(self, name: str, pos=0, *args, **kwargs) -> Union[Any, None]:
        """Retrieves an item either by name or by position."""
        if name in kwargs:
            return kwargs[name]
        if len(args) > pos:
            return args[pos]
        return None

    def _create_logger(
        self, force_clean: bool = False, name="logger", *args, **kwargs
    ) -> logging.Logger:
        """Creates a logger for the function.

        If the logger is already passed, it is returned.

        Args:
            force_clean (bool, optional): If True, the logger is always created. Defaults to False.
            name (str, optional): The name of the logger. Defaults to "logger".

        Returns:
            logging.Logger: The logger.
        """
        logger = self._get(name, *args, **kwargs)
        if logger is None or force_clean is True:
            name = self.__class__.__name__
            logging.debug(f"Creating logger for {name}")
            logger = logging.getLogger(name)
        return logger

    def run(self, func, *args, **kwargs):
        """Implement this function with additional parameters as the actual decorator logic.

        In this form, this is just a pass through.

        In order to have proper function of the inner function,
        this should always end with a return func(*args, **kwargs).
        """
        return func(*args, **kwargs)

    def __increase_count(self, func, address):
        """Retrieves the function id and increases the count of the decorator."""
        # check if the function is already registered
        if address not in self.__decorator_count:
            self.__class__.__decorator_count[address] = 0

        # increase the count
        self.__class__.__decorator_count[address] += 1
        if self.__class__.__decorator_count[address] > 1:
            self.is_outer = False

        # update the inner signature
        self.__class__.__inner_signature[address] = signature(func)

    def __call__(self, *args, **kwargs):
        """Call the decorator.

        Note that if the function is not passed to the init (only for @BaseDecorator),
        This function is always passed here
        """
        # check if the function is passed directly
        if self.func is None:
            # retrieve the function from the arguments
            self.func = args[0]

            # check if self.func is part of another BaseDecorator call
            is_decorator = self.func.__qualname__.startswith("BaseDecorator")

            # FIXME: find solution for counting
            if is_decorator == False:
                # TODO:
                pass

            def execute(*args, **kwargs):
                # check to get address from kwargs (or generate)
                self.__address = kwargs.get(ADDRESS_PARAM, uuid().hex)
                self.__increase_count(self.func, self.__address)

                # check if self.func is a call on the BaseDecorator object
                if is_decorator:
                    kwargs[ADDRESS_PARAM] = self.__address
                    return self.run(self.func, *args, **kwargs)

                # check if the address should be removed
                if ADDRESS_PARAM in kwargs:
                    del kwargs[ADDRESS_PARAM]
                return self.run(self.func, *args, **kwargs)

            # clean additional arguments from the signature return for the outer decorator
            if self.mask_signature:
                sig = self.__class__.__inner_signature.get(self.__address)

                # get all parameters to replace
                kws = self.added_kw

                # if this is the outer decorator, add all keywords that start with * or **
                if self.is_outer:
                    # find all keywords that start with * or ** and add them to the list
                    for kw in sig.parameters:
                        p = sig.parameters[kw]
                        if (
                            p.kind == Parameter.VAR_KEYWORD
                            or p.kind == Parameter.VAR_POSITIONAL
                        ):
                            kws.append(kw)

                # replace the parameters
                kws = [kw for kw in kws if kw in sig.parameters]
                if kws:
                    sig = sig.replace(
                        parameters=[
                            p for p in sig.parameters.values() if p.name not in kws
                        ]
                    )

                # update the signature
                execute.__signature__ = sig

            return execute

        # if the function is passed to the init, just run the function
        self.__increase_count(self.func)
        return self.run(self.func, *args, **kwargs)
