#!/usr/bin/env python

import os
import sys
import json
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from utils import exists, sanitize, save, extract_images, extract_styles

wait_time = 7  # Time to wait for page to load

# Login credentials
email = os.getenv('email')
password = os.getenv('password')
home = 'https://intranet.alxswe.com'
projects_page = 'https://intranet.alxswe.com/projects/current'

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
wait = WebDriverWait(driver, wait_time)

# Load the offline page source if it exists else, load the url
if os.path.exists(home_page):
    with open(home_page, 'r', encoding='utf-8') as file:
        driver.get(f'file://{os.path.abspath(home_page)}')
else:
    driver.get(home)

# Wait till page is fully loaded
wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'body')))

if driver.find_elements(By.CSS_SELECTOR, 'form#new_user'):
    print('Logging in...')
    driver.find_element(By.ID, 'user_email').send_keys(email)
    driver.find_element(By.ID, 'user_password').send_keys(password)
    driver.find_element(By.ID, 'user_remember_me').click()  # Check remember me
    driver.find_element(By.NAME, 'commit').click()  # Click the login button

    # Wait for redirect to complete along with page loading
    wait.until(lambda d: d.current_url != home)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'body')))
    print("Login successful")
else:
    print('Loaded from offline page source ... DONE!')

# Save Home page as PDF
extract_styles(driver=driver)
save(driver, 'home.[extension]')

print("Navigating to projects page...")
driver.get(projects_page)
wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'body')))
print("Projects page loaded.")


# Save page source for offline use
if not exists(projects_dir):
    print(f"Creating folder {projects_dir}")
    os.makedirs(projects_dir)
else:
    print(f"Folder {projects_dir} already exists.")

# print("Saving the fully rendered page with resources...")
extract_styles(driver=driver)
save(driver, f'{projects_dir}/projects.[extension]')

print('Getting ready to extract...')
time.sleep(wait_time)

soup = BeautifulSoup(driver.page_source, 'html.parser')
groups = soup.select('.panel-group')  # Select all groups
if not groups:
    print("No groups found. Exiting...")
    driver.quit()
    exit(0)
else:
    print(f"Found {len(groups)} groups.")

print("Processing groups...")
for group in groups:
    # Get FOLDER name from .panel-heading .panel-title a
    folder_name = group.select_one(
        '.panel-heading .panel-title a').get_text(strip=True)
    print(f"Processing group...{folder_name}")

    santized_folder_name = f'{projects_dir}/{sanitize(folder_name)}'
    if not exists(santized_folder_name):
        print(f"Creating folder {santized_folder_name}")
        os.makedirs(santized_folder_name)
    else:
        print(f"Folder {santized_folder_name} already exists.")

    # Get all LINKS inside the group
    links = group.select(
        '.panel.panel-default ul.list-group li.list-group-item a')
    for link in links:
        path = f"{home}/{link['href']}"  # PATH
        description = link.get_text(strip=True)
        sanitized_description = sanitize(description)
        print(f"Processing topic...{description}: {path}")

        # Visit the link and render the page content
        driver.get(path)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'body')))
        time.sleep(wait_time//3)

        # Save the rendered HTML page within the FOLDER
        file = f"{santized_folder_name}/{sanitized_description}.[extension]"
        extract_styles(driver=driver)
        save(driver, file)
print("All groups processed.")
driver.quit()
