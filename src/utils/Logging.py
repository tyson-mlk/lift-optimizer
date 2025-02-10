import logging
import os, errno
import streamlit as st

def get_logger(logger_name, logger_class, logging_level):

    logfile_dir = '../logs'
    if not os.path.exists(logfile_dir):
        try:
            os.makedirs(logfile_dir)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

    if logging_level == logging.INFO:
        logfile_name = f"{logfile_dir}/{logger_class}.log"
    elif logging_level == logging.DEBUG:
        logfile_name = f"{logfile_dir}/{logger_class}_detail.log"

    if not os.path.exists(logfile_name):
        try:
            open(logfile_name, 'a').close()
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

    py_logger = logging.getLogger(logger_name)
    py_logger.setLevel(logging_level)

    py_handler = logging.FileHandler(logfile_name)
    py_formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

    py_handler.setFormatter(py_formatter)
    py_logger.addHandler(py_handler)
    return py_logger

def print_st(*args):
    from src.base.PassengerList import PASSENGERS

    print(*args)
    msg = ' '.join([str(a) for a in args])
    if PASSENGERS.visual_lock.locked():
        PASSENGERS.visual_lock.release()
    PASSENGERS.print_queue.put_nowait(msg)
