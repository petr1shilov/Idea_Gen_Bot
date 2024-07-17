from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from bot.texts import *

button_1 = KeyboardButton(text=button_text_gen)
button_2 = KeyboardButton(text=button_text_agents)
button_3 = KeyboardButton(text=button_text_dialog_len)
button_4 = KeyboardButton(text=button_text_them)
button_5 = KeyboardButton(text=button_text_model)

model_button_1 = KeyboardButton(text=button_text_model_1)
model_button_2 = KeyboardButton(text=button_text_model_2)

kb = ReplyKeyboardMarkup(
    keyboard=[[button_1],
              [button_2],
              [button_3],
              [button_4],
              [button_5]],
    resize_keyboard=True
)

model_kb = ReplyKeyboardMarkup(
    keyboard=[[model_button_1],
              [model_button_2]],
    resize_keyboard=True
)