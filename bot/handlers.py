import telebot
from telebot import types
from bot import keyboards
import datetime
import os
from dotenv import load_dotenv
from rapidfuzz import process

from pars_info import pars_kotr
from pars_info.search_active import search_active_from_pars
from models import speech_to_text, llm_news_analysis
from database.repository import Repository
from services.scheduler_service import escape_markdown, escape_markdown_v2, generate_answer
from services.report_service import ReportService
from models.llm_router import llm_router

load_dotenv()
telegram_token = os.getenv("TELEGRAM_TOKEN")

bot = telebot.TeleBot(telegram_token, skip_pending=True)

# # Сохранение списка активов

user_dict = {}


class User:
    def __init__(self, userid):
        self.userid = userid

        self.userfirstname = None
        self.userlastname = None

        self.name_telebot = None
        self.date = None
        self.type_active = None
        self.name_active = None
        self.shortname_active = None
        self.count = 0
        self.day_buy = None
        self.price_buy_USD = 0
        self.price_buy_RUB = 0

        self.slov_to_del = None
        self.id_to_del = None

        self.select_active = None
        self.curr = None

        self.recognized_text = ""
        self.parsed_partial = None
        self.missing_fields = []
        self.analysis_slov = None

        self.llm_result = None

        self.mailing_period = None
        self.mailing_time = None
        self.mailing_day = None
        self.mailing_week = None


# команда /start
@bot.message_handler(commands=['start']
                     # , func=lambda message: message.chat.id in users
                     )
def send_start(message):
    chat_id = message.chat.id
    user = User(chat_id)
    user_dict[chat_id] = user
    user.userfirstname = message.chat.first_name
    user.userlastname = message.chat.last_name

    msg = bot.send_message(chat_id,
                           text="Привет!✌\n\n"
                                "Я твой личный инвестиционный ассистент!🤖\n"
                                "Ты можешь выбрать из предложенных вариантов или запросить в свободной форме:"
                                "\n🆕 Добавление нового актива в портфель"
                                "\n📈 Анализ твоего инвестиционного портфеля"
                                "\n💭 Анализ новостей за последние сутки по любому активу"
                                "\n🧐 Теоретическую информацию из моей базы знаний",
                           reply_markup=keyboards.main_menu_markup(), parse_mode="Markdown")
    bot.register_next_step_handler(msg, start_bot)


@bot.message_handler(content_types=['Начать заново'])
def send_welcome(message):
    chat_id = message.chat.id
    userid = message.chat.id
    user = User(userid)
    user_dict[chat_id] = user
    user.userfirstname = message.chat.first_name
    user.userlastname = message.chat.last_name

    msg = bot.send_message(chat_id,
                           text="Привет!✌\n\n"
                                "Я твой личный инвестиционный ассистент!🤖\n"
                                "Ты можешь выбрать из предложенных вариантов или запросить в свободной форме:"
                                "\n🆕 Добавление нового актива в портфель"
                                "\n📈 Анализ твоего инвестиционного портфеля"
                                "\n💭 Анализ новостей за последние сутки по любому активу"
                                "\n🧐 Теоретическую информацию из моей базы знаний",
                           reply_markup=keyboards.main_menu_markup(), parse_mode="Markdown")
    bot.register_next_step_handler(msg, start_bot)


@bot.message_handler(content_types=['text', 'voice'])
def handle_clarification(message):
    chat_id = message.chat.id
    user = user_dict.get(chat_id)
    if user is None:
        bot.send_message(chat_id, "Пожалуйста, сначала нажмите /start.")
        return

    if message.content_type == 'voice':
        file_info = bot.get_file(message.voice.file_id)
        ogg_bytes = bot.download_file(file_info.file_path)

        clarification_text = speech_to_text.generate_text_from_voice(ogg_bytes)
    elif message.content_type == 'text':
        clarification_text = message.text

    if clarification_text[0] == "⚠":
        bot.register_next_step_handler(message, clarification_text)
    else:
        combined_input = user.recognized_text + " " + clarification_text
        user.recognized_text = combined_input
        llm_result = llm_router(combined_input, chat_id)
        user.llm_result = llm_result
        if llm_result['used_tool'] == 'add_asset_tool':
            handle_add_asset(message)
        elif llm_result['used_tool'] == 'analyze_news_tool':
            handle_analyze_news(message)
        elif llm_result['used_tool'] == 'sql_query_tool' or llm_result['used_tool'] == 'rag_tool':
            handle_sql_query_or_rag(message)


def handle_add_asset(message):
    chat_id = message.chat.id
    user = user_dict.get(chat_id)
    llm_result = user.llm_result
    parsed, missing = generate_answer(llm_result['tool_data']['data'])
    recognized_text = user.recognized_text
    user.parsed_partial = parsed
    user.missing_fields = missing
    print("missing", missing)
    if missing:
        human_names = {
            "name_active": "название актива",
            "count": "количество",
            "price": "цену",
            "currency": "валюту покупки",
            "day_buy": "дату покупки"
        }
        missing_str = ", ".join(human_names[f] for f in missing)
        ask = (
            f"Я смог распознать:\n\n«{recognized_text}»\n\n"
            f"Однако не хватает информации: {missing_str}.\n"
            "Пожалуйста, уточните недостающие данные (текстом или голосом), "
            "и я попробую дополнить."
        )
        bot.send_message(chat_id, ask)
        bot.register_next_step_handler(message, handle_clarification)
        return

    # Если ничего не пропало – сразу оформляем подтверждение (как раньше)
    user.type_active = parsed["type_active"]
    user.name_active = parsed["name_active"]
    user.shortname_active = parsed["shortname_active"]
    user.count = parsed["count"]
    user.price_buy_USD = parsed["price_buy_USD"]
    user.price_buy_RUB = parsed["price_buy_RUB"]
    user.day_buy = parsed["day_buy"]

    fmt_rub = f"{user.price_buy_RUB:,.2f}".replace(",", " ")
    fmt_usd = f"{user.price_buy_USD:,.2f}".replace(",", " ")
    confirm_text = (
        "Проверьте, правильно ли я понял данные:\n\n"
        f"• Актив: *{user.name_active}* (тикер `{user.shortname_active}`)\n"
        f"• Тип: `{user.type_active}`\n"
        f"• Количество: `{user.count}`\n"
        f"• Цена: `{fmt_rub}₽` / `{fmt_usd}$`\n"
        f"• Дата покупки: `{user.day_buy}`\n\n"
        "Добавить в базу?"
    )
    msg = bot.send_message(chat_id, text=confirm_text, reply_markup=keyboards.yes_or_no(),
                           parse_mode="Markdown")
    bot.register_next_step_handler(msg, confirm_insert)


def handle_analyze_news(message):
    chat_id = message.chat.id
    user = user_dict.get(chat_id)
    user.recognized_text = ""
    llm_result = user.llm_result

    result_text = llm_result['tool_data']['result_text']
    link = llm_result['tool_data']['link']
    try:
        msg = bot.send_message(chat_id, text=result_text, reply_markup=keyboards.url_news_button(link),
                               parse_mode="Markdown")
    except:
        msg = bot.send_message(chat_id, text=escape_markdown_v2(result_text), reply_markup=keyboards.url_news_button(link),
                               parse_mode="MarkdownV2")
    bot.register_next_step_handler(msg, start_bot)


def handle_sql_query_or_rag(message):
    chat_id = message.chat.id
    user = user_dict.get(chat_id)
    user.recognized_text = ""
    llm_result = user.llm_result

    result_text = llm_result['output']
    try:
        msg = bot.send_message(chat_id, text=result_text,
                               parse_mode="Markdown")
    except:
        msg = bot.send_message(chat_id, text=escape_markdown_v2(result_text),
                               parse_mode="MarkdownV2")
    bot.register_next_step_handler(msg, start_bot)



@bot.message_handler(content_types=['text'])
def start_bot(message):
    chat_id = message.chat.id
    user = user_dict[chat_id]
    if message.text == "/start":
        send_welcome(message)
    elif message.text == "📑 Получить отчет":
        ReportService.send_report_to_user(int(chat_id), bot)
    elif message.text == "📨 Настроить рассылку":
        mailing_setup(message)
    elif message.text == "🔃 Изменить активы":
        change_active(message)
    elif message.text == "💭 Рекомендации из новостей":
        results, analysis_slov = llm_news_analysis.analyze_assets_with_news(int(chat_id), bot)
        user.analysis_slov = analysis_slov
        try:
            bot.send_message(chat_id,
                             text=results,
                             reply_markup=keyboards.get_all_news(), parse_mode="Markdown")
        except:
            bot.send_message(chat_id,
                             text=escape_markdown_v2(results),
                             reply_markup=keyboards.get_all_news(), parse_mode="MarkdownV2")

    else:
        handle_clarification(message)

def change_active(message):
    chat_id = message.chat.id

    msg = bot.send_message(chat_id,
                           text="Какой из активов тебе необходимо изменить?\n\n "
                                "Ты также можешь написать\записать голосовое сообщение в свободной форме, указав количество купленного актива, стоимость за единицу и дату покупки."
                                "\n_Например: Я купил 5 акций Сбербанка 2 июня 2025 года по цене 300 рублей за штуку_",
                           reply_markup=keyboards.asset_type_menu_markup(), parse_mode="Markdown")
    bot.register_next_step_handler(msg, change_type_active)


def change_type_active(message):
    chat_id = message.chat.id
    user = user_dict[chat_id]

    if message.text == "🪙 Криптовалюта":
        user.type_active = "cripto"
        change_db(message)
    elif message.text == "📑 Российские акции":
        user.type_active = "stock_rus"
        change_db(message)
    elif message.text == "📄 Иностранные акции":
        user.type_active = "stock_for"
        change_db(message)
    elif message.text == "💵 Валюта":
        user.type_active = "currency"
        change_db(message)
    elif message.text == "🥇 Драгоценные металлы":
        user.type_active = "metal"
        change_db(message)
    else:
        try:
            handle_clarification(message)
        except:
            pass


# Обработчик подтверждения
def confirm_insert(message):
    chat_id = message.chat.id
    user = user_dict[chat_id]
    text = message.text

    if text == "✅ Да":
        # Фактически вставляем запись в базу
        Repository.insert_data_table(
            int(chat_id),
            user.userfirstname + "&" + user.userlastname,
            datetime.datetime.now().strftime('%Y-%m-%d'),
            user.type_active,
            user.name_active,
            user.shortname_active,
            user.count,
            datetime.datetime.strptime(user.day_buy, '%d.%m.%Y').strftime('%Y-%m-%d'),
            user.price_buy_USD,
            user.price_buy_RUB
        )
        bot.send_message(chat_id, "✅ Данные успешно добавлены!", reply_markup=keyboards.back_to_start_markup())
        user.recognized_text = ""
        bot.register_next_step_handler(message, send_welcome)

    elif text == "❌ Нет":
        msg = bot.send_message(chat_id,
                               "Отмена. Что вы хотите сделать?",
                               reply_markup=keyboards.back_to_start_or_retry_markup())
        bot.register_next_step_handler(msg, after_cancel)

    else:
        # Если пользователь ввёл что-то другое
        bot.send_message(chat_id, "Пожалуйста, выберите «✅ Да» либо «❌ Нет».")
        bot.register_next_step_handler(message, confirm_insert)


# Если пользователь отменил и выбрал “📝 Ввести снова”
def after_cancel(message):
    chat_id = message.chat.id
    if message.text == "↩️Вернуться в начало":
        send_welcome(message)
    elif message.text == "📝 Ввести снова":
        change_active(message)
    else:
        bot.send_message(chat_id, "Нажмите одну из кнопок.")
        bot.register_next_step_handler(message, after_cancel)


def change_db(message):
    chat_id = message.chat.id
    user = user_dict[chat_id]
    req_db = Repository.select_by_id_telebot(int(chat_id))
    result = req_db.loc[(req_db['type_active'] == user.type_active)]

    if len(result) > 0:
        msg = bot.send_message(chat_id,
                               text="Я нашел записи о твоих активах. Хочешь добавить еще или удалить текущие?",
                               reply_markup=keyboards.add_new_or_delete(), parse_mode="Markdown")

        bot.register_next_step_handler(msg, change_cripto_db)

    else:
        msg = bot.send_message(chat_id,
                               text="У меня нет информации о твоем активе 🧐\n"
                                    "Давай добавим?",
                               reply_markup=keyboards.add_new_or_to_start(), parse_mode="Markdown")
        bot.register_next_step_handler(msg, change_cripto_db)


def change_cripto_db(message):
    chat_id = message.chat.id
    user = user_dict[chat_id]

    if message.text == "↩️Вернуться в начало":
        send_welcome(message)
    elif message.text == "🆕 Добавить новый актив":
        msg = bot.send_message(chat_id,
                               text=f"Напиши название, а я постараюсь его найти 🔎\n\n"
                                    f"_Например: bitcoin, SBER, USD_",
                               reply_markup=keyboards.back_to_start_markup(), parse_mode="Markdown")

        bot.register_next_step_handler(msg, search_cripto)




    elif message.text == "❌ Удалить из портфеля":
        req_db = Repository.select_by_id_telebot(int(chat_id))
        result = req_db.loc[(req_db['type_active'] == user.type_active)]

        id = result["id"].tolist()
        name_active = result["name_of_the_asset"].tolist()
        shortname_active = result["second_name_of_the_asset"].tolist()
        count = result["amount_of_asset"].tolist()
        day_buy = result["asset_purchase_date"].tolist()
        price_buy_USD = result["purchase_price_of_one_asset_in_dollars"].tolist()
        price_buy_RUB = result["purchase_price_of_one_asset_in_rubles"].tolist()

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("↩️Вернуться в начало"))

        slov_to_del = {}

        for i in range(len(result)):
            markup.add(types.KeyboardButton(f"{i + 1}. {name_active[i]} - {count[i]}"))
            slov_to_del[f"{i + 1}. {name_active[i]} - {count[i]}"] = str(id[i])
            bot.send_message(chat_id,
                             text=f"{i + 1}. {escape_markdown(name_active[i])}({escape_markdown(shortname_active[i])}) - {escape_markdown(str(count[i]))}\n"
                                  f"Дата покупки - {escape_markdown(str(day_buy[i]))}\n"
                                  f"Цена покупки (в рублях) - {escape_markdown(str(price_buy_RUB[i]))}\n"
                                  f"Цена покупки (в долларах) - {escape_markdown(str(price_buy_USD[i]))}",
                             parse_mode="Markdown")

        msg = bot.send_message(chat_id,
                               text="Какую запись ты хочешь изменить\удалить?",
                               reply_markup=markup, parse_mode="Markdown")
        user.slov_to_del = slov_to_del

        bot.register_next_step_handler(msg, change_one_cripto_db)


def search_cripto(message):
    chat_id = message.chat.id
    user = user_dict[chat_id]

    if message.text == "↩️Вернуться в начало":
        send_welcome(message)
    else:
        all_cactive_name, combined, select_active, slov = search_active_from_pars(user.type_active)
        if message.text in user.select_active.keys():
            if user.select_active[message.text][0] in all_cactive_name:
                user.name_active = user.select_active[message.text][1]
                user.shortname_active = user.select_active[message.text][0]
                msg = bot.send_message(chat_id,
                                       text=f"Отлично, я нашел *{message.text}*\n"
                                            f"Добавляем в портфель?",
                                       reply_markup=keyboards.add_active_or_to_start(), parse_mode="Markdown")
                bot.register_next_step_handler(msg, insert_count)
        elif message.text in all_cactive_name:
            user.name_active = message.text
            user.shortname_active = slov[message.text]
            msg = bot.send_message(chat_id,
                                   text=f"Отлично, я нашел *{message.text}*\n"
                                        f"Добавляем в портфель?",
                                   reply_markup=keyboards.add_active_or_to_start(), parse_mode="Markdown")
            bot.register_next_step_handler(msg, insert_count)
        else:
            results = process.extract(message.text, combined, limit=10, score_cutoff=50)

            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add(types.KeyboardButton("↩️Вернуться в начало"))
            for match, score, _ in results:
                markup.add(types.KeyboardButton(match))

            msg = bot.send_message(chat_id,
                                   text=f"Я не смог найти *{message.text}* 😓\n"
                                        f"Может что-то из этого _(список в кнопках)_?\n\n"
                                        f"Или попробуй написать иначе",
                                   reply_markup=markup, parse_mode="Markdown")

            bot.register_next_step_handler(msg, search_cripto)


def insert_count(message):
    chat_id = message.chat.id
    if message.text == "↩️Вернуться в начало":
        send_welcome(message)
    elif message.text == "🆕 Добавляем":
        msg = bot.send_message(chat_id,
                               text=f"Напиши количество\n"
                                    f"_Если значение не целочисленное, то пиши через точку (например 1.7873)_",
                               reply_markup=keyboards.back_to_start_markup(), parse_mode="Markdown")
        bot.register_next_step_handler(msg, insert_price_buy_USD)


def insert_price_buy_USD(message):
    chat_id = message.chat.id
    user = user_dict[chat_id]
    if message.text == "↩️Вернуться в начало":
        send_welcome(message)
    else:
        if float(user.count) > 0 and message.text != "💵️Я знаю сколько в долларах":
            user.price_buy_RUB = float(message.text.replace(" ", ""))
            insert_day_buy(message)
        else:
            user.curr = "USD"
            msg = bot.send_message(chat_id,
                                   text=f"Напиши сколько стоила единица актива в долларах США 💵\n"
                                        f"_Если значение не целочисленное, то пиши через точку (например 1.7873)_",
                                   reply_markup=keyboards.rub_price_or_to_start(), parse_mode="Markdown")
            bot.register_next_step_handler(msg, insert_price_buy_RUB)
            user.count = float(message.text.replace(" ", ""))


def insert_price_buy_RUB(message):
    chat_id = message.chat.id
    user = user_dict[chat_id]

    if message.text == "↩️Вернуться в начало":
        send_welcome(message)
    elif message.text == "₽️Я знаю сколько в рублях":
        user.curr = "RUB"
        msg = bot.send_message(chat_id,
                               text=f"Напиши сколько стоила единица актива в российских рублях ₽\n"
                                    f"_Если значение не целочисленное, то пиши через точку (например 1.7873)_",
                               reply_markup=keyboards.usd_price_or_to_start(), parse_mode="Markdown")
        bot.register_next_step_handler(msg, insert_price_buy_USD)
    else:
        user.price_buy_USD = float(message.text.replace(" ", ""))
        insert_day_buy(message)


def insert_day_buy(message):
    chat_id = message.chat.id
    user = user_dict[chat_id]
    if user.curr == "USD":
        user.price_buy_USD = float(message.text.replace(" ", ""))
    elif user.curr == "RUB":
        user.price_buy_RUB = float(message.text.replace(" ", ""))

    if message.text == "↩️Вернуться в начало":
        send_welcome(message)
    else:
        msg = bot.send_message(chat_id,
                               text=f"Напиши когда была осуществлена покупка\nЭто необходимо для предоставления подробного анализа.\n"
                                    f"_Формат типа дд.мм.гггг (например {datetime.datetime.now().strftime('%d.%m.%Y')})_",
                               reply_markup=keyboards.back_to_start_markup(), parse_mode="Markdown")
        bot.register_next_step_handler(msg, insert_in_db)


def insert_in_db(message):
    chat_id = message.chat.id
    user = user_dict[chat_id]
    user.day_buy = message.text.replace(" ", "")
    user_date = datetime.datetime.strptime(message.text.replace(" ", ""), "%d.%m.%Y")

    ruble_exchange = pars_kotr.get_cbr_history(currency_id="R01235",
                                               date_from=user_date.strftime("%d/%m/%Y"),
                                               date_to=user_date.strftime("%d/%m/%Y")
                                               )["rate"].to_list()[0]
    if user.price_buy_USD > 0:
        user.price_buy_RUB = float(user.price_buy_USD) * float(ruble_exchange)
    else:
        user.price_buy_USD = float(user.price_buy_RUB) / float(ruble_exchange)

    Repository.insert_data_table(int(chat_id), user.userfirstname + "&" + user.userlastname,
                                 datetime.datetime.now().strftime('%d.%m.%Y'), user.type_active, user.name_active,
                                 user.shortname_active, user.count, user.day_buy, user.price_buy_USD,
                                 user.price_buy_RUB)
    msg = bot.send_message(chat_id,
                           text=f"Данные успешно добавлены!",
                           reply_markup=keyboards.back_to_start_markup(), parse_mode="Markdown")
    bot.register_next_step_handler(msg, send_welcome)


def change_one_cripto_db(message):
    chat_id = message.chat.id
    user = user_dict[chat_id]
    user.id_to_del = user.slov_to_del[message.text]
    if message.text == "↩️Вернуться в начало":
        send_welcome(message)
    else:
        msg = bot.send_message(chat_id,
                               text=f"Ок, ты хочешь полностью удалить запись или изменить количество?",
                               reply_markup=keyboards.delete_options_markup(), parse_mode="Markdown")
        bot.register_next_step_handler(msg, change_one_cripto_db_2)


def change_one_cripto_db_2(message):
    chat_id = message.chat.id
    user = user_dict[chat_id]
    if message.text == "↩️Вернуться в начало":
        send_welcome(message)

    elif message.text == "❌️Полностью удалить":
        Repository.delete_rows_by_condition(str(user.id_to_del))
        msg = bot.send_message(chat_id,
                               text=f"Запись удалена",
                               reply_markup=keyboards.back_to_start_markup(), parse_mode="Markdown")
        bot.register_next_step_handler(msg, send_welcome)

    elif message.text == "↩️Изменить количество":
        msg = bot.send_message(chat_id,
                               text=f"Напиши новое количество\n"
                                    f"_Если значение не целочисленное, то пиши через точку (например 1.7873)_",
                               reply_markup=keyboards.back_to_start_markup(), parse_mode="Markdown")
        bot.register_next_step_handler(msg, change_count_in_db)


def change_count_in_db(message):
    chat_id = message.chat.id
    user = user_dict[chat_id]
    if message.text == "↩️Вернуться в начало":
        send_welcome(message)
    else:
        Repository.update_count_by_id((user.id_to_del), (message.text))
        msg = bot.send_message(chat_id,
                               text="Количество изменено",
                               reply_markup=keyboards.back_to_start_markup(), parse_mode="Markdown")
        bot.register_next_step_handler(msg, send_welcome)


def mailing_setup(message):
    msg = bot.send_message(message.chat.id,
                           text="Выберите период рассылки отчета",
                           reply_markup=keyboards.mailing_period_button(), parse_mode="Markdown")
    bot.register_next_step_handler(msg, mailing_day)


def mailing_day(message):
    chat_id = message.chat.id
    user = user_dict[chat_id]
    user.mailing_period = message.text
    if message.text == "↩️Вернуться в начало":
        send_welcome(message)
    elif message.text == "📆 Еженедельно":
        msg = bot.send_message(chat_id,
                               text="Выберите день недели для рассылки отчета",
                               reply_markup=keyboards.mailing_week_button(), parse_mode="Markdown")
        bot.register_next_step_handler(msg, mailing_time)
    elif message.text == "📅 Ежемесячно":
        msg = bot.send_message(chat_id,
                               text="Выберите дату рассылки отчета",
                               reply_markup=keyboards.mailing_day_button(), parse_mode="Markdown")
        bot.register_next_step_handler(msg, mailing_time)
    elif message.text == "🔄 Ежедневно":
        mailing_time(message)
    else:
        mailing_setup(message)


def mailing_time(message):
    chat_id = message.chat.id
    user = user_dict[chat_id]
    if message.text == "↩️Вернуться в начало":
        send_welcome(message)
    else:
        if user.mailing_period == "📆 Еженедельно":
            user.mailing_week = message.text
        elif user.mailing_period == "📅 Ежемесячно":
            user.day = message.text
        msg = bot.send_message(chat_id,
                               text="Выберите время рассылки",
                               reply_markup=keyboards.mailing_time_button(), parse_mode="Markdown")
        bot.register_next_step_handler(msg, mailing_time_final)


def mailing_time_final(message):
    chat_id = message.chat.id
    user = user_dict[chat_id]
    if message.text == "↩️Вернуться в начало":
        send_welcome(message)
    else:
        user.mailing_time = message.text
        Repository.update_mailing_settings(chat_id, user.mailing_period, user.mailing_day, user.mailing_week, user.mailing_time)
        msg = bot.send_message(chat_id,
                               text="Данные успешно сохранены, рассылка будет осуществляться в соответствии с указанными параметрами",
                               reply_markup=keyboards.mailing_time_button(), parse_mode="Markdown")
        bot.register_next_step_handler(msg, mailing_day)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    chat_id = call.from_user.id
    user = user_dict[chat_id]
    if call.data == "get_all_news":
        analysis_slov = user.analysis_slov
        for an in analysis_slov.keys():
            analysis_new = analysis_slov[an]
            if len(analysis_new["name_active"]) > 1:
                name_active = ' '.join(analysis_new["name_active"])
                results = analysis_new["llm_result"]
            else:
                name_active = analysis_new["name_active"][0]
                results = analysis_new["llm_result"]
            link = analysis_new["link"][0]

            try:
                bot.send_message(chat_id,
                                 text=f"Для {name_active}\n"
                                      f"{results}",
                                 reply_markup=keyboards.url_news_button(link), parse_mode="Markdown")
            except:
                bot.send_message(chat_id,
                                 text=escape_markdown_v2(f"Для {name_active}\n"
                                                         f"{results}"),
                                 reply_markup=keyboards.url_news_button(link), parse_mode="MarkdownV2")