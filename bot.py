import asyncio

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor

from configs import *
from callbacks import get_crypt_info
from classes import StatusDialog, Form


@dp.message_handler(commands=["start"])
async def hello_message(message):
    user_id = str(message.from_user.id)
    await bot.send_message(message.chat.id, f'Здравствуйте, {message.from_user.first_name}! Для подробной информации введите /info')
    USER_CONDITIONS.data[user_id] = StatusDialog.STATUS_INFO.value

@dp.message_handler(commands=['info'])
async def get_user_info(message):
    markup_reply = types.ReplyKeyboardMarkup()
    item_yes = types.KeyboardButton(text='ДА')
    item_no = types.KeyboardButton(text='НЕТ')

    markup_reply.add(item_yes, item_no)
    await bot.send_message(message.chat.id, 'Желаете узнать текущую информацию о криптовалютах?', reply_markup=markup_reply)
    
    # Явно устанавливаем состояние
    await Form.waiting_for_confirmation.set()

@dp.message_handler(state=Form.waiting_for_confirmation)
async def handle_confirmation(message: types.Message, state: FSMContext):
    # global TASK_CHANGE_MANAGER, TASK_TELEGRAM_OBSERVER, CHANGE_MANAGER, TELEGRAM_OBSERVER
    global CHANGE_MANAGER
    user_id = str(message.from_user.id)
    chat_id = message.chat.id

    if user_id in USER_CONDITIONS.data:
        if USER_CONDITIONS.data[user_id] == StatusDialog.STATUS_INFO.value \
              or USER_CONDITIONS.data[user_id] == StatusDialog.STATUS_OF_ASK_CRIPT.value:
            if message.text == "ДА":
                CHANGE_MANAGER, message_to_send = await asyncio.create_task(get_crypt_info(bot, user_id, chat_id))
                await bot.send_message(chat_id, message_to_send, parse_mode="HTML")
            elif message.text == "Обновить":
                message_to_send = await CHANGE_MANAGER.notify_observers()
                await bot.send_message(chat_id, message_to_send, parse_mode="HTML")


    # Сбрасываем состояние, чтобы оно могло быть установлено заново
    await state.finish()
    
    markup_reply = types.ReplyKeyboardMarkup()
    item_reload = types.KeyboardButton(text='Обновить')
    markup_reply.add(item_reload)
    await bot.send_message(message.chat.id, 'Чтобы узнать информацию еще раз, нажмите кнопку "Обновить"', reply_markup=markup_reply)
    
    # Устанавливаем состояние заново
    await Form.waiting_for_confirmation.set()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)