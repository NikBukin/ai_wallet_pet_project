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


def generate_answer(parsed):
    # parsed может быть None, если LLM не нашла JSON вовсе
    if not parsed:
        return "⚠️ LLM не вернула структуру. Попробуйте иначе."

    # 5) Определяем, каких полей не хватает
    missing = []
    print(parsed)
    for key in ["name_active", "count", "price", "currency", "day_buy"]:
        val = parsed.get(key) if key in parsed else None
        if val is None or (isinstance(val, str) and not val.strip()) or (isinstance(val, (int, float)) and val == 0 and key not in ["count"]):
            missing.append(key)

    return parsed, missing



