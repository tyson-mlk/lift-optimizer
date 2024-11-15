import logging

def get_logger(logger_filename, logging_level):
    py_logger = logging.getLogger(logger_filename)
    py_logger.setLevel(logging_level)

    py_handler = logging.FileHandler(f"../logs/{logger_filename}.log")
    py_formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

    py_handler.setFormatter(py_formatter)
    py_logger.addHandler(py_handler)
    return py_logger
