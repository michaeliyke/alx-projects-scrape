#!/usr/bin/env python

import os
import sys
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from utils import (clean_up, exists, save,
                   scrape_projects, switch_curriculums, update_links)


# Login credentials
email = os.getenv('email')
password = os.getenv('password')
home = 'https://intranet.alxswe.com'

# The offline page source to manipulate
home_page = 'index.html'
projects_dir = 'projects'

if not email or not password:
    usage = f'Usage: email=your_email password=your_password python {
        sys.argv[0]}'
    print(usage)
    exit(1)

chrome_options = Options()
chrome_options.add_argument('--incognito')
chrome_options.add_argument('--headless')
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)
wait = WebDriverWait(driver, 7)

# Load the offline page source if it exists else, load the url
if os.path.exists(home_page):
    with open(home_page, 'r', encoding='utf-8') as file:
        driver.get(f'file://{os.path.abspath(home_page)}')
else:
    driver.get(home)

# Wait till page is fully loaded
wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'body')))

if driver.find_elements(By.CSS_SELECTOR, 'form#new_user'):  # Am I to login?
    print('Logging in...')
    save(driver, 'login.[extension]')  # Save the login page
    update_links((driver.current_url, 'Intranet Login Screen'))

    driver.find_element(By.ID, 'user_email').send_keys(email)
    driver.find_element(By.ID, 'user_password').send_keys(password)
    driver.find_element(By.ID, 'user_remember_me').click()  # Check remember me
    driver.find_element(By.NAME, 'commit').click()  # Click the login button

    # Wait for redirect to complete, wait for full page loading
    wait.until(lambda d: d.current_url != home)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'body')))
    print("Login successful: redirecting to intranet home page...")
else:
    print('Loaded from offline page source ... DONE!')

# Save intranet home page
save(driver, 'home.[extension]')
update_links((driver.current_url, 'Intranet Home Page'))

print("Navigating to projects page...")
driver.get('https://intranet.alxswe.com/projects/current')
wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'body')))
print("Projects page loaded.")


# Create the base projects directory
if not exists(projects_dir):
    print(f"Creating folder {projects_dir}")
    os.makedirs(projects_dir)
else:
    print(f"Folder {projects_dir} already exists.")

# Save the default project page
save(driver, f'{projects_dir}/projects.[extension]')
update_links((driver.current_url, 'Default Projects Page'))

print('Getting ready to extract...')
time.sleep(4)

update_links(("Short Specializations", "#"))
scrape_projects(driver, wait, "projects/specializations", home)

print("Switching curriculums...")
switch_curriculums(driver, wait)

update_links(("#", "SE Foundations"))
scrape_projects(driver, wait, "projects/foundations", home)

clean_up()

print("All projects processed.")
driver.quit()
