import requests
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv
import argparse
import time


def from_persian_digits(num):
    num = num.replace('۰', '0').replace('۱', '1').replace(
        '۲', '2').replace('۳', '3').replace('۴', '4')
    num = num.replace('۵', '5').replace('۶', '6').replace(
        '۷', '7').replace('۸', '8').replace('۹', '9')
    return int(num)


def extract(HW_ID: int, PROBLEM_ID:int):
    HEADER_DATA = {'cookie': f'session_id={os.environ["QUERA_SESSION_ID"]}'}
    URL = f'https://quera.org/course/assignments/{HW_ID}/moss/{PROBLEM_ID}'
    try:
        r = requests.get(URL, headers=HEADER_DATA)
        r.raise_for_status()
    except requests.exceptions.HTTPError:
        if r.status_code == 404:
            print('HW not found!')
            return
        if r.status_code == 403:
            print('Invalid session ID!')
            return
        if r.status_code == 429:
            print('Too many requests! Sleeping for 1 minute...')
            time.sleep(60)
            return
    soup = BeautifulSoup(r.text, features='lxml')
    body = soup.find_all('tbody')[1]
    trs = body.find_all('tr')
    data = []
    for tr in trs:
        tds = tr.find_all('td')
        std_1 = tds[0].text.strip()
        std_2 = tds[3].text.strip()
        lines = from_persian_digits(tds[6].text.strip())
        data.append((std_1, std_2, lines))
    return data


if __name__ == '__main__':
    load_dotenv('../.env')
    parser = argparse.ArgumentParser(description='Quera HW downloader')
    parser.add_argument('hw_id', type=int,
                        help='HW ID (can be extracted from the url)')
    parser.add_argument('problem_id', type=int,
                        help='Problem ID (can be extracted from the url)')
    args = parser.parse_args()
    data = extract(args.hw_id, args.problem_id)
    with open(f'{args.hw_id}_{args.problem_id}.csv', 'w', encoding='utf-8') as f:
        f.write('student_1,student_2,lines\n')
        for row in data:
            f.write(f'{row[0]},{row[1]},{row[2]}\n')