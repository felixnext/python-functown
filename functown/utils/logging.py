import logging


class LogListHandler(logging.Handler):
    """List handler that retrives a reference to a list to append logs to

    Usage:

    ```python
    log_list = []
    logger = logging.getLogger()
    logger.addHandler(LogListHandler(log_list))

    # do stuff
    # log_list now contains all logs
    ```

    """

    def __init__(self, log_list):
        logging.Handler.__init__(self)
        self.log_list = log_list

    def emit(self, record):
        # record.message is the log message
        self.log_list.append(record.msg)
