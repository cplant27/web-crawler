import os
import mechanicalsoup as ms
import redis
from elasticsearch import Elasticsearch, helpers
import requests
import sqlite3


connection = sqlite3.connect("linkedin_jobs.db")
cursor = connection.cursor()


def write_to_elastic(es, url, html):
    url = url.decode('utf-8') 
    es.index(index='scrape', document={ 'url': url, 'html': html })

def crawl(browser, r, es, neo, url):
    print("Downloading url:", url)
    browser.open(url)
    print(browser.page)

    print("Parsing data")
    #parse data

    print("Pushing to elastic")
    write_to_elastic(es, url, str(browser.page))

    print("Parsing for more links")
    a_tags = browser.page.find_all("a")
    hrefs = [a.get("href") for a in a_tags if a.get("href")]

    linkedin_domain = "https://www.linkedin.com"
    job_links = [a if a.startswith("https://") else linkedin_domain + a for a in hrefs if "jobs/view" in a]

    print(f"Found {len(job_links)} job links")
    if job_links:
        print("Pushing links onto Redis")
        r.lpush("links", *job_links)
    else:
        print("No job links found on this page")

### MAIN ###

neo = None

username = 'elastic'
password = os.getenv('ELASTIC_PASSWORD')

if not password:
    raise ValueError("ELASTIC_PASSWORD environment variable is not set.")

es = Elasticsearch(
    "http://localhost:9200",
    basic_auth=(username, password)
)

r = redis.Redis()
r.flushall()

browser = ms.StatefulBrowser()

start_url = "https://www.linkedin.com/jobs/search/?keywords=Software%20Engineer"
r.lpush("links", start_url)

while link := r.rpop("links"):
    crawl(browser, r, es, neo, link)

if neo:
    neo.close()
