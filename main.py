from bot.handlers import bot
from database.init_db import init_db
from services.report_service import init_scheduler
import time

if __name__ == "__main__":
    # Инициализируем планировщик
    scheduler = init_scheduler(bot)
    init_db()
    bot.remove_webhook()
    if __name__ == '__main__':
        while True:
            try:
                bot.polling(none_stop=True, skip_pending=True)
            except Exception as e:
                time.sleep(3)
                print(e)