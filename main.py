import csv
from time import sleep
from urllib.parse import urlparse

from browsermobproxy import Server
from bs4 import BeautifulSoup
from selenium import webdriver

# Init CSV
with open('stats.csv', 'w', newline='') as f:  # num_redirects
    f.write('site,num_internal,num_external,num_http,num_ad_trackers,num_ext_js,num_ext_img_vid\n')

with open('top_sites.txt', 'r') as f:
    lines = f.readlines()

sites = []
for line in lines:
    sites.append(line.strip())

for site in sites:
    full_site_url = 'https://' + site
    full_site_url_www = 'https://www.' + site
    # used to filter out false positive external sites with subdomains
    # domain = full_url[8:]
    domain = site
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
    driver.get(full_site_url)

    print(domain)

    # read html page
    soup = BeautifulSoup(driver.page_source, features="html.parser")
    internal = []
    others_https = []
    others_http = []
    ext_img_vid = []
    ext_js = []
    ad_tracker_matches = []
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
    # with open('lists/trackers.json') as f:
    #     tracker_list = str(json.load(f))

    ad_list = []
    # read ads_trackers.txt - add to array, strip newline
    with open('lists/ads_trackers.txt') as f:
        ad_list_file = f.readlines()
    for line in ad_list_file:
        ad_list.append(line.strip())

    print('Waiting 20s for full page load to collect ads/trackers...')
    sleep(120)
    # Print all URLs/resources that were requested - external
    # links_file = open(f'sites\{domain}.txt', 'w')

    entries = proxy.har['log']["entries"]
    for entry in entries:
        if 'request' in entry.keys():
            full_test_url = entry['request']['url']
            base_url = urlparse(full_test_url).netloc
            # check for image extensions
            if any(ext in full_test_url for ext in img_types) or any(ext in full_test_url for ext in vid_types) \
                    and (full_site_url not in full_test_url) and (full_site_url_www not in full_test_url):
                ext_img_vid.append(full_test_url)
            elif 'js' in full_test_url and (full_site_url not in full_test_url) \
                    and (full_site_url_www not in full_test_url):
                ext_js.append(full_test_url)
            # ads & trackers
            elif base_url in ad_list:
                ad_tracker_matches.append(base_url)

    # remove dupes
    ad_tracker_matches = list(dict.fromkeys(ad_tracker_matches))
    print(f'AD Matches: {len(ad_tracker_matches)} - {ad_tracker_matches}')

    ext_img_vid = list(dict.fromkeys(ext_img_vid))
    print(f'Num ext. img/vid: {len(ext_img_vid)} - {ext_img_vid}')

    ext_js = list(dict.fromkeys(ext_js))
    print(f'Num ext. js: {len(ext_js)} - {ext_js}')

    print(f'Num Internal Links: {(len(internal))}')

    others_https = list(dict.fromkeys(others_https))
    print(f'Num External https: {(len(others_https))}')

    others_http = list(dict.fromkeys(others_http))
    print(f'Num External http: {(len(others_http))}')

    # TODO: save to CSV for each site
    # TODO: site,num_internal,num_external,num_http,num_ad_trackers,num_ext_js,num_ext_img_vid,num_redirects
    csv_row = [domain, len(internal), len(others_https), len(others_http), len(ad_tracker_matches), len(ext_js),
               len(ext_img_vid), len(redirects)]

    with open('stats.csv', 'a', newline='') as f:
        # Create a writer object from csv module
        # doc = csv.writer(sys.stdout, lineterminator='\n')
        csv_writer = csv.writer(f)
        # csv_writer = writer(write_obj)
        # Add contents of list as last row in the csv file
        csv_writer.writerow(csv_row)

    server.stop()
    driver.quit()
