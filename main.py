import requests
from bs4 import BeautifulSoup

# --- Privacy Score ---
# num# of external urls
# redirections
# http urls
# external urls dling js or html vs image or video


# file = open('top_sites.txt', 'r')
# lines = file.readlines()
# for site in lines:
url = 'https://yahoo.com'
domain = url[8:]
print(domain)
html_page = requests.get(url)
print('Headers: ' + str(requests.get(url).headers))
# read html page
soup = BeautifulSoup(html_page.text, features="html.parser")
internal = []
others_https = []
others_http = []

img_types = ['png', 'jpg', 'jpeg', 'JPEG', 'webp']
document_types = ['html', 'htm', 'js']

for link in soup.findAll('a'):
    # possible external - check url compared to page?
    if 'https' in str(link):
        # if the href has no http/https, then it is internal
        if link.get('href') is not None and ('https' not in link.get('href') or domain in link.get('href')):
            internal.append(link.get('href'))
        elif link.get('href') is not None:
            others_https.append(link.get('href'))
    # internal link - without http or https
    elif link.get('href') is not None and ('http' not in str(link) or 'https' not in str(link)):
        internal.append(link.get('href'))
    # HTTP (non-SSL link)
    elif link.get('href') is not None:
        others_http.append(link.get('href'))
    # TODO: save to CSV for each?

print('Num Internal Links: ' + str(len(internal)))
for link in internal:
    print(link)

print('Num External https: ' + str(len(others_https)))
for link in others_https:
    print(link)

print('Num External http: ' + str(len(others_http)))
for link in others_http:
    print(link)
