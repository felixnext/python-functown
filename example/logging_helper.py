import logging


class ListHandler(logging.Handler):
    """List handler that retrives a reference to a list to append logs to"""

    def __init__(self, log_list):
        logging.Handler.__init__(self)
        self.log_list = log_list

    def emit(self, record):
        # record.message is the log message
        self.log_list.append(record.msg)
