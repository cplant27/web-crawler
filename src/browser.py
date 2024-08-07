from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

chrome_options = Options()
chrome_options.add_experimental_option("detach", True)

driver = webdriver.Chrome(options=chrome_options)

url = 'https://www.linkedin.com/jobs/view/3978276878/?alternateChannel=search&refId=fBu82BZzzrBgqeHx5TJnhQ%3D%3D&trackingId=17OoZWzCceiVGfg7SMMLiQ%3D%3D'
url = "https://www.linkedin.com/jobs/search/?keywords=Software%20Engineer"

driver.get(url)