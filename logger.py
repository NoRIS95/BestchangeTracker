import os
import logging
from logging.handlers import RotatingFileHandler
from configs import LOG_DIR

class CustomRotatingFileHandler(RotatingFileHandler):
    def __init__(self, filename, maxBytes=0, backupCount=0, encoding=None, delay=False):
        super().__init__(filename, maxBytes=maxBytes, backupCount=backupCount, encoding=encoding, delay=delay)

    def doRollover(self):
        """
        Переопределяем метод doRollover, чтобы изменить способ именования резервных файлов.
        """
        if self.stream:
            self.stream.close()
            self.stream = None
        
        # Перемещаем существующие файлы
        for i in range(self.backupCount - 1, 0, -1):
            base, ext = os.path.splitext(self.baseFilename)
            sfn = f"{base}{i}{ext}"
            dfn = f"{base}{i+1}{ext}"
            if os.path.exists(sfn):
                if os.path.exists(dfn):
                    os.remove(dfn)
                os.rename(sfn, dfn)
        
        # Переименование текущего файла в первый резервный
        base, ext = os.path.splitext(self.baseFilename)
        dfn = f"{base}1{ext}"
        if os.path.exists(self.baseFilename):
            if os.path.exists(dfn):
                os.remove(dfn)
            os.rename(self.baseFilename, dfn)
        
        # Создаем новый пустой файл
        if not self.delay:
            self.stream = self._open()


def setup_logger():
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    LOG_FILE = os.path.join(LOG_DIR, 'debug.log')
    MAX_SIZE = 10 * 1024 * 1024  # 10 MB
    BACKUP_COUNT = 10

    handler = CustomRotatingFileHandler(LOG_FILE, maxBytes=MAX_SIZE, backupCount=BACKUP_COUNT)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)


    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)

    # logger.handlers[0].doRollover()