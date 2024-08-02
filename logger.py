import os
import logging
from logging.handlers import RotatingFileHandler
from configs import LOG_DIR


def setup_logger():
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    LOG_FILE = os.path.join(LOG_DIR, 'debug.log')
    MAX_SIZE = 10 * 1024 * 1024  # 10 MB
    BACKUP_COUNT = 10

    handler = RotatingFileHandler(LOG_FILE, maxBytes=MAX_SIZE, backupCount=BACKUP_COUNT)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)


    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)

    logger.handlers[0].doRollover()