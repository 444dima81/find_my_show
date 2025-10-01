from scrapling.fetchers import DynamicSession
from urllib.parse import urljoin

BASE_URL = "https://lordserials.fan/zarubezhnye-serialy/"

with DynamicSession(headless=False, disable_resources=False, network_idle=True) as session:
    page = session.fetch(BASE_URL, load_dom=True)

    # проверяем, есть ли карточки
    links = page.css("#dle-content a::attr(href)")
    links = [urljoin(BASE_URL, l) for l in links if "/zarubezhnye-serialy/" in l]

    print("Нашёл:", len(links))
    for l in links[:10]:
        print(l)