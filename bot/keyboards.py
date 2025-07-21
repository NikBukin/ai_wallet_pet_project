from telebot import types


def main_menu_markup() -> types.ReplyKeyboardMarkup:
    """
    📑 Получить отчет
    💭 Рекомендации из новостей
    🔃 Изменить активы
    📨 Настроить рассылку
    """
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("📑 Получить отчет"))
    markup.add(types.KeyboardButton("💭 Рекомендации из новостей"))
    markup.add(types.KeyboardButton("🔃 Изменить активы"))
    markup.add(types.KeyboardButton("📨 Настроить рассылку"))
    return markup


def asset_type_menu_markup() -> types.ReplyKeyboardMarkup:
    """
    Меню выбора типа актива:
    🪙 Криптовалюта
    📑 Российские акции
    📄 Иностранные акции
    💵 Валюта
    🥇 Металл
    + кнопка «Вернуться в начало»
    """
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("🪙 Криптовалюта"))
    markup.add(types.KeyboardButton("📑 Российские акции"))
    markup.add(types.KeyboardButton("📄 Иностранные акции"))
    markup.add(types.KeyboardButton("💵 Валюта"))
    markup.add(types.KeyboardButton("🥇 Металл"))
    markup.add(types.KeyboardButton("↩️Вернуться в начало"))
    return markup


def back_to_start_markup() -> types.ReplyKeyboardMarkup:
    """
    Клавиатура из одной кнопки: «↩️Вернуться в начало»
    """
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("↩️Вернуться в начало"))
    return markup


def back_to_start_or_retry_markup() -> types.ReplyKeyboardMarkup:
    """
    Клавиатура из кнопок: «↩️Вернуться в начало»
    Клавиатура из кнопок: «📝 Ввести снова»
    """
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("↩️Вернуться в начало"))
    markup.add(types.KeyboardButton("📝 Ввести снова"))
    return markup


def delete_options_markup() -> types.ReplyKeyboardMarkup:
    """
    Меню, предлагающее удаление или изменение количества:
    ❌️Полностью удалить
    ↩️Изменить количество
    ↩️Вернуться в начало
    """
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("❌️Полностью удалить"))
    markup.add(types.KeyboardButton("↩️Изменить количество"))
    markup.add(types.KeyboardButton("↩️Вернуться в начало"))
    return markup


def yes_or_no() -> types.ReplyKeyboardMarkup:
    """
    Меню, предлагающее согласие или отказ:
    ✅ Да
    ❌ Нет
    """
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("✅ Да"))
    markup.add(types.KeyboardButton("❌ Нет"))
    return markup


def add_new_or_delete() -> types.ReplyKeyboardMarkup:
    """
    Меню, добавление нового актива или удаление существующего:
    🆕 Добавить новый актив
    ❌ Удалить из портфеля
    """
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("🆕 Добавить новый актив"))
    markup.add(types.KeyboardButton("❌ Удалить из портфеля"))
    return markup


def add_new_or_to_start() -> types.ReplyKeyboardMarkup:
    """
    Меню, добавление нового актива или возврат в начало:
    🆕 Добавить новый актив
    ↩️Вернуться в начало
    """
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("🆕 Добавить новый актив"))
    markup.add(types.KeyboardButton("↩️Вернуться в начало"))
    return markup


def rub_price_or_to_start() -> types.ReplyKeyboardMarkup:
    """
    Меню, определение стоимости в рублях или возврат в начало:
    ₽️Я знаю сколько в рублях
    🆕 Добавить новый актив
    """
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("₽️Я знаю сколько в рублях"))
    markup.add(types.KeyboardButton("↩️Вернуться в начало"))
    return markup


def usd_price_or_to_start() -> types.ReplyKeyboardMarkup:
    """
    Меню, определение стоимости в рублях или возврат в начало:
    💵️Я знаю сколько в долларах
    🆕 Добавить новый актив
    """
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("💵️Я знаю сколько в долларах"))
    markup.add(types.KeyboardButton("↩️Вернуться в начало"))
    return markup


def add_active_or_to_start() -> types.ReplyKeyboardMarkup:
    """
    Меню, добавление актива или возврат в начало:
    🆕 Добавляем
    ↩️Вернуться в начало
    """
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("🆕 Добавляем"))
    markup.add(types.KeyboardButton("↩️Вернуться в начало"))
    return markup

def url_news_button(url):
    """
    Кнопка url отправляющая на новостной сайт
    """
    markup = types.InlineKeyboardMarkup()
    button1 = types.InlineKeyboardButton("Ссылка на источник", url=url)
    markup.add(button1)
    return markup


def get_all_news():
    """
    Кнопка inline для получения всех новостей
    """
    markup = types.InlineKeyboardMarkup()
    button1 = types.InlineKeyboardButton("Получить", callback_data="get_all_news")
    markup.add(button1)

    return markup

def mailing_period_button():
    """
    Меню для выбора периода рассылки отчета
    """
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("🔄 Ежедневно"))
    markup.add(types.KeyboardButton("📆 Еженедельно"))
    markup.add(types.KeyboardButton("📅 Ежемесячно"))
    markup.add(types.KeyboardButton("↩️Вернуться в начало"))
    return markup

    return markup

def mailing_week_button():
    """
    Меню для выбора дня недели для рассылки отчета
    """
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("1⃣ Понедельник"))
    markup.add(types.KeyboardButton("2⃣ Вторник"))
    markup.add(types.KeyboardButton("3⃣ Среда"))
    markup.add(types.KeyboardButton("4⃣ Четверг"))
    markup.add(types.KeyboardButton("5⃣ Пятница"))
    markup.add(types.KeyboardButton("6⃣ Суббота"))
    markup.add(types.KeyboardButton("7⃣ Воскресенье"))
    markup.add(types.KeyboardButton("↩️Вернуться в начало"))
    return markup

    return markup

def mailing_day_button():
    """
    Меню для выбора дня недели для рассылки отчета
    """
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("🚩 В начале месяца"))
    markup.add(types.KeyboardButton("↔ В середине месяца"))
    markup.add(types.KeyboardButton("🏁 В конце месяца"))
    markup.add(types.KeyboardButton("↩️Вернуться в начало"))
    return markup

    return markup

def mailing_time_button():
    """
    Меню для выбора времени рассылки отчета
    """
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("🕙 10:00"))
    markup.add(types.KeyboardButton("🕛 12:00"))
    markup.add(types.KeyboardButton("🕑 14:00"))
    markup.add(types.KeyboardButton("🕓 16:00"))
    markup.add(types.KeyboardButton("🕕 18:00"))
    markup.add(types.KeyboardButton("↩️Вернуться в начало"))
    return markup

    return markup