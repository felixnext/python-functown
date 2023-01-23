"""Decorator base class.

Used for stackable decorators to avoid boilerplate and clean at the out layer.

Copyright (c) 2023, Felix Geilert
"""


import logging
from inspect import Parameter, Signature, signature
import traceback
from typing import Dict, Any, Union, List, Callable, Tuple


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
    __decorator_count: Dict[int, Tuple[int, int]] = {}

    def __init__(
        self,
        func=None,
        added_kw: List[str] = None,
        mask_signature: bool = True,
        **kwargs,
    ):
        # NOTE: this retrieves either only `func` (in non-init case) or decorator parameters
        # check if a function is passed (in case of @BaseDecorator, i.e. non-init)
        self.func = func
        self._is_init = func is None

        # create basic variables
        self.mask_signature = mask_signature
        self.added_kw = added_kw if added_kw else []
        self.__address = None

    @property
    def level(self) -> Union[int, None]:
        """Returns the level of the decorator (i.e. how many other decorators have been called before).

        First decorator is level 0, second is level 1, etc.
        """
        tpl = self.__class__.__decorator_count.get(self.__address, None)
        if tpl is None:
            return None
        return tpl[0] - 1

    @property
    def max_level(self) -> Union[int, None]:
        # retrieve current data
        if self.__address is None:
            return None
        tpl = self.__class__.__decorator_count.get(self.__address, None)
        if tpl is None:
            return None

        # find the max level
        base_id = tpl[1]
        max_lvl = tpl[0]
        for lvl, ref_id in self.__class__.__decorator_count.values():
            if ref_id == base_id and lvl > max_lvl:
                max_lvl = lvl
        return max_lvl - 1

    @property
    def is_first_decorator(self) -> Union[bool, None]:
        """Returns True if this is the first decorator in the stack (i.e. outermost)."""
        if self.__address is None:
            return None

        # get current data
        cur_lvl, base_id = self.__class__.__decorator_count[self.__address]

        # validate if higher data
        for lvl, addr in self.__class__.__decorator_count.values():
            if addr == base_id and lvl > cur_lvl:
                return False
        return True

    @property
    def is_last_decorator(self) -> bool:
        """Returns True if this is the last decorator in the stack (i.e. innermost)."""
        return self.level == 0

    def _get(self, name: str, pos: int = 0, *args, **kwargs) -> Union[Any, None]:
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

    def __increase_count(self, id_func, id_exec):
        """Retrieves the function id and increases the count of the decorator."""
        self.__address = id_exec
        if self.is_last_decorator is True:
            self.__class__.__decorator_count[self.__address] = (1, None)
        else:
            self.__class__.__decorator_count[self.__address] = (
                self.__class__.__decorator_count[id_func][0] + 1,
                id_func,
            )

    def __modify_sig(self, sig: Signature, kws: List[str]) -> Signature:
        """Removes the given keywords from the signature."""
        kws = [kw for kw in kws if kw in sig.parameters]
        if kws:
            sig = sig.replace(
                parameters=[p for p in sig.parameters.values() if p.name not in kws]
            )

        return sig

    def __id(self, func):
        """Returns the id of the function.

        self.level = len([member for member in inspect.getmembers(self.func) if inspect.isfunction(member[1]) and member[1].__name__ == "wrapped"])
        """
        return id(func)

    def __call__(self, *args, **kwargs) -> Union[Any, Callable[[Any], Any]]:
        """Call the decorator.

        Note that if the function is not passed to the init (only for @BaseDecorator),
        This function is always passed here

        This function has two call modes:
        - non-init decorator: retrieves the call arguments from the inner function and
            returns function result.
        - init decorator: retrieves only the `func` as call argument and returns an
            updated function object.
        """
        # check the case
        if self._is_init is True:
            # retrieve the function from the arguments
            self.func = self._get("func", 0, *args, **kwargs)

            def execute(*args, **kwargs):
                return self.run(self.func, *args, **kwargs)

            # clean additional arguments from the signature return for the outer decorator
            if self.mask_signature:
                sig = signature(self.func)
                kws = [
                    kw
                    for kw in sig.parameters
                    if sig.parameters[kw].kind
                    in [Parameter.VAR_KEYWORD, Parameter.VAR_POSITIONAL]
                ]
                execute.__signature__ = self.__modify_sig(sig, self.added_kw + kws)

            # update the reference pointer
            base_id = None
            self.__address = id(self)
            level = 0
            if self.func.__closure__ is None:
                base_id = id(self.func)
                self.__class__.__decorator_count[base_id] = (level, None)
            else:
                obj = [
                    cl.cell_contents
                    for cl in self.func.__closure__
                    if cl.cell_contents is not None
                ]
                if len(obj) == 0:
                    base_id = id(self.func)
                    self.__class__.__decorator_count[base_id] = (level, None)
                else:
                    ref_id = id(obj[0])
                    if ref_id not in self.__class__.__decorator_count:
                        base_id = id(self.func)
                        self.__class__.__decorator_count[base_id] = (level, None)
                    else:
                        level, base_id = self.__class__.__decorator_count[ref_id]
            self.__class__.__decorator_count[self.__address] = (level + 1, base_id)
            # self.__increase_count(self.__id(self.func), self.__id(execute))

            return execute

        # --- code for non-init decorator ---
        # if the function is passed to the init, just run the function
        self.__increase_count(self.__id(self.func), self.__id(self))
        return self.run(self.func, *args, **kwargs)
