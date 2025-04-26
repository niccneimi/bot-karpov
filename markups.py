from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from config import *

def get_start_1_kb(language):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=language['but_connect']),
                KeyboardButton(text=language['but_my_keys']),
            ],
            [
                KeyboardButton(text=language['but_desription'].format(name_config=NAME_VPN_CONFIG))
            ],
            [
                KeyboardButton(text=language['but_change_language']),
                KeyboardButton(text=language['but_help'])
            ]
        ],
        resize_keyboard=True,
        selective=True
    )
    return kb

def get_start_2_kb(language):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=language['but_connect'], callback_data="vpn_connect")
            ],
            [
                InlineKeyboardButton(text=language['but_desription'].format(name_config=NAME_VPN_CONFIG), callback_data="bot_description")
            ]
        ]
    )
    return kb

def get_help_kb(language):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=language['but_how_podkl'])
            ],
            [
                KeyboardButton(text=language['but_no_work_vpn'])
            ],
            [
                KeyboardButton(text=language['but_manager'])
            ],
            [
                KeyboardButton(text=language['but_main'])
            ]
        ],
        resize_keyboard=True,
        selective=True
    )
    return kb

def get_contact_us_kb(language):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=language['but_support'], url='https://t.me/DexPN_Support_bot')
            ]
        ]
    )
    return kb

def get_devices_kb(language):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📎📱Android"),
                KeyboardButton(text="📎📱IOS"),
                KeyboardButton(text="📎💻Windows/MacOS"),
            ],
            [
                KeyboardButton(text=language['but_back_help']),
                KeyboardButton(text=language['but_main'])
            ]
        ],
        resize_keyboard=True,
        selective=True
    )
    return kb

def get_connect_kb(language):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=language['but_connect'], callback_data="vpn_connect")
            ]
        ]
    )
    return kb

def get_but_main_kb(language):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=language['but_main'])
            ]
        ],
        resize_keyboard=True,
        selective=True
    )
    return kb

def get_ios_connection_links_kb(language):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=language['instr_2_0_download'], url="https://apps.apple.com/ru/app/streisand/id6450534064")
            ],
            [
                InlineKeyboardButton(text=language['instr_2_0_install'], url="https://apps.apple.com/ru/app/streisand/id6450534064") #TODO разобраться с ссылкой для добавления ключа в приложение на ios
            ]
        ]
    )
    return kb
    
def get_languages_kb():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🔹{lang}", callback_data=f"language:{lang}")]
        for lang in LANG.keys()
    ])
    return kb

def get_about_connect_kb(language):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=language['but_connect'])
            ],
            [
                KeyboardButton(text=language['but_main'])
            ]
        ],
        resize_keyboard=True,
        selective=True
    )
    return kb

def get_buy_days_kb(language):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=f"{language['but_1_month']} - 5.0$"),
                KeyboardButton(text=f"{language['but_3_month']} - 12.0$"),
                KeyboardButton(text=f"{language['but_6_month']} - 22.0$")
            ],
            [
                KeyboardButton(text=f"{language['but_12_month']} - 40.0$")
            ],
            [
                KeyboardButton(text=language['but_main'])
            ]
        ],
        resize_keyboard=True,
        selective=True
    )
    return kb

def get_select_valute_kb():
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="USDT", callback_data="valute:USDT")
            ],
            [
                InlineKeyboardButton(text="DEXNET (-20%)", callback_data="valute:DEXNET")
            ]
        ]
    )
    return kb

def get_no_promo_kb(language):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=language['no_promocode_but'], callback_data='no_promocode')
            ]
        ]
    )
    return kb

def get_check_pay_kb(language, currency, price):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=language['but_check_pay'], callback_data=f"check_payment:{currency}:{price}")
            ]
        ]
    )
    return kb