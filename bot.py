##############################IMPORTS################################
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart,Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from decimal import Decimal
import asyncio, logging, json, re
from FSM import *
from config import *
from markups import *
from utils import *
from services.promocode import check_promocode
from services.dexstore_code import AdminDPNClient
from cryptoapinet.services import get_qr_code_image, get_payment_address
from cryptoapinet.check_transaction import request_transaction_info
from cryptoapinet.utils import get_currency_cryptoapinet_by_token
from database import Database
import requests, datetime

bot = Bot(TOKEN)
dp = Dispatcher()
db = Database(f'postgresql://{DATABASE_USERNAME}:{DATABASE_PASSWORD}@{DATABASE_HOST}/{DATABASE_NAME}')

# Состояния для работы с промокодами
class PromoCodeStates:
    ENTER_PROMOCODE = 'enter_promocode'

#####################################################################

@dp.message(buyConnection.checkPromo)
async def waiting_for_promocode(message: Message, state: FSMContext):
    check_result = check_promocode(message.text)
    language = LANG[await db.get_lang(message.from_user.id)]
    data = await state.get_data()
    address = data.get('payment_address')
    currency = data.get('valute')
    dexnet_discount=0
    if currency == "DEXNET":
        dexnet_discount = 20
    if check_result:
        if not await db.is_used_promocode_by_telegram_id(str(message.from_user.id), message.text):
            await message.answer(language['tx_spec_url_yes'].format(discount=check_result['discount_percent']))
            await db.add_promocode_used_by_telegram_id(str(message.from_user.id), message.text)
            qr_image = get_qr_code_image(address=address)
            await bot.send_photo(message.from_user.id, BufferedInputFile(qr_image.getvalue(), filename="qr.png"))
            await message.answer(f"<code>{address}</code>", parse_mode="HTML")
            await message.answer(
                language['total_amount_payment'].format(
                    summ=data['price']-data['price']*((check_result['discount_percent']+dexnet_discount)/100),
                    currency=currency.upper()
                ), 
                reply_markup=get_check_pay_kb(language, currency, data['price'], 0 if not data.get('key_uuid') else data.get('key_uuid'), check_result['discount_percent']+dexnet_discount), 
                parse_mode="HTML"
            )
        else:
            await message.answer(language['tx_promo_is_activate'])
            qr_image = get_qr_code_image(address=address)
            await bot.send_photo(message.from_user.id, BufferedInputFile(qr_image.getvalue(), filename="qr.png"))
            await message.answer(f"<code>{address}</code>", parse_mode="HTML")
            await message.answer(
                language['total_amount_payment'].format(
                    summ=data['price']-data['price']*(dexnet_discount/100),
                    currency=currency.upper()
                ), 
                reply_markup=get_check_pay_kb(language, currency, data['price'], 0 if not data.get('key_uuid') else data.get('key_uuid'), dexnet_discount), 
                parse_mode="HTML"
            )
    else:
        await message.answer(language['promocode_does_not_exist'])
        qr_image = get_qr_code_image(address=address)
        await bot.send_photo(message.from_user.id, BufferedInputFile(qr_image.getvalue(), filename="qr.png"))
        await message.answer(f"<code>{address}</code>", parse_mode="HTML")
        await message.answer(
            language['total_amount_payment'].format(
                summ=data['price']-data['price']*(dexnet_discount/100),
                currency=currency.upper()
            ), 
            reply_markup=get_check_pay_kb(language, currency, data['price'], 0 if not data.get('key_uuid') else data.get('key_uuid'), dexnet_discount), 
            parse_mode="HTML"
        )
    await state.clear()

##############################COMANDS################################
@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    if not await db.user_exists(message.from_user.id):
        await db.add_user(message.from_user.id, message.from_user.username)
        language = LANG[await db.get_lang(message.from_user.id)]
        await message.answer(language['tx_change_language'], reply_markup=get_languages_kb())
    
    language = LANG[await db.get_lang(message.from_user.id)]
    
    start_params = message.text.split()
    if len(start_params) > 1:
        token = start_params[1]
        request_data = {
            "code": token
        }
        code_data, status_code = AdminDPNClient.check_code(request_data=request_data)
        
        if code_data.get("valid"):
            days_to_add = 365
            data = {
                "telegram_id": str(message.from_user.id),
                "expiration_date": int((datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=days_to_add)).timestamp())
            }
            
            create_user = requests.post(f"http://{MANAGER_SERVER_HOST}:{MANAGER_SERVER_PORT}/create_config", json=data)
            
            if create_user.status_code == 200:
                activate_data = {
                    "code": token,
                    "telegram_id": message.from_user.id
                }
                AdminDPNClient.activate_code(request_data=activate_data)
                
                await message.answer('Промокод успешно применён ✅')
                await message.answer(language['tx_how_install_after_pay'])
                await message.answer(
                    f"http://{MANAGER_SERVER_HOST}:8000/sub/{create_user.json()['result'][0]['telegram_id']}--{create_user.json()['result'][0]['uuid']}", 
                    reply_markup=get_devices_kb_after_pay(language)
                )
            else:
                await message.answer(language['tx_no_create_key'])
    
    await message.answer(language['tx_hello'].format(name=message.from_user.first_name), reply_markup=get_start_1_kb(language, await db.is_free_trial_used(message.from_user.id)))
    await message.answer(language['tx_start'].format(name_config=NAME_VPN_CONFIG, 
                                                     but_1=language['but_connect'], 
                                                     but_2=language['but_desription'].format(name_config=NAME_VPN_CONFIG)), 
                                                     reply_markup=get_start_2_kb(language, await db.is_free_trial_used(message.from_user.id)), 
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
    await message.answer(language['tx_buy_no_keys'].format(text_1=probniy, text_2=language['tx_prodlt_tarif']), reply_markup= await get_buy_days_kb(language, await db.get_tarifs()))

@dp.message(Command("promo"))
async def create_promocode_with_days(message: Message):
    user_id = message.from_user.id
    is_admin = user_id in ADMIN_IDS or await db.is_admin(user_id)
    
    if not is_admin:
        await message.answer("У вас нет прав для использования этой команды.")
        return
    
    command_parts = message.text.split()
    if len(command_parts) != 2:
        await message.answer("Неверный формат команды. Используйте: /promo X, где X - количество дней.")
        return
    
    try:
        days = int(command_parts[1])
        if days <= 0:
            await message.answer("Количество дней должно быть положительным числом.")
            return
    except ValueError:
        await message.answer("Неверный формат количества дней. Укажите число.")
        return
    promo_code = generate_promo_code()
    
    success = await db.create_admin_promocode(promo_code, days, user_id)
    
    if success:
        await message.answer(f"Промокод создан успешно!\n\nКод: <code>{promo_code}</code>\nДней: {days}\n\nЭтот промокод можно использовать один раз.", parse_mode="HTML")
    else:
        await message.answer("Ошибка при создании промокода. Попробуйте еще раз.")

@dp.message(Command("promo_30"))
async def create_promo_30_days(message: Message):
    user_id = message.from_user.id
    is_admin = user_id in ADMIN_IDS or await db.is_admin(user_id)
    
    if not is_admin:
        await message.answer("У вас нет прав для использования этой команды.")
        return
    
    promo_code = generate_promo_code()
    success = await db.create_admin_promocode(promo_code, 30, user_id)
    
    if success:
        await message.answer(f"Промокод создан успешно!\n\nКод: <code>{promo_code}</code>\nДней: 30\n\nЭтот промокод можно использовать один раз.", parse_mode="HTML")
    else:
        await message.answer("Ошибка при создании промокода. Попробуйте еще раз.")

@dp.message(Command("promo_90"))
async def create_promo_90_days(message: Message):
    user_id = message.from_user.id
    is_admin = user_id in ADMIN_IDS or await db.is_admin(user_id)
    
    if not is_admin:
        await message.answer("У вас нет прав для использования этой команды.")
        return
    
    promo_code = generate_promo_code()
    success = await db.create_admin_promocode(promo_code, 90, user_id)
    
    if success:
        await message.answer(f"Промокод создан успешно!\n\nКод: <code>{promo_code}</code>\nДней: 90\n\nЭтот промокод можно использовать один раз.", parse_mode="HTML")
    else:
        await message.answer("Ошибка при создании промокода. Попробуйте еще раз.")

@dp.message(Command("promo_180"))
async def create_promo_180_days(message: Message):
    user_id = message.from_user.id
    is_admin = user_id in ADMIN_IDS or await db.is_admin(user_id)
    
    if not is_admin:
        await message.answer("У вас нет прав для использования этой команды.")
        return
    promo_code = generate_promo_code()
    success = await db.create_admin_promocode(promo_code, 180, user_id)
    
    if success:
        await message.answer(f"Промокод создан успешно!\n\nКод: <code>{promo_code}</code>\nДней: 180\n\nЭтот промокод можно использовать один раз.", parse_mode="HTML")
    else:
        await message.answer("Ошибка при создании промокода. Попробуйте еще раз.")

@dp.message(Command("promo_365"))
async def create_promo_365_days(message: Message):
    user_id = message.from_user.id
    is_admin = user_id in ADMIN_IDS or await db.is_admin(user_id)
    
    if not is_admin:
        await message.answer("У вас нет прав для использования этой команды.")
        return
    promo_code = generate_promo_code()
    success = await db.create_admin_promocode(promo_code, 365, user_id)
    
    if success:
        await message.answer(f"Промокод создан успешно!\n\nКод: <code>{promo_code}</code>\nДней: 365\n\nЭтот промокод можно использовать один раз.", parse_mode="HTML")
    else:
        await message.answer("Ошибка при создании промокода. Попробуйте еще раз.")

@dp.message(Command("promocode"))
async def activate_promocode(message: Message):
    command_parts = message.text.split()
    if len(command_parts) != 2:
        await message.answer("Неверный формат команды. Используйте: /promocode КОД")
        return
    
    promo_code = command_parts[1].strip().upper()
    user_id = message.from_user.id
    language = LANG[await db.get_lang(user_id)]
    promocode_data = await db.get_admin_promocode(promo_code)
    
    if not promocode_data:
        await message.answer("Промокод не найден или уже был использован.")
        return
    
    if await db.is_used_promocode_by_telegram_id(str(user_id), promo_code):
        await message.answer("Вы уже использовали этот промокод.")
        return
    days = promocode_data['days']
    
    try:
        data = {
            "telegram_id": str(user_id),
            "expiration_date": int((datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=days)).timestamp())
        }
        
        create_user = requests.post(f"http://{MANAGER_SERVER_HOST}:{MANAGER_SERVER_PORT}/create_config", json=data)
        
        if create_user.status_code == 200:
            await db.mark_admin_promocode_used(promo_code)
            await db.add_promocode_used_by_telegram_id(str(user_id), promo_code)
            await message.answer(f"Промокод успешно активирован! ✅\nВаша подписка на {days} дней активирована.")
            
            await message.answer(language['tx_how_install_after_pay'])
            await message.answer(
                f"http://{MANAGER_SERVER_HOST}:8000/sub/{create_user.json()['result'][0]['telegram_id']}--{create_user.json()['result'][0]['uuid']}",
                reply_markup=get_devices_kb_after_pay(language)
            )
        else:
            await message.answer("Произошла ошибка при создании ключа. Пожалуйста, обратитесь к администратору.")
    
    except Exception as e:
        logging.error(f"Error creating key with promocode: {str(e)}")
        await message.answer("Произошла ошибка при активации промокода. Пожалуйста, попробуйте позже или обратитесь к администратору.")

##############################HANDLERS#################################
@dp.callback_query(lambda c: c.data == 'no_promocode', buyConnection.checkPromo)
async def no_promocode(callback_query: CallbackQuery, state: FSMContext):
    language = LANG[await db.get_lang(callback_query.from_user.id)]
    data = await state.get_data()
    address = data.get('payment_address')
    currency = data.get('valute')
    dexnet_discount=0
    if currency == "DEXNET":
        dexnet_discount = 20
    
    qr_image = get_qr_code_image(address=address)
    await bot.send_photo(callback_query.from_user.id, BufferedInputFile(qr_image.getvalue(), filename="qr.png"))
    await callback_query.message.answer(f"<code>{address}</code>", parse_mode="HTML")
    await callback_query.message.answer(
        language['total_amount_payment'].format(
            summ=data['price']-data['price']*(dexnet_discount/100),
            currency=currency.upper()
        ), 
        reply_markup=get_check_pay_kb(language, currency, data['price'], 0 if not data.get('key_uuid') else data.get('key_uuid'), dexnet_discount), 
        parse_mode="HTML"
    )
    await state.clear()

@dp.callback_query(lambda c: c.data.startswith("valute:"), buyConnection.selectValute)
async def choose_valute(callback_query: CallbackQuery, state: FSMContext):
    language = LANG[await db.get_lang(callback_query.from_user.id)]
    currency = callback_query.data.split(":")[1].upper()
    user_id = callback_query.from_user.id
    data = await state.get_data()
    await state.update_data(valute=currency)
    
    address_data = await db.get_address_by_user_and_token(user_id, currency)
    if not address_data:
        await db.add_crypto_address(
            user_id=user_id,
            token=currency,
            standart='BEP20',
            result='pending',
            address_type='default'
        )
        address_data = await db.get_address_by_user_and_token(user_id, currency)

    if not address_data.get('address'):
        address = get_payment_address(address_data['id'], currency)
        await db.update_crypto_address(user_id, address, currency)
    else:
        address = address_data['address']    
    await callback_query.message.answer(language['promocode_question'], reply_markup=get_no_promo_kb(language))
    await state.update_data(payment_address=address)
    await state.set_state(buyConnection.checkPromo)


@dp.message()
async def message_handler(message: Message, state: FSMContext):
    text = message.text
    language = LANG[await db.get_lang(message.from_user.id)]

    if text == language['but_new_key']:
        language = LANG[await db.get_lang(message.from_user.id)]
        if not await db.is_free_trial_used(message.from_user.id):
            probniy = '\n\n' + language['tx_buy_probniy'].format(days_trial=COUNT_DAYS_TRIAL, dney_text=await dney(language, COUNT_DAYS_TRIAL))
        else:
            probniy = ''
        await message.answer(language['tx_buy_no_keys'].format(text_1=probniy, text_2=language['tx_prodlt_tarif']), reply_markup= await get_buy_days_kb(language, await db.get_tarifs()))

    elif text == language['but_connect']:
        keys_from_db = await db.get_all_client_keys(str(message.from_user.id))
        keys = []
        if len(keys_from_db) != 0:
            for key, value in keys_from_db.items():
                keys.append((key, await db.get_key_days_left(key)))
            await message.answer(language['tx_buy'].format(name=message.from_user.first_name), reply_markup=await get_prodl_new_kb(language, keys))
        else:
            if not await db.is_free_trial_used(message.from_user.id):
                probniy = '\n\n' + language['tx_buy_probniy'].format(days_trial=COUNT_DAYS_TRIAL, dney_text=await dney(language, COUNT_DAYS_TRIAL))
            else:
                probniy = ''
            await message.answer(language['tx_buy_no_keys'].format(text_1=probniy, text_2=language['tx_prodlt_tarif']), reply_markup= await get_buy_days_kb(language, await db.get_tarifs()))


    elif "🟣 " in text or "🟢 " in text or  "🟡 " in text:
        await message.answer(language['tx_wait'],reply_markup=get_but_main_kb(language))
        await message.answer(language['tx_select_currency'], reply_markup=get_select_valute_kb())
        await state.set_state(buyConnection.selectValute)
        await state.update_data(price=get_price_from_text(text))

    elif text == language['but_test_key']:
        if not await db.is_free_trial_used(message.from_user.id):
            days_to_add = 7
            data = {
                "telegram_id": str(message.from_user.id),
                "expiration_date": int((datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=days_to_add)).timestamp())
            }
            create_user = requests.post(f"http://{MANAGER_SERVER_HOST}:{MANAGER_SERVER_PORT}/create_config", json=data)
            if create_user.status_code == 200:
                await db.change_free_trial(message.from_user.id)
                await message.answer(language['tx_how_install_after_pay'])
                await message.answer(f"http://91.84.111.102:8000/sub/{create_user.json()['result'][0]['telegram_id']}--{create_user.json()['result'][0]['uuid']}", reply_markup=get_devices_kb_after_pay(language))
            else:
                await message.answer(language['tx_no_create_key'])
        else:
            return
        
    elif text == language['but_my_keys']:
        keys = await db.get_all_client_keys(str(message.from_user.id))
        if len(keys) != 0:
            for key, value in keys.items():
                await message.answer(f"http://91.84.111.102:8000/sub/{message.from_user.id}--{key}", reply_markup=await get_but_prodlit_key_kb(language, await db.get_key_days_left(key), key))
            await message.answer(language['tx_key_select_for_help'], reply_markup=get_devices_kb_after_pay(language))
        else:
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
        await message.answer(language['tx_hello'].format(name=message.from_user.first_name), reply_markup=get_start_1_kb(language, await db.is_free_trial_used(message.from_user.id)))
        await message.answer(language['tx_start'].format(name_config=NAME_VPN_CONFIG, 
                                                        but_1=language['but_connect'], 
                                                        but_2=language['but_desription'].format(name_config=NAME_VPN_CONFIG)), 
                                                        reply_markup=get_start_2_kb(language, await db.is_free_trial_used(message.from_user.id)), 
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

    # Политика конфиденциальности и пользовательское солгашение
    elif text == language['but_user_agreement']:
        klava = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=language['but_user_agreement'], url="https://admin.dpntg.online/configs/document/?slug=user_agreement")]])
        await message.answer(language['but_pointer'], reply_markup=klava)

    elif text == language['but_privacy_policy']:
        klava = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=language['but_privacy_policy'], url="https://admin.dpntg.online/configs/document/?slug=privacy_policy")]])
        await message.answer(language['but_pointer'], reply_markup=klava)

@dp.callback_query(lambda c: c.data == "give_test_key")
async def give_test_key(callback_query: CallbackQuery, state: FSMContext):
    if not await db.is_free_trial_used(callback_query.from_user.id):
        language = LANG[await db.get_lang(callback_query.from_user.id)]
        days_to_add = 7
        data = {
            "telegram_id": str(callback_query.from_user.id),
            "expiration_date": int((datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=days_to_add)).timestamp())
        }
        create_user = requests.post(f"http://{MANAGER_SERVER_HOST}:{MANAGER_SERVER_PORT}/create_config", json=data)
        if create_user.status_code == 200:
            await db.change_free_trial(callback_query.from_user.id)
            await callback_query.message.answer(language['tx_how_install_after_pay'])
            await callback_query.message.answer(f"http://{MANAGER_SERVER_HOST}:8000/sub/{create_user.json()['result'][0]['telegram_id']}--{create_user.json()['result'][0]['uuid']}", reply_markup=get_devices_kb_after_pay(language))
        else:
            await callback_query.message.answer(language['tx_no_create_key'])
    else:
        return

@dp.callback_query(lambda c: c.data.startswith('language:'))
async def change_language(callback_query: CallbackQuery, state: FSMContext):
    language_to_change = callback_query.data.split(":")[1]
    await db.change_lang(callback_query.from_user.id, language_to_change)
    language = LANG[await db.get_lang(callback_query.from_user.id)]
    await callback_query.message.delete()
    await callback_query.message.answer(language['tx_yes_language'], reply_markup=get_start_1_kb(language, await db.is_free_trial_used(callback_query.from_user.id)))
    await state.clear()

@dp.callback_query(lambda c: c.data == "but_connect")
async def but_connect_handler(callback_query: CallbackQuery, state: FSMContext):
    language = LANG[await db.get_lang(callback_query.from_user.id)]
    keys_from_db = await db.get_all_client_keys(str(callback_query.from_user.id))
    keys = []
    if len(keys_from_db) != 0:
        for key, value in keys_from_db.items():
            keys.append((key, await db.get_key_days_left(key)))
        await callback_query.message.answer(language['tx_buy'].format(name=callback_query.from_user.first_name), reply_markup=await get_prodl_new_kb(language, keys))
    else:
        if not await db.is_free_trial_used(callback_query.from_user.id):
            probniy = '\n\n' + language['tx_buy_probniy'].format(days_trial=COUNT_DAYS_TRIAL, dney_text=await dney(language, COUNT_DAYS_TRIAL))
        else:
            probniy = ''
        await callback_query.message.answer(language['tx_buy_no_keys'].format(text_1=probniy, text_2=language['tx_prodlt_tarif']), reply_markup= await get_buy_days_kb(language, await db.get_tarifs()))


@dp.callback_query(lambda c: c.data == "vpn_connect")
async def connect_by_inline_button(callback_query: CallbackQuery, state: FSMContext):
    language = LANG[await db.get_lang(callback_query.from_user.id)]
    if not await db.is_free_trial_used(callback_query.from_user.id):
        probniy = '\n\n' + language['tx_buy_probniy'].format(days_trial=COUNT_DAYS_TRIAL, dney_text=await dney(language, COUNT_DAYS_TRIAL))
    else:
        probniy = ''
    await callback_query.message.answer(language['tx_buy_no_keys'].format(text_1=probniy, text_2=language['tx_prodlt_tarif']), reply_markup= await get_buy_days_kb(language, await db.get_tarifs()))

@dp.callback_query(lambda c: c.data.startswith("check_payment"))
async def check_payment_manual(callback_query: CallbackQuery, state: FSMContext):
    currency = callback_query.data.split(":")[1]
    price = Decimal(callback_query.data.split(":")[2])
    prodlit_key = callback_query.data.split(":")[3]
    discount = int(callback_query.data.split(":")[4])
    price_with_discount = price-price*(discount)
    user_id = callback_query.from_user.id
    language = LANG[await db.get_lang(user_id)]
    
    address_data = await db.get_address_by_user_and_token(user_id, currency)

    address = address_data['address']
    confirmations, tx_data = request_transaction_info(address)

    
    if tx_data is not None:
        existing_tx = await db.get_transaction_by_txid_and_address(tx_data['hash'], address)
        token = get_currency_cryptoapinet_by_token(tx_data['tokenSymbol'])
        
        if confirmations >= 3 and not existing_tx and currency == token:
            tx_amount = Decimal(tx_data['value']) / Decimal((10 ** int(tx_data['tokenDecimal'])))
            tx_amount = round(Decimal(tx_amount), 8)

            try:
                if Decimal(price_with_discount) <= Decimal(tx_amount):
                    await db.add_transaction(
                        txid=tx_data['hash'],
                        transaction_type="in" if prodlit_key == "0" else "prodlit",
                        confirmations=confirmations,
                        token=token,
                        amount=str(tx_amount),
                        from_address=tx_data['from'],
                        standart="BEP20",
                        user_crypto_address_id=address_data['id'],
                        address=tx_data['to'],
                        paid=True,
                        status="Paid"
                    )
                    
                    await callback_query.message.answer(language['tx_how_install_after_pay'], reply_markup=get_devices_kb_after_pay(language))
                    if prodlit_key == "0":
                        days_to_add = get_price_to_days(await db.get_tarifs(), str(price))
                        data = {
                            "telegram_id": str(callback_query.from_user.id),
                            "expiration_date": int((datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=days_to_add)).timestamp())
                        }
                        create_user = requests.post(f"http://{MANAGER_SERVER_HOST}:{MANAGER_SERVER_PORT}/create_config", json=data)
                        if create_user.status_code == 200:
                            await callback_query.message.answer(f"http://{MANAGER_SERVER_HOST}:8000/sub/{create_user.json()['result'][0]['telegram_id']}--{create_user.json()['result'][0]['uuid']}")
                            expiration_date = create_user.json()['result'][0]['expiration_date']
                        else:
                            await callback_query.message.answer(language['tx_no_create_key'])
                            return
                    else:
                        days_to_add = get_price_to_days(await db.get_tarifs(), str(price))
                        r = await db.prodlit_expiration_date(prodlit_key, int(days_to_add)*86400)
                        expiration_date = r[0]['expiration_date']
                        await db.unmark_key_notified(prodlit_key)
                        keys = await db.get_all_client_keys(str(callback_query.from_user.id))
                        if len(keys) != 0:
                            for key, value in keys.items():
                                await callback_query.message.answer(f"http://{MANAGER_SERVER_HOST}:8000/sub/{callback_query.from_user.id}--{key}", reply_markup=await get_but_prodlit_key_kb(language, await db.get_key_days_left(key), key))
                    await db.create_order(
                        user_id=user_id,
                        paid=True,
                        extra={
                            "hash_tx": tx_data['hash']
                        },
                        currency=currency,
                        amount = price_with_discount,
                        package_size = int(get_price_to_days(await db.get_tarifs(), str(price))),
                        promocode_used = False if (discount == "0" or (discount == '20' and currency == "DEXNET")) else True,
                        expiration_date = expiration_date
                    )
                    await state.clear()
                    return
                    
            except Exception as ex:
                logging.error(f"Error processing payment for user {user_id}: {ex}")
                
    await callback_query.message.answer(
        language['transaction_not_found'],
        reply_markup=get_check_pay_kb(language, currency, price, prodlit_key, discount)
    )

# Продление ключей
@dp.callback_query(lambda c: c.data.startswith("prodlit_key_button"))
async def prodlit_client_key(callback_query: CallbackQuery, state: FSMContext):
    language = LANG[await db.get_lang(callback_query.from_user.id)]
    key_uuid = callback_query.data.split('--')[1]
    await state.update_data(key_uuid=key_uuid)
    await state.set_state(buyConnection.selectValute)
    await callback_query.message.answer(language['tx_prodlt_tarif'], reply_markup= await get_buy_days_kb(language, await db.get_tarifs()))

# Уведомления об истечении ключей
async def notify_expiring_keys():
    while True:
        try:
            now = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
            all_keys = await db.get_all_keys_with_expiration()
            for key in all_keys:
                user_id = key['telegram_id']
                expiration = key['expiration_date']
                days_left = (expiration - now) // 86400
                language = LANG[await db.get_lang(int(user_id))]

                if days_left == 2 and not key.get('notified_2_days'):
                    try:
                        await bot.send_message(
                            user_id,
                            f"{language['tx_after_2_days']}\nhttp://{MANAGER_SERVER_HOST}:8000/sub/{user_id}--{key['uuid']}",
                            reply_markup=await get_but_prodlit_key_kb(language, await db.get_key_days_left(key['uuid']), key['uuid'])
                        )
                    except:
                        pass
                    await db.mark_key_notified(key['uuid'], 'notified_2_days')

                if days_left == 1 and not key.get('notified_1_day'):
                    try:
                        await bot.send_message(
                            user_id,
                            f"{language['tx_tommorow']}\nhttp://{MANAGER_SERVER_HOST}:8000/sub/{user_id}--{key['uuid']}",
                            reply_markup=await get_but_prodlit_key_kb(language, await db.get_key_days_left(key['uuid']), key['uuid'])
                        )
                    except:
                        pass
                    await db.mark_key_notified(key['uuid'], 'notified_1_day')
        except Exception as e:
            logging.error(f"Error in notify_expiring_keys: {e}")
        await asyncio.sleep(3600)

#####################################################################


##############################START##################################
async def main():
    await bot.delete_webhook(True)
    await db.create_pool()
    asyncio.create_task(notify_expiring_keys()) 
    try:
        await dp.start_polling(bot,allowed_updates=["message", "inline_query", "callback_query"])
    finally:
        await db.close_pool()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())