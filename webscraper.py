import os
import json
import datetime
import requests

from bs4 import BeautifulSoup
from urllib.parse import urljoin
from langchain_community.document_loaders import WebBaseLoader


def getWinmateCategoryURL(root_url):
    try:
        res = requests.get(url=root_url)
    except requests.RequestException as e:
        raise e
    
    html_page = res.content
    soup = BeautifulSoup(html_page, features='html.parser')
    anchors = soup.find_all('a', {'class': 'pageword'})
    category_urls = [urljoin(root_url, anchor.get('href')) for anchor in anchors if 'ProductCategory/Detail' in anchor.get('href')]
    return category_urls


def getWinmateProductURL(root_url, category_urls):
    all_product_urls = []
    for category_url in category_urls:
        try:
            res = requests.get(url=category_url)
        except requests.RequestException as e:
            raise e
        
        html_page = res.content
        soup = BeautifulSoup(html_page, features='html.parser')
        all_series = soup.find_all('div', {'class': 'series_more'})
        for series in all_series:
            # product_urls = [urljoin(category_url, series.find('a').get('href')) for series in series]
            anchors = series.find_all('a')
            product_urls = [urljoin(root_url, anchor.get('href')) for anchor in anchors]
            all_product_urls += product_urls

    return all_product_urls


def getWinmateProductData(root_url, product_urls):
    product_data_list = []
    for product_url in product_urls:
        try:
            res = requests.get(url=product_url)
        except requests.RequestException as e:
            raise e
        
        html_page = res.content
        soup = BeautifulSoup(html_page, features='html.parser')
        product_name = soup.find('nav', {'role': 'navigation'}).find('li', {'class': 'active'}).find('a').get_text()
        product_content = soup.find('div', {'class': 'contentcenter'}).get_text()
        gallery = soup.find('div', {'class': 'gallery-thumbs'})
        product_images = gallery.find_all('img')

        product_data = {
            'product_name': product_name,
            'product_content': product_content,
            'product_images': [{'alt': product_image.get('alt'), 'url': urljoin(root_url, product_image.get('src'))} for product_image in product_images]
        }
        
        with open(os.path.join('docs/json/winmate_product/', f'{product_name}.json'), 'w') as f: 
            json.dump(product_data, f, ensure_ascii=False, indent = 4)
            product_data_list.append(f.name)

    return product_data_list


def getGeneralWebData(url):
    try:
        res = requests.get(url=url)
    except requests.RequestException as e:
        raise e
    
    html_page = res.content
    soup = BeautifulSoup(html_page, features='html.parser')

    loader = WebBaseLoader(url)
    docs = loader.load()

    content = docs[0].page_content
    imgs = soup.find_all('img')

    data = {
        'title': soup.title.get_text(),
        'content': content,
        'images': [{'alt': img.get('alt'), 'url': urljoin(url, img.get('src'))} for img in imgs]
    }

    with open(os.path.join('docs/json/general/', f'{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}.json'), 'w') as f: 
        json.dump(data, f, ensure_ascii=False, indent = 4)

    return f.name


if __name__ == '__main__':
    # root_url = 'https://www.winmate.com.tw/'
    # category_urls = getWinmateCategoryURL(root_url)
    # product_urls = getWinmateProductURL(root_url, category_urls)
    # product_data_list = getWinmateProductData(root_url, product_urls)
    getGeneralWebData('https://www.winmate.com.tw/Solutions/AI-ready')