#! /usr/bin/python3.6

import os
import re
import requests
import lxml.html
from bs4 import BeautifulSoup
from selectolax.parser import HTMLParser
from urllib.parse import urlparse


# Boolean Utilities
def contains(object, entry):
    return entry in object


def is_file(res):
    return os.path.isfile(res)


def exists(res):
    return os.path.exists(res)


def in_file(filename, string, isblob=False):
    if isblob:
        blob = filename
    else:
        blob = fetch_other(filename)
    return string in blob.split("\n") or string in blob

# Scraping and Crawling utilities


def get_cache(cache_url="urlcache.txt"):
    if exists(cache_url):
        return fetch_other(cache_url)
    else:
        return "Specified cache file does not exists!"


def url_cached(url, cache_url="urlcache.txt"):
    """Say yes if cached otherwise, it says no and caches it"""
    if not exists(cache_url):
        create_file(
            cache_url, "This File is for URL cache - DO NOT MODIFY DIRECTLY!")
    if not in_file(cache_url, url):
        write_to_file(cache_url, url)
        print("Cache not found - - created successfully!")
        return False
    print("Cache exists - - {0}".format(os.path.realpath("urlcache.txt")))
    return True


def write_to_file(filename, content, newline="\n"):
    with open(filename, "a", encoding="UTF-8", newline="\n") as file:
        file.write(content)
    return True


def create_file(filename, content, newline="\n"):
    with open(filename, "w+", encoding="UTF-8", newline=newline) as f:
        f.write(content)

    return True


def save_on_disk(filename, content):
    return create_file(filename, content)


def array_to_string(arraylist):
    return "\n".join(arraylist).strip()


def beautiful(url, condition=None):
    return beautify(fetching(url)) if not condition else beautify(fetching(url, condition))


def beautify(txt):
    return BeautifulSoup(txt, "lxml")


def html_parse(url, condition):
    return parse(fetching(url)) if not condition else parse(fetching(url, condition))


def parse(txt):
    return HTMLParser(txt)


def fetch_other(url):
    return open(url, "rt", encoding="UTF-8").read()


def fetching(url, condition=None):
    """
    @param: url - web address to scrape
    @param: condition - a function that makes a bit of decision about desired data
    @returns: text
    """
    page = requests.get(url)
    return condition(page.text) if condition else page.text


def fetch_local(file_path: str):
    with open(file_path, "r") as file:
        return file.read()


def fetch__safe(url):
    url = urlparse(url)
    path = url.path.split("/")
    if not url.hostname:
        return ""
    name = str(re.sub(r"www.|\.\w+", "", url.hostname))
    if path:
        name += "_" + \
            path[len(path) - 1] if bool(path[len(path) - 1]
                                        ) else "_" + path[len(path) - 2]

    if exists(name + ".html") and is_file(name + ".html"):
        print("Cache found  - -  retreiving offline")
        return fetch_other(name + ".html")
    print("Not available - - going online")
    html = fetching(url.geturl())
    create_file(name + ".html", html)
    return html


def fetch_links(url):
    links = []
    html = BeautifulSoup(fetching(url), "lxml")
    anchor_tags = html.find_all("a", href=True)
    for tag in anchor_tags:
        links.append(tag["href"])
    return array_to_string(links)


def traverse():
    pass


def list_folder_content():
    pass


def list_resource():
    """List files, folders, file-type, etc, with ease"""
    pass


def delete_resource():
    pass


__all__ = [
    "create_file", "fetching", "array_to_string", "beautiful", "html_parse", "fetch_links",
    "beautify", "parse", "fetch_other", "exists", "in_file", "url_cached", "write_to_file",
    "save_on_disk", "fetch__safe", "get_cache", "traverse", "list_folder_content", "list_resource",
    "delete_resource",
    "contains"
]
