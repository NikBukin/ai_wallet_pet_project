import feedparser
import requests
from bs4 import BeautifulSoup
import html
from datetime import datetime, timedelta
from rapidfuzz import fuzz


def extract_article_text(url):
    headers = {
        'User-Agent': 'Mozilla/5.0'
    }
    try:

        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Yahoo / Fool.com
        if "yahoo.com" in url or "fool.com" in url:
            paragraphs = soup.find_all('p')
            return "\n".join([p.get_text(strip=True) for p in paragraphs])

        # CryptoCompare or coin sites
        elif "coin" in url or "crypto" in url:

            garbage_keywords = [
                "Bonus", "Join Drake", "Claim $25", "Search keywords",
                "Stake Cash FREE", "PLAY NOW", "Provably Fair", "America's Social Casino"
            ]
            paragraphs = soup.find_all('p')
            text = "\n".join([p.get_text(strip=True) for p in paragraphs])
            lines = text.splitlines()
            filtered = [line for line in lines if all(gk.lower() not in line.lower() for gk in garbage_keywords)]
            return "\n".join(filtered).strip()

        return ""
    except Exception as e:
        print(f"[ERROR] Failed to fetch {url}: {e}")
        return ""

# Российские акции Finam
def get_finam_news(ticker_list=None, max_entries=10, min_score=70):
    """
    ticker_list — список [SBER, GAZP, LKOH]
    min_score — минимальный порог похожести
    """
    rss_url = "https://www.finam.ru/analysis/conews/rsspoint/"
    feed = feedparser.parse(rss_url)

    now = datetime.now()
    results = []

    for entry in feed.entries:
        published_dt = datetime.strptime(entry.published, '%a, %d %b %Y %H:%M:%S %z')
        now = datetime.now(published_dt.tzinfo)

        if published_dt < now - timedelta(days=2):
            continue

        title = entry.title
        description = entry.description
        clean_html = BeautifulSoup(description, "html.parser").get_text()
        clean_text = html.unescape(clean_html)
        combined_text = (title + " " + clean_text).lower()

        if ticker_list:
            match_found = False
            for t in ticker_list:
                score = fuzz.partial_ratio(t.lower(), combined_text)
                if score >= min_score:
                    match_found = True
                    break
            if not match_found:
                continue  # если ни один тикер не попал — пропускаем

        results.append({
            "title": title,
            "link": entry.link,
            "published": published_dt,
            "text": description
        })

        if len(results) >= max_entries:
            break

    return results


# Иностранные акции и металлы через Yahoo Finance RSS
def get_yahoo_news(query, max_entries=10):
    feed_url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={query}&region=US&lang=en-US"
    feed = feedparser.parse(feed_url)
    news = []

    for entry in feed.entries[:max_entries]:
        published_str = entry.published
        published_dt = datetime.strptime(published_str, '%a, %d %b %Y %H:%M:%S %z')
        now = datetime.now(published_dt.tzinfo)
        if published_dt > now - timedelta(days=1):
            news.append({
                "title": entry.title,
                "link": entry.link,
                "published": published_dt,
                "text": extract_article_text(entry.link)
            })

    return news


# CryptoCompare – криптовалюты
def get_crypto_news(query="bitcoin", max_entries=10):
    url = f"https://min-api.cryptocompare.com/data/v2/news/?lang=EN"
    response = requests.get(url)
    news = response.json().get("Data", [])
    results = []
    for item in news:
        published_str = item["published_on"]
        published_dt = datetime.fromtimestamp(published_str)
        now = datetime.now(published_dt.tzinfo)
        if (query.lower() in item["title"].lower() or query.lower() in item["body"].lower()) and published_dt > now - timedelta(days=1):
            results.append({
                "title": item["title"],
                "link": item["url"],
                "published": published_dt,
                "text": extract_article_text(item["url"])
            })
        if len(results) >= max_entries:
            break
    return results
