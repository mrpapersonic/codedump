# example args.url: https://kemono.party/fanbox/user/5375435/post/2511461
# created by Paper in 2021
# please do not share without crediting me!
import argparse
import http.cookiejar
import os
import re
import requests  # pip install requests
import time
import math
import zipfile
import urllib.parse
from urllib.error import HTTPError
from http.client import BadStatusLine


def download_folder_from_google_drive(link):
    session = requests.Session()
    session.headers = {
        'origin': 'https://drive.google.com',
        'content-type': 'application/json',
    }
    key = "AIzaSyC1qbk75NzWBvSaDh6KnsjjA9pIrP4lYIE"  # google anonymous key
    takeoutjs = session.post(f"https://takeout-pa.clients6.google.com/v1/exports?key={key}", data='{{"items":[{{"id":"{0}"}}]}}'.format(link.split("?")[0].split("/")[-1])).json()
    takeoutid = takeoutjs["exportJob"]["id"]
    storagePath = None
    while storagePath is None:
        succeededjson = session.get("https://takeout-pa.clients6.google.com/v1/exports/{0}?key={1}".format(takeoutid, key)).json()
        if succeededjson["exportJob"]["status"] == "SUCCEEDED":
            storagePath = succeededjson["exportJob"]["archives"][0]["storagePath"]
        time.sleep(1)
    size = 0
    for path, dirs, files in os.walk("./{0}/Drive - {1}".format(output, sanitize(i["title"]))):
        for f in files:
            fp = os.path.join(path, f)
            size += os.path.getsize(fp)
    if size >= int(succeededjson["exportJob"]["archives"][0]["sizeOfContents"]):
        print("  {0} already downloaded!".format(succeededjson["exportJob"]["archives"][0]["fileName"]))
        return
    response = session.get(storagePath, stream=True)
    amountdone = 0
    with open(succeededjson["exportJob"]["archives"][0]["fileName"], "wb") as f:
        for chunk in response.iter_content(1024):
            if chunk:  # filter out keep-alive new chunks
                f.write(chunk)
                amountdone += 1024
                print("  downloading {0}: ".format(succeededjson["exportJob"]["archives"][0]["fileName"]) + " " + str(round((amountdone / int(succeededjson['exportJob']['archives'][0]['compressedSize'])) * 100, 2)) + "%\r", end="")
        print("  downloaded  {0}".format(succeededjson["exportJob"]["archives"][0]["fileName"]) + ": 100.00%    ")
    unzip(succeededjson["exportJob"]["archives"][0]["fileName"], "./{0}/Drive - {1}".format(output, sanitize(i["title"])))


def unzip(src_path, dst_dir, pwd=None):
    with zipfile.ZipFile(src_path) as zf:
        members = zf.namelist()
        for member in members:
            arch_info = zf.getinfo(member)
            arch_name = arch_info.filename.replace('/', os.path.sep)
            dst_path = os.path.join(dst_dir, arch_name)
            dst_path = os.path.normpath(dst_path)
            if not os.path.exists(dst_path):
                zf.extract(arch_info, dst_dir, pwd)


def download_from_dropbox(link):
    responsehead = req.head(link.split("?")[0] + "?dl=1", allow_redirects=True)
    if responsehead.status_code == 404:
        print("  dropbox link not available!")
        return
    if not os.path.exists(output + "/Dropbox - " + sanitize(i["title"])):
        os.makedirs(output + "/Dropbox - " + sanitize(i["title"]))
    filename = output + "/Dropbox - " + sanitize(i["title"]) + "/" + sanitize(responsehead.headers["Content-Disposition"].split("'")[-1])
    if os.path.exists(urllib.parse.unquote(os.path.splitext(filename)[0])) and os.path.isdir(urllib.parse.unquote(os.path.splitext(filename)[0])):
        print("  file(s) already downloaded!")
        return
    if os.path.exists(filename):
        filesize = os.stat(filename).st_size
    else:
        filesize = 0
    serverfilesize = int(responsehead.headers["Content-Length"])
    if filesize < serverfilesize:
        with req.get(link.split("?")[0] + "?dl=1", stream=True, headers={"Range": f"bytes={filesize}-"}) as r:
            r.raise_for_status()
            with open(filename, "ab") as f:
                for chunk in r.iter_content(chunk_size=4096):
                    f.write(chunk)
                    filesize += 4096
                    print("  file {0} downloading: ".format(urllib.parse.unquote(responsehead.headers["Content-Disposition"].split("'")[-1])) + str(round((filesize / serverfilesize) * 100)) + "%\r", end="")
                print("  {0} successfully downloaded!".format(urllib.parse.unquote(responsehead.headers["Content-Disposition"].split("'")[-1])))
    if responsehead.headers["Content-Disposition"].split("'")[-1].endswith(".zip"):
        unzip(filename, urllib.parse.unquote(os.path.splitext(filename)[0]))
        os.remove(filename)


def download_file_from_google_drive(id, dir=""):  # https://stackoverflow.com/questions/25010369/wget-curl-large-file-from-google-drive/39225039
    def get_confirm_token(response):
        for key, value in response.cookies.items():
            if key.startswith('download_warning'):
                return value

        return None

    def save_response_content(response):
        amountdone = 0
        CHUNK_SIZE = 4096
        if not os.path.exists(output + "/Drive - " + sanitize(i["title"]) + "/" + dir):
            os.makedirs(output + "/Drive - " + sanitize(i["title"]) + "/" + dir)
        destination = output + "/Drive - " + sanitize(i["title"]) + "/" + dir + "/" + sanitize(response.headers["Content-Disposition"].split("'")[-1])
        if os.path.exists(destination):
            filesize = os.stat(destination).st_size
        else:
            filesize = 0

        if os.path.exists(destination) and filesize == int(response.headers["Content-Range"].partition('/')[-1]):
            print("  " + os.path.basename(destination) + " already downloaded!")
            return

        with open(destination, "wb") as f:
            for chunk in response.iter_content(CHUNK_SIZE):
                if chunk:  # filter out keep-alive new chunks
                    f.write(chunk)
                    amountdone += CHUNK_SIZE
                    print("  downloading {0}: ".format(os.path.basename(destination)) + " " + str(round((amountdone / int(response.headers["Content-Range"].partition('/')[-1])) * 100, 2)) + "%\r", end="")
            print("  downloaded  {0}".format(os.path.basename(destination)) + ": 100.00%    ")

    URL = "https://docs.google.com/uc?export=download"

    session = requests.Session()

    headers = {
        "Range": "bytes=0-",
    }

    session.proxies = req.proxies

    response = session.get(URL, headers=headers, params={'id': id}, stream=True)

    while response.status_code == 403:
        time.sleep(30)
        response = session.get(URL, headers=headers, params={'id': id}, stream=True)

    if response.status_code == 404:
        return  # bypass when root folder has no files

    token = get_confirm_token(response)

    if token:
        params = {'id': id, 'confirm': token}
        response = session.get(URL, headers=headers, params=params, stream=True)

    save_response_content(response)


def sanitize(filename):
    return re.sub(r"[\/:*?\"<>|]", "_", filename).strip()


def find_urls(s):
    urllist = []
    for findall in re.findall(r"""http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+""", s):
        urllist.append(findall.split("<")[0].split(">")[-1])
    return urllist


def downloadfile(i, x, count):
    filename = "{4}/{0}_{1}p_{2}_{3}".format(i["id"], count, sanitize(i["title"]), os.path.basename(x["path"]), output)
    amountdone = 0
    if os.path.exists(filename):
        filesize = os.stat(filename).st_size
    else:
        filesize = 0
    serverhead = req.head("https://data.kemono.party" + x['path'])
    for i in range(500):
        serverfilesize = int(serverhead.headers["Content-Length"])
        if filesize < serverfilesize:
            with req.get(f"https://data.kemono.party{x['path']}", stream=True, headers={"Range": f"bytes={filesize}-"}) as r:
                r.raise_for_status()
                with open(filename, "ab") as f:
                    for chunk in r.iter_content(chunk_size=4096):
                        f.write(chunk)
                        amountdone += len(chunk)
                        print(" downloading image " + str(count) + ": " + str(round(((filesize + amountdone) / serverfilesize) * 100, 2)) + "%\r", end="")
                    print(" downloaded image " + str(count) + ": 100.00%  ")
            return
        else:
            print(" image " + str(count) + " already downloaded!")
            return
        time.sleep(10)
    print(" download timed out!")
    return


def parse_json(i, count):
    seen = set()
    unique_urls = []
    for url in find_urls(i["content"]):
        if url.startswith("https://drive.google.com/drive/folders"):
            if url.split("/")[-1].split("?")[0] not in seen:
                unique_urls.append(url)
                seen.add(url.split("/")[-1].split("?")[0])
        elif url.startswith("https://drive.google.com/open?id="):
            if url.split("?id=")[-1] not in seen:
                unique_urls.append(req.head(url).headers["Location"])
                seen.add(url.split("/")[-1].split("?")[0])
        elif url.startswith("https://drive.google.com/file/"):
            if url.split("?")[0].split("/")[-2] not in seen:
                unique_urls.append(url)
                seen.add(url.split("?")[0].split("/")[-2])
        elif url.startswith("https://www.dropbox.com"):
            print(" Dropbox link found! attempting to download its files...")
            download_from_dropbox(url)
        else:  # TODO: add MEGA, or some sort of other file hosting website(s). gdrive and dropbox seem like the most popular ones atm
            pass
    for url in unique_urls:
        if url.startswith("https://drive.google.com/drive/folders/"):
            # Google Drive folder downloading
            print(" Google Drive link found! attempting to download its files...")
            download_folder_from_google_drive(url)
        elif url.startswith("https://drive.google.com/file/"):
            print(" Google Drive link found! attempting to download its files...")
            download_file_from_google_drive(url.split("?")[0].split("/")[-2])
    for x in i["attachments"]:
        count += 1
        while not os.path.exists("{4}/{0}_{1}p_{2}_{3}".format(int(i["id"]) - 1, count, sanitize(i["title"]), os.path.basename(x["path"]), output)):
            try:
                downloadfile(i, x, count)
                break
            except HTTPError:
                while 1:
                    time.sleep(10)
                    downloadfile(i, x, count)
            except BadStatusLine:  # DDoS-GUARD
                while 1:
                    time.sleep(10)
                    downloadfile(i, x, count)
            except Exception as e:
                print(e)
            time.sleep(10)


def get_amount_of_posts(s, u):
    amount = 0
    while 1:
        data = req.get("https://kemono.party/api/{0}/user/{1}?o={2}".format(s, u, amount)).json()
        if len(data) < 25:
            return math.ceil((amount + 1) / 25)
        amount += 25


parser = argparse.ArgumentParser(description="Downloads files from kemono.party")
parser.add_argument("-u", "--url", help="user URL", metavar='<url>', required=True)
parser.add_argument("-c", "--cookies", help="", metavar='<cookies>', required=True)  # required because of DDoS-GUARD
parser.add_argument("-p", "--proxy", help="proxy\n supported types: http, https, socks5 (requires pysocks)", metavar='<proxy>')  # SOCKS proxy support is through PySocks - pip install pysocks
parser.add_argument("-o", "--output", help="output folder, defaults to user ID", metavar='<output>')
parser.add_argument("--test-download-services", dest="testdownloadservices", action="store_true", help="test download services")
args = parser.parse_args()

req = requests.Session()

if args.proxy:
    req.proxies = {}
    if args.proxy[:6] == "socks5":
        httpproxy = args.proxy
        httpsproxy = args.proxy
    elif args.proxy[:5] == "https":
        httpsproxy = args.proxy
    elif args.proxy[:4] == "http":
        httpproxy = args.proxy
    else:
        print("unknown proxy format! defaulting to HTTP...")
        httpproxy = args.proxy
    if httpproxy:
        req.proxies["http"] = httpproxy
    if httpsproxy:
        req.proxies["https"] = httpsproxy

cj = http.cookiejar.MozillaCookieJar(args.cookies)
cj.load(ignore_expires=True)
req.cookies = cj

try:
    int(args.url)
    print("do not input user IDs in --url! use a link instead")
    exit()
except Exception:
    pass

if args.url.split("/")[-2] == "post":
    service = args.url.split("/")[-5]
    user = args.url.split("/")[-3]
    post = args.url.split("/")[-1]
elif args.url.split("/")[-2] == "user":
    service = args.url.split("/")[-3]
    user = args.url.split("/")[-1]

if not args.output:
    output = user
else:
    output = args.output

if not os.path.isdir(output):
    if os.path.exists(output):
        os.remove(output)
    os.makedirs(output)

try:
    post
    pages = 1
except Exception:
    pages = get_amount_of_posts(service, user)
for page in range(pages):
    try:
        post
        userdata = req.get("https://kemono.party/api/{0}/user/{1}/post/{2}".format(service, user, post)).json()
    except Exception:
        userdata = req.get("https://kemono.party/api/{0}/user/{1}?o={2}".format(service, user, (page * 25))).json()
    for i in userdata:
        print(i["id"])
        count = 0
        parse_json(i, count)
