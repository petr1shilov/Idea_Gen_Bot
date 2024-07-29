import asyncio

from aiogram import Bot, Dispatcher, F, types
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.state import default_state
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    InputFile,
    CallbackQuery,
    ErrorEvent,
    InputSticker,
    Message,
    ReplyKeyboardRemove,
    ContentType,
    FSInputFile,
)
from aiogram.utils.deep_linking import create_start_link

import config

from bot.keyboards import kb, model_kb
from bot.states import UserStates
from bot.texts import *
from api import IdeaGenAPI

TOKEN = config.bot_token

# Добавить описания функций
# Нужно для поднятия локальной базы, что бы созранять передменные
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
bot = Bot(TOKEN)
api = IdeaGenAPI()


@dp.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext) -> None:
    await message.answer(hello_message_text)
    await message.answer(start_message_text, reply_markup=kb)


@dp.message(F.text.in_([button_text_gen, button_text_agents,button_text_dialog_len,
            button_text_theme]))
async def button_taped(message: Message, state: FSMContext):
    if message.text == button_text_gen:
        await message.answer(text_for_gen)
        user_data = await state.get_data()
        agents = user_data["agents"]
        theme = user_data["theme"]
        dialog_len = user_data["dialog_len"]
        convers_history, total_answer = api.get_answer(agents, theme, dialog_len)
        for answer in convers_history:
            await message.answer(f'{list(answer.keys())[0]}\n{list(answer.values())[0]}\n')
        await message.answer(total_answer)
        await state.clear()
    elif message.text == button_text_agents:
        await message.answer(text_for_agent)
        await state.set_state(UserStates.get_agents)
    elif message.text == button_text_dialog_len:
        await message.answer(text_for_dialog_len)
        await state.set_state(UserStates.get_len)
    elif message.text == button_text_theme:
        await message.answer(text_for_theme)
        await state.set_state(UserStates.get_theme)

# @dp.message(F.text == button_text_model)
# async def get_model(message: Message, state: FSMContext):
#     await message.answer(text_for_model_select, reply_markup=model_kb)
#     await state.set_state(UserStates.get_model)


@dp.message(StateFilter(UserStates.get_agents), F.content_type == "text")
async def get_agent(message: Message, state: FSMContext):
    await state.update_data(agents=message.text)
    answer = api.parsing_agents(message.text)
    name_agents = ', '.join(answer.keys())
    await message.answer(f'Вы ввели {len(answer)} агентов:\n{name_agents}')


@dp.message(StateFilter(UserStates.get_len), F.content_type == "text")
async def get_len(message: Message, state: FSMContext):
    text_messege = message.text
    await state.update_data(dialog_len=int(text_messege))
    await message.answer(f'Вы ввели длину = {text_messege}')


@dp.message(StateFilter(UserStates.get_theme), F.content_type == "text")
async def get_theme(message: Message, state: FSMContext):
    text_messege = message.text
    await state.update_data(theme=text_messege)
    await message.answer(f'Тема диалога: {text_messege}')

@dp.message(StateFilter(UserStates.get_model), F.text.in_([button_text_model_1, button_text_model_2]))
async def set_model_params(message: Message, state: FSMContext):
    new_model = message.text
    api.set_model(new_model)
    await message.answer(f'Вы выбрали модель: {new_model}', reply_markup=kb)

if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))
