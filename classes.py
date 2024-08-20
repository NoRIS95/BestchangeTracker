import os
import enum

from dotenv import load_dotenv
from aiogram.dispatcher.filters.state import State, StatesGroup

class Tg_bot:
    load_dotenv()
    def __init__(self):
        self.__bot_token = os.getenv('BOT_TOKEN')
    
    def get_bot_token(self):
        return self.__bot_token

class StatusDialog(enum.Enum):
    STATUS_OF_GREEЕTINGS = 1
    STATUS_INFO = 2
    STATUS_OF_ASK_CRIPT = 3

class Form(StatesGroup):
    waiting_for_confirmation = State()