import logging
import os, errno

def get_logger(logger_name, logging_level):

    logfile_dir = '../logs'
    if not os.path.exists(logfile_dir):
        try:
            os.makedirs(logfile_dir)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

    logfile_name = f"{logfile_dir}/{logger_name}.log"
    if not os.path.exists(logfile_name):
        try:
            open(logfile_name, 'a').close()
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

    py_logger = logging.getLogger(logfile_name)
    py_logger.setLevel(logging_level)

    py_handler = logging.FileHandler(logfile_name)
    py_formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

    py_handler.setFormatter(py_formatter)
    py_logger.addHandler(py_handler)
    return py_logger
