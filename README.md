# AI Wallet Pet Project

> **Телеграм‑бот на базе LLM, который помогает отслеживать инвестиционный портфель, анализировать рыночные новости и общаться с данными на естественном языке.**

---

## Содержание
1. [Возможности](#возможности)
2. [Архитектура](#архитектура)
3. [Архитектура](#архитектура)
4. [Быстрый старт](#быстрый-старт)
5. [Конфигурация](#конфигурация)
6. [Изменение базы знаний (RAG)](#изменение-базы-знаний-rag)

---

## Возможности

### **Учёт активов**
Возможность управления инвестиционным кошельком (добавление/удаление/изменение количества).
![Screen_3](https://github.com/user-attachments/assets/b40b4c7d-1fd3-44c0-b5e0-232e0693246b)

### **Голосовые команды**
Бот способен распознавать голосовые сообщения.
![Screen_6](https://github.com/user-attachments/assets/34454001-cc4f-4f33-9ab7-bbd0639c505a)

### **Анализ новостей**
Интеграция с парсерами новостных лент и генеративной моделью для кратких резюме.
![Screen_2](https://github.com/user-attachments/assets/39a70521-1914-46a0-86ae-b728443feca0)

### **Анализ портфеля**
Получение аналитики по портфелю через формирование sql запроса к базе данных
![Screen_1](https://github.com/user-attachments/assets/174fb40e-aa0d-40ca-b2ce-b07d7a671334)


### **RAG‑поиск**
Отвтеы на вопросы на основе книг/статей, загруженных в векторную БД FAISS.
![Screen_4](https://github.com/user-attachments/assets/7f372d03-61ed-4111-a299-e9d4ce3c0995)

### **Отчёты**
Автоматическая регулярная сводка по портфелю в виде структурированного отчета.
![Screen_5](https://github.com/user-attachments/assets/7076455d-13c6-48d3-8514-d68789713937)

---

## Архитектура

```
ai_wallet_pet_project
├── bot/             # Телеграм‑слой (aiogram)
│   ├── handlers.py  # Основные обработчики сообщений
│   └── keyboards.py # Клавиатура
├── content/         # Векторная БД FAISS + pdf-файлы 
├── database/        # Работа с БД, SQLite
├── models/          # LLM‑агенты, маршрутизация запросов
├── pars_info/       # Парсеры новостей и котировок
├── services/        # Бизнес‑логика (отчёты, форматтеры)
├── main.py          # Точка входа
└── Retriveral.py    # Генерация нового БД (RAG)
```

---

## Ключевые технологические компоненты проекта

| Технология                                            | Назначение в боте                                                                   | Главные файлы / директории                                                      |
| ----------------------------------------------------- | ----------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| **Telegram-бот** <br>*(PyTelegramBotAPI)*             | Приём/отправка сообщений, обработка команд, inline-клавиатуры, управление диалогами | `bot/handlers.py`, `bot/keyboards.py`, `main.py`                                |
| **LLM (Yandex GPT)**                                  | Генерация ответов, анализ новостей, построение отчётов и диалоговых веток           | `models/llm_router.py`, `models/llm_news_analysis.py`, `models/llm_with_RAG.py` |
| **LangChain**                                         | Оркестрация цепочек LLM, подключение инструментов (SQL, RAG)                        | те же файлы модуля **models** + `models/llm_sql_database_toolkit.py`            |
| **SQLite**                                            | Хранение активов пользователей, работа с БД                                         | `database/db_active.db`, `database/repository.py`, `database/init_db.py`        |
| **RAG + FAISS**                                       | Векторная база знаний книг/статей; улучшение ответов LLM фактами                    | `content/rag_vector_db/`, `models/llm_with_RAG.py`                              |
| **Pandas**                                            | Табличные операции и построение фин. отчётов (своды, группировки, форматирование)   | `services/report_builder.py`, `pars_info/pars_kotr.py`                          |
| **Парсинг данных** <br>*(requests, lxml, feedparser)* | Сбор котировок, курсов ЦБ, RSS-новостей                                             | `pars_info/pars_kotr.py`, `pars_info/pars_news.py`                              |
| **Финансовые API** <br>*(yfinance, Coingecko)*        | Получение цен акций, металлов, криптовалют                                          | `pars_info/pars_kotr.py`, `services/report_service.py`                          |
| **Поиск по активам** <br>*(RapidFuzz)*                | Нечёткое сопоставление тикеров и названий при вводе пользователя                    | `pars_info/search_active.py`, `bot/handlers.py`                                           |
| **Speech-to-Text** <br>*(Whisper + Pydub)*            | Распознавание голосовых сообщений пользователей                                     | `models/speech_to_text.py`                                                      |
| **Планировщик задач** <br>*(schedule + pytz)*         | Ежедневная рассылка отчётов и напоминаний c учётом часового пояса                   | `services/scheduler_service.py`, `services/report_service.py`                   |


---

## Быстрый старт

```bash
# 1. Клонируем репозиторий
$ git clone https://github.com/NikBukin/ai_wallet_pet_project.git
$ cd ai_wallet_pet_project

# 2. Создаём виртуальное окружение
$ python -m venv .venv
$ source .venv/bin/activate

# 3. Устанавливаем зависимости
$ pip install -r requirements.txt

# 4. Настраиваем переменные окружения (см. ниже)

# 5. Запускаем бота
$ python main.py
```

---

## Конфигурация

Создайте файл `.env` в корне проекта или экспортируйте переменные окружения:

```env
TELEGRAM_TOKEN=6075...
API_KEY_LLM=AQVN3...
FOLDER_ID_LLM=b1go...
```

---

## Изменение базы знаний (RAG)

1. Сложите PDF файлы в `content/`.
2. Запустите скрипт индексации:

   ```bash
   python Retriveral.py
   ```
3. Перезапустите бота.


