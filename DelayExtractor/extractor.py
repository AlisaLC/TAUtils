import requests
from bs4 import BeautifulSoup
import os
from tqdm import tqdm
import math
from dotenv import load_dotenv
import argparse
import re
import time
import datetime
import jdatetime

def from_persian_digits(num):
    num = num.replace('۰', '0').replace('۱', '1').replace(
        '۲', '2').replace('۳', '3').replace('۴', '4')
    num = num.replace('۵', '5').replace('۶', '6').replace(
        '۷', '7').replace('۸', '8').replace('۹', '9')
    return int(num)

def extract_deadline(HW_ID):
    HEADER_DATA = {'cookie': f'session_id={os.environ["QUERA_SESSION_ID"]}'}
    url = f'https://quera.org/course/assignments/{HW_ID}/edit'
    try:
        r = requests.get(url, headers=HEADER_DATA)
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
    finish_time = soup.find('input', {'id': 'id_finish_time'})['value']
    finish_time = datetime.datetime.strptime(finish_time, '%Y/%m/%d %H:%M:%S')
    finish_time = jdatetime.datetime.fromgregorian(datetime=finish_time)
    return finish_time

def extract_delays(HW_ID, HW_DEADLINE):
    problems = set()
    delays = dict()
    HEADER_DATA = {'cookie': f'session_id={os.environ["QUERA_SESSION_ID"]}'}
    total_pages = 100
    page_counter = 1
    while page_counter <= total_pages:
        url = f'https://quera.org/course/assignments/{HW_ID}/submissions/final?page={page_counter}'
        try:
            r = requests.get(url, headers=HEADER_DATA)
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
                continue
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
        body = soup.find('tbody')
        trs = body.find_all('tr')
        for row in trs:
            tds = row.find_all('td')
            std_id = tds[0].text.strip()
            if not std_id.isdigit():
                std_id = tds[1].text.strip()
            if std_id not in delays:
                delays[std_id] = dict()
            problem_id = tds[2]
            problem_id = problem_id.find('a')['href'].split('/')[-1]
            problem_id = int(problem_id)
            problems.add(problem_id)
            submit_time = tds[3].text.strip().split(' ')
            submit_day = from_persian_digits(submit_time[0])
            submit_month = submit_time[1]
            submit_month = ['فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور', 'مهر', 'آبان','آذر','دی','بهمن','اسفند'].index(submit_month) + 1
            submit_year = from_persian_digits(submit_time[2])
            submit_time = submit_time[5]
            submit_time = submit_time.split(':')
            submit_hour = from_persian_digits(submit_time[0])
            submit_minute = from_persian_digits(submit_time[1])
            submit_datetime = jdatetime.datetime(submit_year, submit_month, submit_day, submit_hour, submit_minute)
            if submit_datetime > HW_DEADLINE:
                delays[std_id][problem_id] = submit_datetime - HW_DEADLINE
                delays[std_id][problem_id] = delays[std_id][problem_id].days * 24 * 60 + delays[std_id][problem_id].seconds // 60
            pbar.update(1)
        time.sleep(1)
        page_counter += 1
    pbar.close()
    return delays, problems

if __name__ == '__main__':
    load_dotenv('../.env')
    parser = argparse.ArgumentParser(description='Quera HW downloader')
    parser.add_argument('hw_id', type=int,
                        help='HW ID (can be extracted from the url)')
    args = parser.parse_args()
    HW_DEADLINE = extract_deadline(args.hw_id)
    print(HW_DEADLINE)
    delays, problems = extract_delays(args.hw_id, HW_DEADLINE)
    print(problems)
    print(delays)
    with open(f'{args.hw_id}.csv', 'w') as f:
        f.write('std_id,')
        for problem in problems:
            f.write(f'problem_{problem},')
        f.write('\n')
        for std_id in delays:
            f.write(f'{std_id},')
            for problem in problems:
                if problem in delays[std_id]:
                    f.write(f'{delays[std_id][problem]},')
                else:
                    f.write('0,')
            f.write('\n')