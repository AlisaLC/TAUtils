import requests
from bs4 import BeautifulSoup
import zipfile
import os
from tqdm import tqdm
import math
from io import BytesIO
from dotenv import load_dotenv
import argparse
import re
import time


def from_persian_digits(num):
    num = num.replace('۰', '0').replace('۱', '1').replace(
        '۲', '2').replace('۳', '3').replace('۴', '4')
    num = num.replace('۵', '5').replace('۶', '6').replace(
        '۷', '7').replace('۸', '8').replace('۹', '9')
    return int(num)


def download(HW_ID: int, root_dir: str):
    HEADER_DATA = {'cookie': f'session_id={os.environ["QUERA_SESSION_ID"]}'}
    total_pages = 100
    page_counter = 1
    while page_counter <= total_pages:
        url = f'https://quera.org/course/assignments/{HW_ID}/submissions/final?page={page_counter}'
        r = requests.get(url, headers=HEADER_DATA)
        soup = BeautifulSoup(r.text, features='lxml')
        if page_counter == 1:
            foot = soup.find('tfoot')
            if foot is not None:
                count = from_persian_digits(
                    foot.find('th').text.strip().split(' ')[0])
            else:
                count = len(soup.find('tbody').find_all('tr'))
            pbar = tqdm(total=count)
            total_pages = math.ceil(count / 20)
            os.makedirs(root_dir, exist_ok=True)
        body = soup.find('tbody')
        trs = body.find_all('tr')
        for row in trs:
            tds = row.find_all('td')
            std_id = tds[0].text.strip()
            if not std_id.isdigit():
                std_id = tds[1].text.strip()
            file_id = row['data-submission_id']
            file_url = f'https://quera.org/assignment/download_submission_file/{file_id}'
            with requests.get(file_url, headers=HEADER_DATA) as file_r:
                file_r.raise_for_status()
                try:
                    with zipfile.ZipFile(BytesIO(file_r.content)) as zip_ref:
                        zip_ref.extractall(f'{root_dir}/{std_id}')
                except zipfile.BadZipFile:
                    os.makedirs(f'{root_dir}/{std_id}', exist_ok=True)
                    file_name = re.search(
                        r'filename="(.+)"', file_r.headers['Content-Disposition']).group(1)
                    with open(f'{root_dir}/{std_id}/{file_name}', 'wb') as f:
                        f.write(file_r.content)
                time.sleep(0.5)
                pbar.update(1)
        page_counter += 1
    pbar.close()


if __name__ == '__main__':
    load_dotenv('../.env')
    parser = argparse.ArgumentParser(description='Quera HW downloader')
    parser.add_argument('hw_id', type=int,
                        help='HW ID (can be extracted from the url)')
    parser.add_argument('hw_dir', type=str, default='HW', nargs='?',
                        help='Root directory of downloaded files')
    args = parser.parse_args()
    download(args.hw_id, args.hw_dir)
