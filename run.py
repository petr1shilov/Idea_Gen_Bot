import argparse
import asyncio
import base64
import fitz
import os
import time


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

from bot.keyboards import kb
from bot.states import UserStates
from bot.texts import *
from api import IdeaGenAPI

TOKEN = config.test_api_key

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
            button_text_them,button_text_instrustion]))
async def button_taped(message: Message, state: FSMContext):
    if message.text == button_text_gen:
        await message.answer(message.text)
        await message.answer(text_for_gen)
        user_data = await state.get_data()
        agents = user_data["agents"]
        them = user_data["them"]
        dialog_len = user_data["dialog_len"]
        convers_history, answer = api.get_answer(agents, them, dialog_len)
        for mes in convers_history:
            await message.answer(mes)
        await message.answer(answer)

    elif message.text == button_text_agents:
        await message.answer(message.text)
        await message.answer(text_for_agent)
        await state.set_state(UserStates.get_agents)
    elif message.text == button_text_dialog_len:
        await message.answer(message.text)
        await message.answer(text_for_dialog_len)
        await state.set_state(UserStates.get_len)
    elif message.text == button_text_them:
        await message.answer(message.text)
        await message.answer(text_for_them)
        await state.set_state(UserStates.get_them)
    elif message.text == button_text_instrustion:
        await message.answer(message.text)
        await message.answer(text_for_instrustion)
        await state.set_state(UserStates.get_instrustion)


@dp.message(StateFilter(UserStates.get_agents), F.content_type == "text")
async def get_agent(message: Message, state: FSMContext):
    await state.update_data(agents=message.text)
    answer = api.parsing_agents(message.text)
    for name_agent in answer:
        text_messege = f"{name_agent}\n{answer[name_agent]}\n\n"
        print(text_messege)
        await message.answer("ответ получен ...")
        await message.answer(text_messege)


@dp.message(StateFilter(UserStates.get_len), F.content_type == "text")
async def get_len(message: Message, state: FSMContext):
    text_messege = message.text
    await state.update_data(dialog_len=int(text_messege))
    await message.answer("ответ получен ...")
    await message.answer(text_messege)


@dp.message(StateFilter(UserStates.get_them), F.content_type == "text")
async def get_them(message: Message, state: FSMContext):
    text_messege = message.text
    await state.update_data(them=text_messege)
    await message.answer("ответ получен ...")
    await message.answer(text_messege)


@dp.message(StateFilter(UserStates.get_instrustion), F.content_type == "text")
async def get_instrustion(message: Message, state: FSMContext):
    text_messege = message.text
    await state.update_data(instrustion=text_messege)
    await message.answer("ответ получен ...")
    await message.answer(text_messege)


if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))
