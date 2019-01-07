from selenium import webdriver
import selenium.common.exceptions
import tldextract
import os
import re
try:
    import Config
except ImportError:
    from js_spider import Config
if Config.browser == 'Firefox':
    from selenium.webdriver.firefox.options import Options

def get_domain(url:str):
    try:
        domain = tldextract.extract(url)
        return domain
    except Exception as e:
        return None

result_dir = Config.save_dir # indicates where the pages captured store
target = Config.target_url # indicates the target url
domain = get_domain(target)
if domain == None:
    print('{url} is not a valid URL'.format(url=target))
    exit(2)

if not os.path.isdir(result_dir):
    os.makedirs(result_dir, 0o777, True)


def make_driver():
    if Config.browser == 'Chrome':
        options = webdriver.ChromeOptions()
        if Config.headless:
            options.add_argument('--headless')
        driver = webdriver.Chrome(chrome_options=options)
    elif Config.browser == 'Firefox':
        options = Options()
        if Config.headless:
            options.add_argument('--headless')
        driver = webdriver.Firefox(firefox_options=options)
    return driver


if Config.ignore_pattern:
    ignore_pattern = re.compile(Config.ignore_pattern)
elif not Config.ignore_pattern:
    ignore_pattern = re.compile('^\.\.\.\.\.\.')                # This is a nonsense pattern that should never occur in a URL


urls = []
urls.append(target)
index = 0
error_count = 0
error_files = []
errors = {}

driver = make_driver()

while index < len(urls):
    url = urls[index]
    print("Starting to process " + str(url))
    try:
        driver.get(url)
    except selenium.common.exceptions.WebDriverException as e:
        error_count += 1
        errors[url] = e
        driver = make_driver()
        continue
    page_source = driver.page_source
    url_base = url.replace("https://", "")
    url_base = url_base.replace("http://", "")

    file_path = result_dir + url_base
    if url == target:
        file_path = result_dir + domain.domain + ".html"
    elif file_path.endswith("/"):
        file_path = file_path[:-1] + ".html"
    elif not re.search(re.compile('\.[^/]+$'), file_path):
        file_path = file_path + ".html"
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
    except FileExistsError as e:
        error_count += 1
        errors[url] = e
        #error_files.append(file_path)
    if os.path.isfile(file_path):
        e = "File already exists: " + str(file_path)
        print(e)
        error_count += 1
        errors[url] = e
        #error_files.append(file_path)
    else:
        try:
            with open(file_path, 'w+', encoding="utf-8") as f:
                f.write(page_source)

            new_urls = 0
            links = driver.find_elements_by_tag_name('a')
            for link in links:
                href = link.get_attribute('href')
                if (type(href) == str) and (href.startswith('http')) and (not re.search(Config.ignore_pattern, href)) and (get_domain(href).domain == domain.domain) and (href not in urls):
                    urls.append(href)
                    new_urls += 1
            print("Found " + str(new_urls) + " new urls in " + str(url))
        except NotADirectoryError as e:
            error_count += 1
            errors[url] = e
            #error_files.append(file_path)
        except IsADirectoryError as e:
            error_count += 1
            errors[url] = e
            #error_files.append(file_path)

    index += 1
    pages_to_go = len(urls) - index
    print(str(index) + " pages archived")
    print(str(pages_to_go) + " pages left to process")

    file_path = False

print("Archiving complete with " + str(error_count) + " errors")
print("Errors:")
print(errors)
