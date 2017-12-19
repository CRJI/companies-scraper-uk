import json
import os
import pathlib
import time
import zipfile

import bs4
import flatten_dict
import requests


DOWNLOAD_PATH = pathlib.Path() / 'downloads'
# DOWNLOAD_URL = 'http://download.companieshouse.gov.uk/persons-with-significant-control-snapshot-2017-12-14.zip'
DOWNLOAD_URL = 'http://download.companieshouse.gov.uk/en_pscdata.html'

OUTPUT_PATH = pathlib.Path() / 'outputs'
TEMPLATE = """
    <!doctype html>
    <meta charset="utf-8">
    <body>
        <h1>Companies House</h1>
"""
TEMPLATE_ROW = "<table>{content}</table>"
ITEM = "<tr><th>{key}</th><td>{value}</td></tr>"


def get_download_url():
    content = bs4.BeautifulSoup(requests.get(DOWNLOAD_URL).content,
                                'html.parser')
    base_url = DOWNLOAD_URL.rsplit('/', 1)[0]

    for link in content.findAll('a', href=True):
        if 'persons-with-significant-control' in link.text:
            return '{}/{}'.format(base_url, link.text)


def download_file():
    url = get_download_url()
    DOWNLOAD_PATH.mkdir(exist_ok=True)

    timestamp = int(time.time())
    filename, ext = os.path.splitext(url.split('/')[-1])
    file_path = DOWNLOAD_PATH / '{}_{}{}'.format(filename, timestamp, ext)

    r = requests.get(url, stream=True)
    with open(str(file_path), 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:   # filter out keep-alive new chunks
                f.write(chunk)

    return file_path


def unzip(file_path):
    zip_ref = zipfile.ZipFile(file_path, 'r')
    zip_ref.extractall(file_path.parent)
    zip_ref.close()


def latest_file():
    files = [i for i in DOWNLOAD_PATH.glob('**/*') if i.is_file()]
    return max(files, key=os.path.getctime)


def process_company(item, output_path):
    output_path.mkdir(exist_ok=True)
    data = []

    flattend = flatten_dict.flatten(item)
    temp_dict = {}

    for key, value in flattend.items():
        if isinstance(value, list):
            if not value:
                flattend.pop(key)
                continue

            if isinstance(value[0], str):
                flattend[key] = ' <br> '.join(value)
            if isinstance(value[0], dict):
                for item in value:
                    temp_dict.update(item)

    flattend.update(temp_dict)

    for key, value in flattend.items():
        if isinstance(key, tuple):
            key = key[-1]
        key = key.replace('_', ' ').title()
        data.append(ITEM.format(key=key, value=value))

    template = TEMPLATE
    template_row = TEMPLATE_ROW.format(content='\n'.join(data))

    file_path = output_path / "{}.html".format(item['company_number'])
    if not file_path.exists():
        with open(file_path, 'w') as f:
            f.write(template)

    with open(file_path, 'a') as f:
        f.write(template_row)


def process_companies_house():
    file_path = download_file()
    unzip(file_path)
    file_path.unlink()

    OUTPUT_PATH.mkdir(exist_ok=True)
    output_path = OUTPUT_PATH / file_path.stem
    output_path.mkdir(exist_ok=True)

    chunk, i = 0, 0
    with open(latest_file(), 'r') as f:
        for line in f:
            try:
                item = json.loads(line)
            except (TypeError, ValueError):
                print("Skipped line because of json error", line)

            if 'company_number' in item and item['company_number']:
                process_company(item, output_path / str(chunk))
            i += 1
            if i % 1000 == 0:
                chunk += 1
                print('.', end='', flush=True)
    print(' done')
    symlink = OUTPUT_PATH / 'latest'
    if symlink.exists():
        symlink.unlink()
    os.symlink(file_path.stem, symlink)
