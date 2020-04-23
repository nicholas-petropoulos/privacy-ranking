import json
from urllib.parse import urlparse

from browsermobproxy import Server
from bs4 import BeautifulSoup
from selenium import webdriver

# Purpose of this script: List all resources (URLs) that
# Chrome downloads when visiting some page.

full_url = "https://msn.com"
# used to filter out false positive external sites with subdomains
domain = full_url[8:]
chromedriver_location = "" # Path containing the chromedriver
browsermobproxy_location = "J:\\iCloud Drive\\Development\\Python\\browsermob-proxy-2.1.4\\bin\\browsermob-proxy.bat" # location of the browsermob-proxy binary file (that starts a server)
chrome_location = "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
###############

# Start browsermob proxy
server = Server(browsermobproxy_location)
server.start()
proxy = server.create_proxy()

# Setup Chrome webdriver - note: does not seem to work with headless On
options = webdriver.ChromeOptions()
options.binary_location = chrome_location

# Setup proxy to point to our browsermob so that it can track requests
options.add_argument('--proxy-server=%s' % proxy.proxy)
options.add_argument('--ignore-certificate-errors')
options.add_argument('--ignore-ssl-errors')
driver = webdriver.Chrome(chrome_options=options)

# Now load some page
proxy.new_har("Example")
driver.get(full_url)

print(domain)

# read html page
soup = BeautifulSoup(driver.page_source, features="html.parser")
internal = []
others_https = []
others_http = []
ext_images = []
ext_videos = []
ext_js = []
redirects = []

# make sure to set ext. lower() when parsing
img_types = ['png', 'jpg', 'jpeg', 'webp', 'gif', 'svg', 'tiff', 'apng']
vid_types = ['mp4', 'webm', 'mpg', 'mpeg', 'avi', 'wmv', 'flv', 'm4v', 'mov', 'm4p', 'mpv', 'swf']
# document_types = ['html', 'htm', 'js']
for link in soup.findAll('a'):
    # possible external - check url compared to page?
    if 'https' in str(link):
        # if the href has no http/https, then it is internal
        if link.get('href') is not None and ('https' not in link.get('href') or domain in link.get('href')):
            internal.append(link.get('href'))
        elif link.get('href') is not None:
            others_https.append(link.get('href'))
        elif link.get('img') is not None:
            # TODO: get images
            pass
    # internal link - without http or https
    elif link.get('href') is not None and ('http' not in str(link) or 'https' not in str(link)):
        internal.append(link.get('href'))
    # HTTP (non-SSL link)
    elif link.get('href') is not None:
        others_http.append(link.get('href'))

# Load tracker and ad lists
with open('lists/trackers.json') as f:
    tracker_list = str(json.load(f))

ad_list = []
# read ads_trackers.txt - add to array, strip newline
with open('lists/ads_trackers.txt') as f:
    ad_list_file = f.readlines()
for line in ad_list_file:
    ad_list.append(line.strip())

# Print all URLs/resources that were requested - external
# links_file = open(f'sites\{domain}.txt', 'w')
entries = proxy.har['log']["entries"]
for entry in entries:
    if 'request' in entry.keys():
        full_url = entry['request']['url']
        base_url = urlparse(full_url).netloc
        # combined url
        new_url = None
        try:
            new_url = base_url.split('.')[1] + '.' + base_url.split('.')[2]
        except IndexError:
            pass
        # check for image extensions
        if any(ext in full_url for ext in img_types):
            pass
        elif any(ext in full_url for ext in vid_types):
            pass
        elif 'js' in full_url:
            pass
        # ads?
        # (base_url.split('.')[1] in tracker_list)
        elif new_url is not None and new_url in ad_list:
            # print(f'match: {base_url}')
            # print(f'NEW URL: {new_url}')
            pass
        # print(entry['request']['url'])
        # links_file.write(f"\n{entry['request']['url']}")



# print('Num Internal Links: ' + str(len(internal)))
# for link in internal:
#     pass
#     #print(link)
#
# print('Num External https: ' + str(len(others_https)))
# for link in others_https:
#     print(link)
#
# print('Num External http: ' + str(len(others_http)))
# for link in others_http:
#     print(link)

# TODO: save to CSV for each site
# TODO: site, num_internal, num_external, num_http, num_redirects, num_ext_js, num_ext_img_vid, num_ad_sites

server.stop()
driver.quit()
