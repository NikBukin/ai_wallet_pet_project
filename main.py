from bot.handlers import bot
from services.scheduler_service import SchedulerService
import time

if __name__ == "__main__":
    # Инициализируем планировщик
    SchedulerService.start_scheduler(bot)
    # if __name__ == '__main__':
    #     while True:
    #         try:
    #             bot.polling(none_stop=True, skip_pending=True)
    #         except Exception as e:
    #             time.sleep(3)
    #             print(e)
    bot.polling(none_stop=True, skip_pending=True)