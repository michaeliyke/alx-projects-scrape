import os
import base64
import time
from selenium.webdriver.chrome.webdriver import WebDriver


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
    if not exists(pdf_path):
        print(f"Saving {pdf_path}...")
        save_page_as_pdf(driver, pdf_path)
    else:
        print(f"{pdf_path} already exists.")

    html_path = path.replace(".[extension]", ".html")
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
