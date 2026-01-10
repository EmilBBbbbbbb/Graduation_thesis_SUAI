import requests
from bs4 import BeautifulSoup
import csv
import time
from datetime import datetime, timedelta
import re
import sys

# Конфигурация
BASE_URL = "https://www.finversia.ru/dragmetally"
KEYWORDS = ["золот"]  # Слова для фильтрации новостей о золоте
OUTPUT_FILE = "../gold_news.csv"
YEARS = 5
MAX_PAGES = 100  # Максимальное количество страниц для проверки

# Тестовый режим: обрабатывает только несколько страниц
TEST_MODE = "--test" in sys.argv or "-t" in sys.argv
if TEST_MODE:
    MAX_PAGES = 2
    OUTPUT_FILE = "gold_news_test.csv"
    print("⚠️  ТЕСТОВЫЙ РЕЖИМ: Будут обработаны только первые 2 страницы")
    print(f"⚠️  Результаты сохранятся в: {OUTPUT_FILE}\n")


def contains_keyword(text):
    """Проверка, содержит ли текст ключевое слово о золоте"""
    if not text:
        return False
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in KEYWORDS)


def parse_date(date_str):
    """Парсинг даты из строки формата '07.01.2026 | 20:39'"""
    try:
        if '|' in date_str:
            date_part = date_str.split('|')[0].strip()
            time_part = date_str.split('|')[1].strip()
            datetime_str = f"{date_part} {time_part}"
            return datetime.strptime(datetime_str, "%d.%m.%Y %H:%M")
        return None
    except Exception as e:
        print(f"Ошибка парсинга даты '{date_str}': {e}")
        return None


def get_article_details(url):
    """Получение полного текста статьи"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Ищем основной текст статьи
        article_text = ""
        
        # Попытка найти текст в различных возможных контейнерах
        article_body = soup.find('div', class_='b-publication-text')
        if not article_body:
            article_body = soup.find('div', class_='b-news-text')
        if not article_body:
            article_body = soup.find('article')
        if not article_body:
            article_body = soup.find('div', class_='content')
        
        if article_body:
            # Извлекаем текст из всех параграфов
            paragraphs = article_body.find_all(['p', 'div'])
            article_text = ' '.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
        
        return article_text.strip() if article_text else "Текст не найден"
        
    except Exception as e:
        print(f"Ошибка при получении статьи {url}: {e}")
        return "Ошибка загрузки текста"


def scrape_page(page_num):
    """Парсинг одной страницы новостей"""
    url = BASE_URL if page_num == 1 else f"{BASE_URL}?page={page_num}"
    
    print(f"Обработка страницы {page_num}: {url}")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Находим все карточки новостей
        news_items = soup.find_all('div', class_='b-item-cont')
        
        articles = []
        
        for item in news_items:
            try:
                # Заголовок и ссылка
                title_elem = item.find('a', class_='title')
                if not title_elem:
                    continue
                    
                title = title_elem.get_text(strip=True)
                article_url = title_elem.get('href', '')
                
                # Делаем ссылку абсолютной
                if article_url and not article_url.startswith('http'):
                    article_url = f"https://www.finversia.ru{article_url}"
                
                # Краткое описание
                descr_elem = item.find('div', class_='descr')
                description = descr_elem.get_text(strip=True) if descr_elem else ""
                
                # Проверяем, есть ли слово "золото" в заголовке или описании
                if not contains_keyword(title) and not contains_keyword(description):
                    continue
                
                # Дата
                date_elem = item.find('div', class_='date')
                date_str = date_elem.get_text(strip=True) if date_elem else ""
                parsed_date = parse_date(date_str)
                
                # Проверяем, попадает ли дата в диапазон последних 5 лет
                if parsed_date:
                    cutoff_date = datetime.now() - timedelta(days=365 * YEARS)
                    if parsed_date < cutoff_date:
                        print(f"Достигнута дата за пределами {YEARS} лет: {date_str}")
                        return articles, True  # Возвращаем флаг, что достигли предела
                
                print(f"Найдена статья о золоте: {title[:50]}...")
                
                # Получаем полный текст статьи
                print(f"  Загрузка полного текста...")
                full_text = get_article_details(article_url)
                time.sleep(1)  # Задержка между запросами
                
                articles.append({
                    'title': title,
                    'description': description,
                    'full_text': full_text,
                    'date': date_str,
                    'url': article_url
                })
                
            except Exception as e:
                print(f"Ошибка обработки элемента: {e}")
                continue
        
        return articles, False
        
    except Exception as e:
        print(f"Ошибка загрузки страницы {page_num}: {e}")
        return [], False


def main():
    """Основная функция парсинга"""
    print(f"Начало парсинга новостей о золоте с {BASE_URL}")
    print(f"Период: последние {YEARS} лет")
    print(f"Результаты будут сохранены в: {OUTPUT_FILE}\n")
    
    all_articles = []
    page = 1
    should_stop = False
    
    # Создаём CSV файл и записываем заголовок
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8-sig') as csvfile:
        fieldnames = ['Заголовок', 'Описание', 'Полный текст', 'Дата и время', 'URL']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        while page <= MAX_PAGES and not should_stop:
            articles, should_stop = scrape_page(page)
            
            if not articles and page > 1:
                print("Новостей больше не найдено.")
                break
            
            # Записываем найденные статьи в CSV
            for article in articles:
                writer.writerow({
                    'Заголовок': article['title'],
                    'Описание': article['description'],
                    'Полный текст': article['full_text'],
                    'Дата и время': article['date'],
                    'URL': article['url']
                })
                all_articles.append(article)
            
            print(f"Страница {page}: найдено {len(articles)} статей о золоте")
            print(f"Всего собрано: {len(all_articles)} статей\n")
            
            if should_stop:
                print(f"Достигнут предел в {YEARS} лет. Парсинг завершён.")
                break
            
            page += 1
            time.sleep(2)  # Задержка между страницами
    
    print(f"\n{'='*60}")
    print(f"Парсинг завершён!")
    print(f"Всего найдено статей о золоте: {len(all_articles)}")
    print(f"Результаты сохранены в файл: {OUTPUT_FILE}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
