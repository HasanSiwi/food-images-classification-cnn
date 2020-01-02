import os
import time
import datetime as dt
from datetime import datetime
from multiprocessing import Pool

from time import sleep, time
from random import randint, choice
import requests
import urllib.request
from bs4 import BeautifulSoup
import csv
import sys

# OS
NOW           = dt.datetime.now()
FILE_NAME     = 'chefkoch_rezepte_' + NOW.strftime('%d-%m-%Y') + '.csv'
DATASET_FOLDER = 'input/csv_files/'
IMGS_FOLDER  = 'input/images/search_thumbnails/'

# Chefkoch.de Seite
CHEFKOCH_URL  = 'http://www.chefkoch.de'
START_URL     = 'http://www.chefkoch.de/rs/s'
CATEGORY      = '/Rezepte.html'

desktop_agents = ['Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
                 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
                 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
                 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_1) AppleWebKit/602.2.14 (KHTML, like Gecko) Version/10.0.1 Safari/602.2.14',
                 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36',
                 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.98 Safari/537.36',
                 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.98 Safari/537.36',
                 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36',
                 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
                 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:50.0) Gecko/20100101 Firefox/50.0']

def random_headers():
    return {'User-Agent': choice(desktop_agents),'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}


category_url = START_URL + '0o3' + CATEGORY

def _get_html(url):
    page = ''
    while page == '':
        try:
            page = requests.get(url, headers=random_headers())
        except:
            print('Connection refused')
            time.sleep(10)
            continue
    return page.text

def _get_total_pages(html):
    return int(11370)

html_text_total_pages = _get_html(category_url)
total_pages = _get_total_pages(html_text_total_pages)
print('Total pages: ', total_pages)

url_list = []

for i in range(0, total_pages + 1):
    url_to_scrap = START_URL + str(i * 30) + 'o3' + CATEGORY
    url_list.append(url_to_scrap)


from pprint import pprint
pprint(url_list[:30])


def _write_to_recipes(data):
    path = DATASET_FOLDER + FILE_NAME
    print("in writing")
    with open(path, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow((data['recipe_id'],
                        data['recipe_name'],
                        data['average_rating'],
                        data['stars_shown'],
                        data['votes'],
                        data['difficulty'],
                        data['preparation_time'],
                        data['date'],
                        data['link'],
                        data['has_picture']))
# TODO:: delete this method
def _get_picture_link(item):
    item_class = item.find('picture').find('img').get('class')
    if item_class == ['lazyload']:
        img_link = item.find('picture').find('img').get('data-srcset')
    else:
        img_link = item.find('picture').find('source').get('srcset')
    return(img_link)

def _get_front_page(html):
    counter = 0
    soup = BeautifulSoup(html, 'lxml')
    lis = soup.find_all('article')
    for element in lis:
        # get receipt ID
        a = element.find('a')
        img = a.find_all('amp-img')[0]

        try:
            id_r = a.get('data-vars-recipe-id')
        except:
            id_r = 'error in getting the id'

        # get image
        try:
            if img is not None:
                img_link = img.get('srcset').split(',')[-1].split(' ')[-2]
                img_name = IMGS_FOLDER + str(id_r) + '.jpg'
                urllib.request.urlretrieve(img_link, img_name)
                has_pic = 'yes'
            else:
                has_pic = 'no'
        except:
            has_pic = 'error in getting the image'

        # link
        try:
            link = CHEFKOCH_URL + element.find('a').get('href')
        except:
            link = 'error in getting the link'

        # name des rezeptes
        try:
            name = element.find('h2', class_='ds-heading-link').text.strip()
        except:
            name = 'error in getting the name'

        # durchschnitts bewertung von nutzern
        try:
            stars = element.find('div', class_='ds-rating-stars').get('title')
        except:
            stars = 'error in getting the stars'

        # anzahl sterne
        try:
            i_tags = element.find_all('i', class_='material-icons')
            stars_shown = 0
            for i in i_tags:
                for j in i:
                    if(j == ""):
                        stars_shown += 1
                    elif(j == ""):
                        stars_shown += 0.5
        except:
            stars_shown = 'error in stars shown'
        
        # anzahl votes
        try:
            votes = element.find('div', class_='ds-rating-count').text.strip().replace('\n','')
        except:
            votes = 'error in getting the votes'

        # schwierigkeitsgrad des rezeptes => simpel, normal oder pfiffig
        try:
            difficulty = element.find('span', class_='recipe-difficulty').text.strip().split(' ')[-1]
        except:
            difficulty = 'error in getting difficulty'

        # zubereitungs zeit
        try:
            preptime = element.find('span', class_='recipe-preptime').text.strip()
            preptime = ' '.join(preptime.split(' ')[-2:])
        except:
            preptime = 'error in getting the preptime'

        # datum
        try:
            date = element.find('span', class_='recipe-date').text.strip().split(' ')[-1]
        except:
            date = 'error in getting the date'

        # write dictionary
        data = {'recipe_id' : id_r,
                'recipe_name' : name,
                'average_rating': stars,
                'stars_shown' : stars_shown,
                'votes' : votes,
                'difficulty' : difficulty,
                'preparation_time' : preptime,
                'has_picture' : has_pic,
                'date' : date,
                'link' : link}

        # append file
        print(data)
        _write_to_recipes(data)
        if(counter>=5):
            sys.exit()
        counter += 1



def scrap_main(url):
    print('Current url: ', url)
    html = _get_html(url)
    _get_front_page(html)
    sleep(randint(1, 2))

start_time = time()
with Pool(1) as p:
    p.map(scrap_main, url_list[len(url_list)-2:])
print("--- %s seconds ---" % (time() - start_time))

import pandas as pd
chef_rezepte = pd.read_csv(DATASET_FOLDER + FILE_NAME, header=None)
chef_rezepte.head()