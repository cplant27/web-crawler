import os
import mechanicalsoup as ms
import redis
from elasticsearch import Elasticsearch, helpers
import requests
import sqlite3
from selenium import webdriver
from selenium.webdriver.common.by import By


connection = sqlite3.connect("linkedin_jobs.db")
cursor = connection.cursor()


def write_to_elastic(es, url, document):
    url = url.decode('utf-8')
    es.index(index='scrape', document=document)

def scrape_data(browser, id):
    document = {'id': id}
    divs = browser.page
    print(divs)
    for div in divs:
        print(div.get_attribute("class"))
    # document['company'] = browser.page.find_first(class_='job-details-jobs-unified-top-card__company-name')
    # document['job_title'] = browser.page.find_first(class_='job-details-jobs-unified-top-card__job-title')
    exit()
    return document

def crawl(browser, r, es, url):
    print("\nDownloading url:", url)
    browser.open(url)
    # print(browser.page)

    print("Parsing data") 
    if "jobs/view" in str(url):
        id = str(url).split('/')
        # print(id)
        # exit()
        document = scrape_data(browser, id)
        print("DOCUMENT", document)

    print("Pushing to elastic")
    # write_to_elastic(es, url, document)

    print("Parsing for more links")
    a_tags = browser.page.find_all("a")
    hrefs = [a.get("href") for a in a_tags if a.get("href")]

    linkedin_domain = "https://www.linkedin.com"
    job_links = [a if a.startswith("https://") else linkedin_domain + a for a in hrefs if "jobs/" in a]
    job_links = set(job_links)

    print(f"Found {len(job_links)} job links")
    if job_links:
        print("Pushing links onto Redis")
        r.lpush("links", *job_links)
    else:
        print("No job links found on this page")
    
    #add retry if no links found to avoid bipolar problem

### MAIN ###

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

url = "https://www.linkedin.com/jobs/view/3978276878/?alternateChannel=search&refId=fBu82BZzzrBgqeHx5TJnhQ%3D%3D&trackingId=17OoZWzCceiVGfg7SMMLiQ%3D%3D"
browser.open(url)
scrape_data(browser,url)
exit()

r.lpush("links", start_url)

while link := r.rpop("links"):
    crawl(browser, r, es, link)

