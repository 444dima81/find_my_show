import csv
from urllib.parse import urljoin
from scrapling.fetchers import FetcherSession

BASE_URL = "https://lordserials.fan/zarubezhnye-serialy/"
OUTPUT_FILE = "./find_my_show/data/data.csv"
MAX_PAGE = 64


def parse_tvshow(session, url):
    """Парсим одну страницу сериала"""
    page = session.get(url, stealthy_headers=True)

    # Заголовок
    title_el = page.css_first("meta[itemprop='name']::attr(content)")
    title = title_el if title_el else ""

    # Описание
    desc_el = page.css_first("div.fdesc.clearfix.slice-this")
    description = desc_el.text.strip() if desc_el else ""

    # Постер
    img_el = page.css_first("div.fposter.img-wide img::attr(src)")
    image_url = urljoin(BASE_URL, img_el) if img_el else ""

    return {
        "page_url": url,
        "image_url": image_url,
        "tvshow_title": title,
        "description": description,
    }


def main():
    all_links = set()

    with FetcherSession(impersonate="chrome") as session:
        # обходим все страницы каталога
        for page_num in range(1, MAX_PAGE + 1):
            url = BASE_URL if page_num == 1 else f"{BASE_URL}page/{page_num}/"
            print(f"Собираю ссылки со страницы {url}")
            try:
                page = session.get(url, stealthy_headers=True)
                links = page.css("div#dle-content a::attr(href)")
                links = [urljoin(BASE_URL, l) for l in links if "/zarubezhnye-serialy/" in l and l.endswith(".html")]
                all_links.update(links)
            except Exception as e:
                print(f"Ошибка при загрузке {url}: {e}")

        print(f"Нашёл всего {len(all_links)} сериалов")

        # Парсим каждый сериал
        results = []
        for i, link in enumerate(all_links, 1):
            try:
                print(f"[{i}/{len(all_links)}] Парсим: {link}")
                data = parse_tvshow(session, link)
                results.append(data)
            except Exception as e:
                print(f"Ошибка при парсинге {link}: {e}")

        # Сохраняем в CSV
        with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["page_url", "image_url", "tvshow_title", "description"])
            writer.writeheader()
            writer.writerows(results)

        print(f"Сохранил {len(results)} сериалов в {OUTPUT_FILE}")


if __name__ == "__main__":
    main()