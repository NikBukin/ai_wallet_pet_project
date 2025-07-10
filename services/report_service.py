import time
from database.repository import Repository
from services.report_builder import det_text_to_report
import pytz
import schedule
import threading

class ReportService:
    @staticmethod
    def send_report_to_user(chat_id: int, bot):
        """
        Формирует отчёт для одного пользователя и отсылает в чат.
        """
        assets = Repository.select_by_id_telebot(chat_id)
        if assets.empty:
            bot.send_message(chat_id, "У тебя пока нет активов в портфеле.", reply_markup=None)
            return

        report_text = det_text_to_report(assets)
        bot.send_message(chat_id, report_text, parse_mode="Markdown", reply_markup=None)

    @staticmethod
    def send_report_to_all(bot):
        """
        Рассылает отчёт всем пользователям, у которых есть хотя бы одна запись.
        """
        all_users = Repository.select_all()

        if all_users.empty:
            return

        # Получаем уникальные id_telebot
        user_ids = all_users['id_telebot'].unique()

        for uid in user_ids:
            assets = Repository.select_by_id_telebot(uid)
            if assets.empty:
                continue
            report_text = det_text_to_report(assets)
            bot.send_message(uid, report_text, parse_mode="Markdown")
            time.sleep(0.5)

    @staticmethod
    def schedule_daily_report(bot, escape_md=None):
        """
        Настраивает ежедневно в 18:00 (МСК) рассылку всем пользователям.
        """
        moscow_tz = pytz.timezone('Europe/Moscow')

        def job():
            ReportService.send_report_to_all(bot)

        schedule.every().day.at("18:00").do(job)

        def run_scheduler():
            while True:
                schedule.run_pending()
                time.sleep(1)

        thread = threading.Thread(target=run_scheduler, daemon=True)
        thread.start()