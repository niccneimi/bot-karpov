async def dney(language, day=0):
    if day % 10 == 1 and day != 11:
            return language['days_text_1']
    elif 2 <= day % 10 <= 4 and (day < 10 or day > 20):
            return language['days_text_2_4']
    else:
            return language['days_text_0_5_9']

def get_price_dict(language, button_text):
    PRICE_DICT = {
        f"{language['but_1_month']} - 5.0$":5,
        f"{language['but_3_month']} - 12.0$":12,
        f"{language['but_6_month']} - 22.0$":22,
        f"{language['but_12_month']} - 40.0$":40
    }
    return PRICE_DICT[button_text]