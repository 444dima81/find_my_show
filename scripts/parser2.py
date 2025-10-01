import csv
from scrapling.fetchers import FetcherSession

BASE_URL = "https://myshows.me/search/all/"
OUTPUT_FILE = "./find_my_show/data/data2.csv"
TOTAL_PAGES = 140

def parse_tvshow(session, url):
    """Парсим страницу отдельного сериала"""
    try:
        page = session.get(url, stealthy_headers=True)

        # Название
        title_elem = page.css_first('h1')
        title = title_elem.text.strip() if title_elem else ""

        # Фото
        image_elem = page.css_first('div.PicturePoster-picture img')
        image_url = image_elem.attrib.get('src') if image_elem else ""

        # Описание
        desc_container = page.css_first('div.SlidingTabs__content-description')
        desc_elem = desc_container.css_first('div.SlidingTabs__descriptioncontent div.HtmlContent') if desc_container else None
        if desc_elem:
            description = "".join([p.text.strip() for p in desc_elem.find_all('p')])
        else:
            description = ""

        return {
            "page_url": url,
            "image_url": image_url,
            "tvshow_title": title,
            "description": description
        }
    except Exception as e:
        print(f"Ошибка при парсинге {url}: {e}")
        return None

def main():
    all_data = []

    with FetcherSession(impersonate='chrome') as session:
        for page_num in range(1, TOTAL_PAGES + 1):
            page_url = f"{BASE_URL}?page={page_num}"
            print(f"Парсим страницу каталога: {page_url}")
            page = session.get(page_url, stealthy_headers=True)

            # все ссылки на сериалы на странице
            cards = page.css('div.ShowsCatalog__tiles > a')
            print(f"Найдено сериалов: {len(cards)} на странице {page_num}")

            for card in cards:
                tvshow_url = card.attrib.get('href')
                if tvshow_url.startswith('/'):
                    tvshow_url = 'https://myshows.me' + tvshow_url
                print(f"Парсим сериал: {tvshow_url}")
                data = parse_tvshow(session, tvshow_url)
                if data:
                    all_data.append(data)

    # сохраняем в CSV с нужным порядком колонок
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["page_url", "image_url", "tvshow_title", "description"])
        writer.writeheader()
        writer.writerows(all_data)

    print(f"Готово! Данные сохранены в {OUTPUT_FILE}")

if __name__ == "__main__":
    main()