import time, threading, pytz, schedule
from datetime import datetime, timedelta
from database.repository import Repository
from services.report_builder import det_text_to_report


class ReportService:
    """Формирование и отправка отчётов."""

    @staticmethod
    def send_report_to_user(chat_id: int, bot) -> None:
        assets = Repository.select_by_id_telebot(chat_id)
        if assets.empty:
            bot.send_message(chat_id, "У тебя пока нет активов в портфеле.")
            return
        bot.send_message(chat_id,
                         det_text_to_report(assets),
                         parse_mode="Markdown")

    @staticmethod
    def send_report_to_all(bot) -> None:
        all_users = Repository.select_all()
        for uid in all_users["id_telebot"].unique():
            ReportService.send_report_to_user(uid, bot)


class MailingScheduler:
    """
    Управляет индивидуальными расписаниями рассылок.
    1 obj == 1 общий поток schedule.run_pending()
    """

    MOSCOW_TZ = pytz.timezone("Europe/Moscow")

    def __init__(self, bot):
        self.bot = bot
        self.jobs: dict[int, schedule.Job] = {}
        self._start_runner()

    # ---------- работа с задачами ----------
    def bootstrap_from_db(self):
        for row in Repository.get_mailing_settings_all().itertuples():
            self._create_job(row)

    def upsert_user(self, user_id: int):
        if job := self.jobs.pop(user_id, None):
            schedule.cancel_job(job)
        if (row := Repository.get_mailing_settings(user_id)) is not None:
            self._create_job(row)

    def _create_job(self, row):
        user_id = row.user_id
        m_period = row.m_period  # 🔄 / 📆 / 📅
        m_day_choice = row.m_day  # строка из кнопки ("🚩 …")
        m_day_week = row.m_day_in_week  # 0-6 для weekly
        m_time = row.m_time[2:]  # ' 18:00' → '18:00'
        send = lambda: ReportService.send_report_to_user(user_id, self.bot)

        if m_period == "🔄 Ежедневно":
            job = schedule.every().day.at(m_time).do(send)

        elif m_period == "📆 Еженедельно":
            # m_day_week хранится цифрой 0-6 (пн-вс)
            week_day = self._dow_str(m_day_week)
            job = getattr(schedule.every(), week_day).at(m_time).do(send)

        elif m_period == "📅 Ежемесячно":
            # ежедневный крон + собственная проверка внутри
            def monthly_wrapper():
                today = datetime.now(self.MOSCOW_TZ).date()

                if m_day_choice == "🚩 В начале месяца" and today.day == 1:
                    send()

                elif m_day_choice == "↔ В середине месяца" and today.day == 15:
                    send()

                elif m_day_choice == "🏁 В конце месяца":
                    tomorrow = today + timedelta(days=1)
                    if tomorrow.day == 1:  # сегодня последний день
                        send()

            job = schedule.every().day.at(m_time).do(monthly_wrapper)

        else:
            return

        self.jobs[user_id] = job

    # ---------- фоновый раннер ----------
    def _start_runner(self):
        threading.Thread(
            target=self._loop, daemon=True, name="mailing-scheduler"
        ).start()

    @staticmethod
    def _loop():
        while True:
            schedule.run_pending()
            time.sleep(1)

    @staticmethod
    def _dow_str(num: int) -> str:
        return ["1⃣ Понедельник", "2⃣ Вторник", "⃣ Среда", "4⃣ Четверг", "⃣ Пятница", "6⃣ Суббота", "⃣ Воскресенье"][int(num)]


# ---------- точка входа для сервиса ----------
def init_scheduler(bot):
    scheduler = MailingScheduler(bot)
    scheduler.bootstrap_from_db()
    return scheduler