import re

class SchedulerService:
    @staticmethod
    def start_scheduler(bot):
        """
        Инициализирует планировщик рассылки отчётов.
        """
        from services.report_service import ReportService
        # escape_md передадим как ссылку на функцию escape_markdown из handlers
        ReportService.schedule_daily_report(bot, escape_md=escape_markdown)

def escape_markdown(text):
    """
    Экранирует спецсимволы Markdown
    """
    if text == None: text = ""
    escape_chars = r"_*[]~`>#+-=|{}!"
    return re.sub(f"([{re.escape(escape_chars)}])", r"\\\1", text)


def escape_markdown_v2(text: str) -> str:
    """
    Экранирует строку по требованиям Telegram MarkdownV2.
    """
    if not text:
        return ""
    # Экранируем все символы, в том числе `-`
    escape_chars = r"_*[]()~`>#+-=|{}.!"
    return re.sub(f"([{re.escape(escape_chars)}])", r"\\\1", text)



