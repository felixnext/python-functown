'''
Bunch of Handler Code for Arguments
'''


from distutils.util import strtobool
import logging

from azure.functions import HttpRequest

from functown.errors import ArgError


class RequestArgHandler():
    def __init__(self, req: HttpRequest):
        self.req = req

    def _convert(self, name, arg, required=False, map_fct=None, allowed=None, list_map=None, default=None):
        # check if required
        if required and not arg:
            raise ArgError(f"Argument {name} is not set, but required!")

        # define mapping
        if map_fct and arg:
            if isinstance(map_fct, str):
                if map_fct == "bool":
                    arg = bool(strtobool(arg))
                else:
                    arg = getattr(arg, map_fct)()
            else:
                arg = map_fct(arg)

        # check for default
        if not arg and default:
            arg = default

        # checks if in list
        if allowed and arg:
            # check for mapping
            if list_map and isinstance(list_map, str):
                ls_arg = getattr(arg, list_map)()
            else:
                ls_arg = list_map(arg) if list_map else arg

            # check if value found
            if ls_arg not in allowed:
                raise ArgError(f"Argument {name} should be one of {allowed} but got {arg}")

        return arg

    def _parse_body(self, name):
        arg = None
        try:
            body = self.req.get_json()
            arg = body[name] if name in body else None
        except Exception:
            logging.warning("Could not parse request body to json")
        return arg

    def get_body(self, name, required=False, map_fct=None, allowed=None, list_map=None, default=None):
        arg = self._parse_body(name)
        return self._convert(name, arg, required, map_fct, allowed, list_map, default)

    def get_query(self, name, required=False, map_fct=None, allowed=None, list_map=None, default=None):
        arg = self.req.params.get(name)
        return self._convert(name, arg, required, map_fct, allowed, list_map, default)

    def get_route(self, name, required=False, map_fct=None, allowed=None, list_map=None, default=None):
        arg = self.req.route_params.get(name)
        return self._convert(name, arg, required, map_fct, allowed, list_map, default)

    def get_body_query(self, name, required=False, map_fct=None, allowed=None, list_map=None, default=None):
        arg = self.req.params.get(name)
        if not arg and self.req.get_body():
            arg = self._parse_body(name)
        return self._convert(name, arg, required, map_fct, allowed, list_map, default)

    def get_form(self, name: str, required: bool = False, map_fct=None, allowed=None, list_map=None, default=None):
        arg = None
        try:
            arg = self.req.form[name]
        except Exception as ex:
            logging.warning(f"Form value {name} could not be parsed: {ex}")
        return self._convert(name, arg, required, map_fct, allowed, list_map, default)

    def get_file(self, name: str, required: bool = False):
        '''Parses a file from the form data of the request'''
        file = None

        # retrieve data
        try:
            file = self.req.files[name]
        except Exception as ex:
            logging.warning(f"File {name} could not be parsed: {ex}")

        # check if provided
        if required and not file:
            raise ArgError(f"File {name} could not be parsed")

        return file
