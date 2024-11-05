import os
import base64
import time
from typing import List, Tuple
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

links_n_decriptions: List[Tuple[str, str]] = []


def clean_up():
    """Clean up the global variables"""
    global links_n_decriptions

    # Save the links and descriptions to a html file
    with open('links.html', 'w', encoding='utf-8') as file:
        file.write('<html><head><title>Links</title></head><body>')
        for link, description in links_n_decriptions:
            file.write(f'<a href="{link}">{description}</a><br>')
        file.write('</body></html>')
    print("Links saved to links.html")

    links_n_decriptions = []


def update_links(entry: Tuple[str, str]):
    """Update the global links_n_decriptions list"""
    global links_n_decriptions
    links_n_decriptions.append(entry)


def scrape_projects(driver, wait, projects_dir: str, home: str):
    if not exists(projects_dir):
        print(f"Creating folder {projects_dir}")
        os.makedirs(projects_dir)
    else:
        print(f"Folder {projects_dir} already exists.")

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
            file = f"{
                santized_folder_name}/{sanitized_description}.[extension]"
            if not exists(file):
                driver.get(path)
                wait.until(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, 'body')))
                time.sleep(1)

                save(driver, file)
            links_n_decriptions.append((path, description))
    print("All groups processed.")


def switch_curriculums(driver: WebDriver, wait: WebDriverWait):
    """Switch between specialization to foundations"""
    sel = "#student-switch-curriculum-dropdown"
    driver.find_element(By.CSS_SELECTOR, sel).click()
    sel2 = '#student-switch-curriculum ul > li:first-child > a'
    driver.find_element(By.CSS_SELECTOR, sel2).click()
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'body')))
    driver.get('https://intranet.alxswe.com/projects/current')
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'body')))
    sel = "#student-switch-curriculum-dropdown > div:first-child > span:first-child"
    span = driver.find_element(By.CSS_SELECTOR, sel)
    return 'Foundations' in span.text


def sanitize(name):
    """Sanitize file names by removing non-alphanumeric characters, and
replacing them with underscores"""
    return ''.join(c if c.isalnum() else '_' for c in name)


def exists(path: str) -> bool:
    """Whether a file exists at the given path"""
    return os.path.exists(path)


def save_page_as_pdf(driver: WebDriver, full_path: str):
    time.sleep(2)
    if full_path:
        settings = {
            "landscape": False,
            "displayHeaderFooter": False,
            "printBackground": True,
            "preferCSSPageSize": True,
            "scale": 1,
            "preferCSSPageSize": True,
            "paperWidth": 8.27,
            "paperHeight": 11.69,
        }
        pdf_data = driver.execute_cdp_cmd("Page.printToPDF", settings)
        pdf_bytes = base64.b64decode(pdf_data["data"])
        with open(full_path, "wb") as f:
            f.write(pdf_bytes)


def save_web_page(driver: WebDriver, path: str) -> None:
    html_content = driver.execute_script(
        "return document.documentElement.outerHTML;")
    with open(path, 'w', encoding='utf-8') as file:
        file.write(html_content)


def save(driver: WebDriver, path: str):
    """Save a page both as a HTML webpage and a PDF file"""

    pdf_path = path.replace(".[extension]", ".pdf")
    html_path = path.replace(".[extension]", ".html")

    if not exists(pdf_path) or not exists(html_path):
        extract_styles(driver)
        remove_at_media_print_in_css(driver)
        fix_at_media_screen_in_css(driver)

    # if not exists(pdf_path):
    #     print(f"Saving {pdf_path}...")
    #     save_page_as_pdf(driver, pdf_path)
    # else:
    #     print(f"{pdf_path} already exists.")

    if not exists(html_path):
        print(f"Saving {html_path}...")
        save_web_page(driver, html_path)
    else:
        print(f"{html_path} already exists.")


def extract_styles(driver: WebDriver):
    """Extract styles from the head of the page and inline them into the body"""
    script = """
        const selector = 'link[rel="stylesheet"]';
        const links = document.querySelectorAll(selector);
        for (const link of links) {
            fetch(link.href)
                .then((response) => response.text())
                .then((cssText) => {
            const  style = document.createElement('style');
            style.type = 'text/css';
            style.appendChild(document.createTextNode(cssText));
            link.parentNode.replaceChild(style, link);
        })
        .catch((error) => console.error("Failed to fetch style", error));
        }
        """
    driver.execute_script(script)


def extract_images(driver: WebDriver):
    """Extract images from the page and convert them to base64"""
    script = """
        const selector = 'img';
        const images = document.querySelectorAll(selector);
        for (const img of images) {
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            canvas.width = img.width;
            canvas.height = img.height;
            ctx.drawImage(img, 0, 0);
            const dataURL = canvas.toDataURL('image/png');
            img.src = dataURL;
        }
        """
    driver.execute_script(script)


def remove_at_media_print_in_css(driver: WebDriver):
    """Fix @media screen in css to allow both screen and print media"""
    script = """
        const selector = 'style';
        const styles = document.querySelectorAll(selector);
        for (const style of styles) {
            const cssText = style.innerHTML;
            // Remove @media print for rich printing - basic
            const newCssText = cssText.replaceAll('@media print', '@media tv');
            style.innerHTML = newCssText;
        }
        """
    driver.execute_script(script)


def fix_at_media_screen_in_css(driver: WebDriver):
    """Fix @media screen in css to allow both screen and print media"""
    script = """
        const selector = 'style';
        const styles = document.querySelectorAll(selector);
        for (const style of styles) {
            const cssText = style.innerHTML;
            // Replace @media screen with @media print, screen for rich printing
            const newCssText = cssText.replaceAll(
                '@media screen', '@media print, screen');
            style.innerHTML = newCssText;
        }
        """
    driver.execute_script(script)


def list_style_rules(driver: WebDriver):
    """Fix @media screen in css to allow both screen and print media"""
    script = """
    const logs = [];
    const styleSheets = [].slice.call(document.styleSheets); // All stylesheets

    for (const stylesheet of styleSheets) { // Iterate through the stylesheets
        try {
            const cssRules = [].slice.call(stylesheet.cssRules);
            for (const rule  of cssRules) {

                //rule.media.mediaText = rule.media.mediaText.replace("print", "tv");
                if (rule.media && rule.media.mediaText.includes("print"))
                    logs.push(rule.cssText);
                //if (rule.media && rule.media.mediaText.includes("screen"))
                //rule.media.mediaText = rule.media.mediaText.replace("print", "tv");
            }
        } catch (e) {
            console.warn('Could not access stylesheet:', stylesheet.href, e);
        }
    }
    return logs;
    """
    print("Result here:", driver.execute_script(script))


def fix_at_media_TODO(driver: WebDriver):
    """Fix @media screen in css to allow both screen and print media"""
    script = """
    const styleSheets = [].slice.call(document.styleSheets); // All stylesheets
    for (const stylesheet of styleSheets) { // Iterate through the stylesheets
        try {
            const cssRules = [].slice.call(stylesheet.cssRules);
            for (const rule  of cssRules) {
                if (rule.media && rule.media.mediaText.includes("screen")) {
                    if(!rule.media.mediaText.includes("print")) {
                        rule.media.appendMedium("print");
                    }
                }
            }
        } catch (e) { // Catch any CORS-related errors
            console.warn('Could not access stylesheet:', stylesheet.href, e);
        }
    }
    """
    driver.execute_script(script)


def del_files_recursive(directory: str, extension: str, remove: bool = False):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(extension):
                file_path = os.path.join(root, file)
                if remove:
                    os.remove(file_path)
                print(f"Found: {file_path}")
