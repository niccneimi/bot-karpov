##############################IMPORTS################################
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart,Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, BufferedInputFile
import asyncio, logging
from FSM import *
from config import *
from markups import *
from utils import *
from services.promocode import check_promocode
from cryptoapinet.services import get_qr_code_image
from cryptoapinet.check_transaction import request_transaction_info
from database import Database

bot = Bot(TOKEN)
dp = Dispatcher()
db = Database(f'postgresql://{DATABASE_USERNAME}:{DATABASE_PASSWORD}@{DATABASE_HOST}/{DATABASE_NAME}')

#####################################################################

@dp.message(buyConnection.checkPromo)
async def waiting_for_promocode(message: Message, state: FSMContext):
    check_result = check_promocode(message.text)
    language = LANG[await db.get_lang(message.from_user.id)]
    if check_result:
        pass
    else:
        data = state.get_data()
        await message.answer(language['promocode_does_not_exist'])
        qr_image = get_qr_code_image(WALLET_ADDRESS)
        await bot.send_photo(message.from_user.id, BufferedInputFile(qr_image.getvalue(), filename="qr.png"))
        await message.answer(f"<code>{WALLET_ADDRESS}</code>", parse_mode="HTML")
        await message.answer(language['total_amount_payment'].format(sum=data['price'],currency=data['valute']), reply_markup=get_check_pay_kb(language))
        await state.clear()

##############################COMANDS################################
@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    if not await db.user_exists(message.from_user.id):
        await db.add_user(message.from_user.id)
        language = LANG[await db.get_lang(message.from_user.id)]
        await message.answer(language['tx_change_language'], reply_markup=get_languages_kb())
    language = LANG[await db.get_lang(message.from_user.id)]
    await message.answer(language['tx_hello'].format(name=message.from_user.first_name), reply_markup=get_start_1_kb(language))
    await message.answer(language['tx_start'].format(name_config=NAME_VPN_CONFIG, 
                                                     but_1=language['but_connect'], 
                                                     but_2=language['but_desription'].format(name_config=NAME_VPN_CONFIG)), 
                                                     reply_markup=get_start_2_kb(language), 
                                                     parse_mode='HTML')
    await state.clear()

@dp.message(Command("help"))
async def help_command(message: Message):
    language = LANG[await db.get_lang(message.from_user.id)]
    await message.answer(language['tx_help'].format(name=message.from_user.first_name), reply_markup=get_help_kb(language))

@dp.message(Command("buy"))
async def buy_command(message: Message, state: FSMContext):
    language = LANG[await db.get_lang(message.from_user.id)]
    if not await db.is_free_trial_used(message.from_user.id):
        probniy = '\n\n' + language['tx_buy_probniy'].format(days_trial=COUNT_DAYS_TRIAL, dney_text=await dney(language, COUNT_DAYS_TRIAL))
    else:
        probniy = ''
    await message.answer(language['tx_buy_no_keys'].format(text_1=probniy, text_2=language['tx_prodlt_tarif']), reply_markup=get_buy_days_kb(language))

# #####################################################################


# ############################HANDLERS#################################
@dp.callback_query(lambda c: c.data == 'no_promocode', buyConnection.checkPromo)
async def no_promocode(callback_query: CallbackQuery, state: FSMContext):
    language = LANG[await db.get_lang(callback_query.from_user.id)]
    data = await state.get_data()
    qr_image = get_qr_code_image(WALLET_ADDRESS)
    await bot.send_photo(callback_query.from_user.id, BufferedInputFile(qr_image.getvalue(), filename="qr.png"))
    await callback_query.message.answer(f"<code>{WALLET_ADDRESS}</code>", parse_mode="HTML")
    await callback_query.message.answer(language['total_amount_payment'].format(summ=data['price'],currency=data['valute'].upper()), reply_markup=get_check_pay_kb(language), parse_mode="HTML")
    await state.clear()

@dp.callback_query(lambda c: c.data.startswith("valute:"),buyConnection.selectValute)
async def choose_value(callback_query: CallbackQuery, state: FSMContext):
    language = LANG[await db.get_lang(callback_query.from_user.id)]
    await state.update_data(valute=callback_query.data.split(":")[1])
    await callback_query.message.answer(language['promocode_question'], reply_markup=get_no_promo_kb(language))
    await state.set_state(buyConnection.checkPromo)


@dp.message()
async def message_handler(message: Message, state: FSMContext):
    await state.clear()
    text = message.text
    language = LANG[await db.get_lang(message.from_user.id)]

    if text == language['but_connect']:
        language = LANG[await db.get_lang(message.from_user.id)]
        if not await db.is_free_trial_used(message.from_user.id):
            probniy = '\n\n' + language['tx_buy_probniy'].format(days_trial=COUNT_DAYS_TRIAL, dney_text=await dney(language, COUNT_DAYS_TRIAL))
        else:
            probniy = ''
        await message.answer(language['tx_buy_no_keys'].format(text_1=probniy, text_2=language['tx_prodlt_tarif']), reply_markup=get_buy_days_kb(language))
    elif text in [f"{language['but_1_month']} - 5.0$", f"{language['but_3_month']} - 12.0$", f"{language['but_6_month']} - 22.0$", f"{language['but_12_month']} - 40.0$"]:
        tmp_msg = await message.answer(language['tx_wait'],reply_markup=get_but_main_kb(language))
        await bot.delete_message(message.from_user.id, tmp_msg.message_id)
        await message.answer(language['tx_select_currency'], reply_markup=get_select_valute_kb())
        await state.set_state(buyConnection.selectValute)
        await state.update_data(price=get_price_dict(language, text))

    
    elif text == language['but_my_keys']:
        #TODO Добавить получение активных ключей
        await message.answer(language['tx_no_activ_keys'])
    elif text == language['but_change_language']: 
        await message.answer(language['tx_change_language'], reply_markup=get_languages_kb())
    elif text == language['but_desription'].format(name_config=NAME_VPN_CONFIG):
        await message.answer(language['tx_description'])
        await message.answer(language['tx_description_connect'].format(days=COUNT_DAYS_TRIAL,dney_text=await dney(language, COUNT_DAYS_TRIAL), nick_help=NICK_HELP),reply_markup=get_about_connect_kb(language))
    elif text == language['but_help']:
        await message.answer(language['tx_help'].format(name=message.from_user.first_name), reply_markup=get_help_kb(language))
    elif text == language['but_main']:
        await state.clear()
        await message.answer(language['tx_hello'].format(name=message.from_user.first_name), reply_markup=get_start_1_kb(language))
        await message.answer(language['tx_start'].format(name_config=NAME_VPN_CONFIG, 
                                                        but_1=language['but_connect'], 
                                                        but_2=language['but_desription'].format(name_config=NAME_VPN_CONFIG)), 
                                                        reply_markup=get_start_2_kb(language), 
                                                        parse_mode='HTML')
        
    # Обработка команд после нажатия "🛟Помощь"
    elif text == language['but_how_podkl']:
        await message.answer(language['tx_how_install'].format(name=message.from_user.first_name), reply_markup=get_devices_kb(language))
        await message.answer(language['tx_how_install_info'].format(but=language['but_connect']), reply_markup=get_connect_kb(language), parse_mode='HTML')
    elif text == language['but_back_help']:
        await message.answer(language['tx_help'].format(name=message.from_user.first_name), reply_markup=get_help_kb(language))
    elif text == language['but_no_work_vpn']:
        await message.answer(language['tx_not_work_vpn'].format(name=message.from_user.first_name))
    elif text == language['but_manager']:
        await message.answer(language['tx_support_button'], reply_markup=get_contact_us_kb(language))
    
    # Инструкции для подключения после нажатия "Как подключиться❔"
    elif text == "📎📱Android":
        await message.answer(language['instr_vless_android'], disable_web_page_preview=True, parse_mode="HTML")
        await message.answer(language['instr_wireguard_rule'])
    elif text == "📎📱IOS":
        await message.answer(language['instr_vless_ios'], disable_web_page_preview=True, reply_markup=get_ios_connection_links_kb(language), parse_mode="HTML")
    elif text == "📎💻Windows/MacOS":
        await message.answer(language['instr_vless_mac_windows'], disable_web_page_preview=True, parse_mode="HTML")
        await message.answer(language['instr_wireguard_rule'])

@dp.callback_query(lambda c: c.data.startswith('language:'))
async def change_language(callback_query: CallbackQuery, state: FSMContext):
    language_to_change = callback_query.data.split(":")[1]
    await db.change_lang(callback_query.from_user.id, language_to_change)
    language = LANG[await db.get_lang(callback_query.from_user.id)]
    await callback_query.message.delete()
    await callback_query.message.answer(language['tx_yes_language'], reply_markup=get_start_1_kb(language))
    await state.clear()

@dp.callback_query(lambda c: c.data == "vpn_connect")
async def connect_by_inline_button(callback_query: CallbackQuery, state: FSMContext):
    language = LANG[await db.get_lang(callback_query.from_user.id)]
    if not await db.is_free_trial_used(callback_query.from_user.id):
        probniy = '\n\n' + language['tx_buy_probniy'].format(days_trial=COUNT_DAYS_TRIAL, dney_text=await dney(language, COUNT_DAYS_TRIAL))
    else:
        probniy = ''
    await callback_query.message.answer(language['tx_buy_no_keys'].format(text_1=probniy, text_2=language['tx_prodlt_tarif']), reply_markup=get_buy_days_kb(language))

@dp.callback_query(lambda c: c.data == "check_payment")
async def check_payment_manual(callback_query: CallbackQuery, state: FSMContext):
    #TODO Проверка платежа после нажатия проверить оплату
    pass
#####################################################################


##############################START##################################
async def main():
    # await bot.delete_webhook(True)
    await db.create_pool()
    try:
        await dp.start_polling(bot,allowed_updates=["message", "inline_query", "callback_query"])
    finally:
        await db.close_pool()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())