import requests
from bs4 import BeautifulSoup
import csv
import time
from datetime import datetime, timedelta

class Scraper:
    def __init__(self, url: str, keywords: list[str],
                 output_file: str, years: int = 5, max_pages: int = 150):
        self.BASE_URL = url
        self.KEYWORDS = keywords
        self.OUTPUT_FILE = output_file
        self.YEARS = years
        self.MAX_PAGES = max_pages

    def contains_keyword(self, text) -> bool:
        """Проверка, содержит ли текст ключевое слово о золоте"""
        if not text:
            return False
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.KEYWORDS)

    @staticmethod
    def parse_date(date_str) -> None | datetime:
        """Парсинг даты из строки формата 'DD.MM.YYYY | hh:mm'"""
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

    @staticmethod
    def get_article_details(url) -> str:
        """Получение полного текста статьи"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            article_text = ""

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

    def scrape_page(self, page_num) -> tuple[list, bool]:
        """Парсинг одной страницы новостей"""
        url = self.BASE_URL if page_num == 1 else f"{self.BASE_URL}?page={page_num}"

        print(f"Обработка страницы {page_num}: {url}")

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Все карточки новостей
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

                    # Абсолютная ссылка
                    if article_url and not article_url.startswith('http'):
                        article_url = f"https://www.finversia.ru{article_url}"

                    # Краткое описание
                    descr_elem = item.find('div', class_='descr')
                    description = descr_elem.get_text(strip=True) if descr_elem else ""

                    # Проверка на ключевое слово
                    if not self.contains_keyword(title) and not self.contains_keyword(description):
                        continue

                    # Дата
                    date_elem = item.find('div', class_='date')
                    date_str = date_elem.get_text(strip=True) if date_elem else ""
                    parsed_date = self.parse_date(date_str)

                    # Проверка даты
                    if parsed_date:
                        cutoff_date = datetime.now() - timedelta(days=365 * self.YEARS)
                        if parsed_date < cutoff_date:
                            print(f"Достигнута дата за пределами {self.YEARS} лет: {date_str}")
                            return articles, True

                    print(f"Найдена статья по ключевому слову {self.KEYWORDS}: {title[:50]}...")

                    # Весь текст
                    print(f"  Загрузка полного текста...")
                    full_text = self.get_article_details(article_url)

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

    def parsing(self):
        """Основная функция парсинга"""
        print(f"Начало парсинга новостей по ключевому слову {self.KEYWORDS} с {self.BASE_URL}")
        print(f"Период: последние {self.YEARS} лет")
        print(f"Результаты будут сохранены в: {self.OUTPUT_FILE}\n")

        all_articles = []
        page = 1
        should_stop = False

        #CSV файл
        with open(self.OUTPUT_FILE, 'w', newline='', encoding='utf-8-sig') as csvfile:
            fieldnames = ['Заголовок', 'Описание', 'Полный текст', 'Дата и время', 'URL']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            while page <= self.MAX_PAGES and not should_stop:
                articles, should_stop = self.scrape_page(page)

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

                print(f"Страница {page}: найдено {len(articles)} статей по ключевому слову {self.KEYWORDS}")
                print(f"Всего собрано: {len(all_articles)} статей\n")

                if should_stop:
                    print(f"Достигнут предел в {self.YEARS} лет. Парсинг завершён.")
                    break

                page += 1
                time.sleep(2)

        print(f"\n{'=' * 60}")
        print(f"Парсинг завершён!")
        print(f"Всего найдено статей по ключевому слову {self.KEYWORDS}: {len(all_articles)}")
        print(f"Результаты сохранены в файл: {self.OUTPUT_FILE}")
        print(f"{'=' * 60}")


if __name__ == "__main__":
    scarper = Scraper(url='https://www.finversia.ru/dragmetally',
                      keywords=['золот'], output_file='test.csv', max_pages=2)
    scarper.parsing()
