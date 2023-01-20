"""Decorator base class.

Used for stackable decorators to avoid boilerplate and clean at the out layer.

Copyright (c) 2023, Felix Geilert
"""


from abc import abstractmethod
import functools
import logging


class BaseDecorator(object):
    """Base Decorator class.

    This decorator can either be used without init or with init:
    - without init: @BaseDecorator
    - with init: @BaseDecorator()

    Note that the variant with init is advised, as it preserves the signature of the inner function.
    """

    decorator_count = 0

    def __init__(self, func=None, mask_outer=True, **kwargs):
        # check if a function is passed (in case of @BaseDecorator)
        self.func = func
        # update the count
        self.__class__.decorator_count += 1

        # variable to check if the decorator is the outermost one
        self.is_outer = self.__class__.decorator_count == 1
        self.mask_outer = mask_outer

    def _get(self, name: str, pos=0, *args, **kwargs):
        """Retrieves an item either by name or by position."""
        if name in kwargs:
            return kwargs[name]
        if len(args) > pos:
            return args[pos]
        return None

    def _create_logger(
        self, force_clean: bool = True, name="logger", *args, **kwargs
    ) -> logging.Logger:
        """Creates a logger for the function."""
        logger = self._get(name, *args, **kwargs)
        if logger is None or force_clean is True:
            name = self.__class__.__name__
            logging.debug(f"Creating logger for {name}")
            logger = logging.getLogger(name)
        return logger

    @abstractmethod
    def run(self, func, *args, **kwargs):
        """Implement this function with additional parameters as the actual decorator logic.

        In order to have proper function of the inner function,
        this should always end with a return func(*args, **kwargs).
        """
        raise NotImplementedError

    def __call__(self, *args, **kwargs):
        """Call the decorator.

        Note that if the function is not passed to the init (only for @BaseDecorator),
        This function is always passed here
        """
        # check if the function is passed directly
        if self.func is None:
            # retrieve the function from the arguments
            self.func = args[0]

            @functools.wraps(self.func)
            def execute(*args, **kwargs):
                return self.run(self.func, *args, **kwargs)

            return execute

        # if the function is passed to the init, just run the function
        return self.run(self.func, *args, **kwargs)
