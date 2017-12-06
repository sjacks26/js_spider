from selenium import webdriver
import tldextract
import os
import datetime
try:
    import Config
except ImportError:
    from js_spider import Config

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

options = webdriver.ChromeOptions()
if Config.headless:
    options.add_argument('--headless')

driver = webdriver.Chrome(chrome_options=options)

urls = []
urls.append(target)
index = 0
errors = 0
error_files = []

while index < len(urls):
    url = urls[index]
    print("Starting to process " + str(url))
    driver.get(url)
    page_source = driver.page_source
    url_base = url.replace("https://", "")
    url_base = url_base.replace("http://", "")

    file_path = result_dir + url_base
    if url == target:
        file_path = result_dir + domain.domain + ".html"
    if file_path.endswith("/"):
        file_path = file_path[:-1] + ".html"
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
    except (FileExistsError, NotADirectoryError) as e:
        errors += 1
        error_files.append(file_path)
    if os.path.isfile(file_path):
        print("File already exists: " + str(file_path))
        errors += 1
        error_files.append(file_path)
    else:
        try:
            with open(file_path, 'w+', encoding="utf-8") as f:
                f.write(page_source)

            new_urls = 0
            links = driver.find_elements_by_tag_name('a')
            for link in links:
                href = link.get_attribute('href')
                if (href not in urls) and (get_domain(href) == domain) and ("#" not in href):
                    urls.append(href)
                    new_urls += 1
            print("Found " + str(new_urls) + " new urls in " + str(url))
        except NotADirectoryError:
            errors += 1
            error_files.append(file_path)

    index += 1
    pages_to_go = len(urls) - index
    print(str(index) + " pages archived")
    print(str(pages_to_go) + " pages left to process")

    file_path = False

print("Archiving complete with " + str(errors) + " errors")
with open(Config.error_file, 'w') as e:
    e.writelines(error_files)
print(datetime.datetime.now())
