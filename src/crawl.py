import os
import mechanicalsoup as ms
import redis
from elasticsearch import Elasticsearch, helpers
import requests
import sqlite3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys



connection = sqlite3.connect("linkedin_jobs.db")
cursor = connection.cursor()


def write_to_elastic(es, url, document):
    url = url.decode('utf-8')
    es.index(index='scrape', document=document)

def scrape_data(driver, id):
    print(driver.current_url)
    document = {'id': id}
    # document['company'] = browser.page.find_first(class_='job-details-jobs-unified-top-card__company-name')
    document['title'] = driver.find_elements(By.CLASS_NAME, 'top-card-layout__title')[0].text
    document['company'] = driver.find_elements(By.CLASS_NAME, 'topcard__org-name-link')[0].text
    document['location'] = driver.find_elements(By.CLASS_NAME, 'topcard__flavor')[1].text
    # document['salary'] = driver.find_elements(By.CLASS_NAME, 'salary compensation__salary')[0].text
    # print(driver.find_elements(By.CLASS_NAME, 'show-more-less-html__markup')[0].text)
    return document

def crawl(driver, r, es, url):
    print("\nDownloading url:", url)
    url = url.decode('utf-8')
    driver.get(url)

    if "original_referer" in driver.current_url:
        print("!!! LOGIN PAGE DETECTED")
        
        # email_field = driver.find_elements(By.NAME, 'email-or-phone')[0]
        # password_field = driver.find_elements(By.NAME, 'password')[0]
        # email_field.send_keys(username)
        # password_field.send_keys(password)
        # password_field.send_keys(Keys.RETURN)


    print("Parsing data") 
    if "jobs/view" in str(url):
        id = str(url).split('/')
        # print(id)
        # exit()
        document = scrape_data(driver, id)
        print("DOCUMENT", document)

    print("Pushing to elastic")
    # write_to_elastic(es, url, document)

    print("Parsing for more links")
    a_tags = driver.find_elements(By.TAG_NAME, "a")
    hrefs = [a.get_attribute("href") for a in a_tags if a.get_attribute("href")]

    linkedin_domain = "https://www.linkedin.com"
    job_links = [a if a.startswith("https://") else linkedin_domain + a for a in hrefs if "jobs/" in a]
    job_links = set(job_links)

    print(f"Found {len(job_links)} job links")
    if job_links:
        print("Pushing links onto Redis")
        r.lpush("links", *job_links)
    else:
        print("No job links found on this page")
        if url == "https://www.linkedin.com/jobs/search/?keywords=Software%20Engineer":
            print('Retrying...')
            r.lpush("links", url)


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

chrome_options = Options()
chrome_options.add_experimental_option("detach", True)

driver = webdriver.Chrome(options=chrome_options)

start_url = "https://www.linkedin.com/jobs/search/?keywords=Software%20Engineer"
# start_url = "https://www.linkedin.com/jobs/view/3978276878/?alternateChannel=search&refId=fBu82BZzzrBgqeHx5TJnhQ%3D%3D&trackingId=17OoZWzCceiVGfg7SMMLiQ%3D%3D"

r.lpush("links", start_url)

while link := r.rpop("links"):
    crawl(driver, r, es, link)