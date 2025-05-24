import random
import string

async def dney(language, day=0):
    if day % 10 == 1 and day != 11:
            return language['days_text_1']
    elif 2 <= day % 10 <= 4 and (day < 10 or day > 20):
            return language['days_text_2_4']
    else:
            return language['days_text_0_5_9']

def get_price_from_text(button_text):
        text = button_text.split('-')[1]
        number_str = ''.join(filter(str.isdigit, text))
        return int(number_str)

def generate_promo_code(length=8):
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))