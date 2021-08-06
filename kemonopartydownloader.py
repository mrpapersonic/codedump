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


def get_google_drive_subfolder_ids(link):
    gdrive = requests.get(link).text
    drivefiles = re.findall(r"\[\"(.{33}?)\",\[\"(.{33}?)\"\],\"(.+?)\",\"(.+?)\"", gdrive)  # format: ["id","name","mimetype"
    seen = set()
    unique_ids = []
    names = []
    for files in drivefiles:
        if files[3] != "application/vnd.google-apps.folder":
            continue
        if files[0] not in seen:
            unique_ids.append(files[0])
            names.append(files[2])
            seen.add(files[0])
    return unique_ids, names


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
    responsehead = requests.head(link.split("?")[0] + "?dl=1", allow_redirects=True)
    if responsehead.status_code == 404:
        print("  dropbox link not available!")
        return
    if not os.path.exists(output + "\\Dropbox - " + sanitize(i["title"])):
        os.makedirs(output + "\\Dropbox - " + sanitize(i["title"]))
    filename = output + "\\Dropbox - " + sanitize(i["title"]) + "\\" + sanitize(responsehead.headers["Content-Disposition"].split("'")[-1])
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


def download_file_from_google_drive(id, dir=""):  # https://stackoverflow.com/questions/25010369/wget-curl-large-file-from-google-drive/39225039 ;)
    def get_confirm_token(response):
        for key, value in response.cookies.items():
            if key.startswith('download_warning'):
                return value

        return None

    def save_response_content(response):
        amountdone = 0
        CHUNK_SIZE = 32768
        if not os.path.exists(output + "\\Drive - " + sanitize(i["title"])):
            os.makedirs(output + "\\Drive - " + sanitize(i["title"]))
        if not os.path.exists(output + "\\Drive - " + sanitize(i["title"]) + "\\" + dir):
            os.makedirs(output + "\\Drive - " + sanitize(i["title"]) + "\\" + dir)
        destination = output + "\\Drive - " + sanitize(i["title"]) + "\\" + dir + "\\" + sanitize(response.headers["Content-Disposition"].split("'")[-1])
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
                    print("  downloading {0}: ".format(os.path.basename(destination)) + " " + str(round(filesize + amountdone / int(response.headers["Content-Range"].partition('/')[-1])) * 100) + "%\r", end="")
            print("  downloaded  {0}".format(os.path.basename(destination)) + ": 100%    ")

    URL = "https://docs.google.com/uc?export=download"

    session = requests.Session()

    headers = {
        "Range": "bytes=0-",
    }

    response = session.get(URL, headers=headers, params={'id': id}, stream=True)

    while response.status_code == 403:
        time.sleep(30)
        response = session.get(URL, headers=headers, params={'id': id}, stream=True)

    token = get_confirm_token(response)

    if token:
        params = {'id': id, 'confirm': token}
        response = session.get(URL, headers=headers, params=params, stream=True)

    save_response_content(response)


def sanitize(filename):
    return re.sub(r"[\/:*?\"<>|]", "_", filename).strip()


def find_urls(s):
    urllist = []
    for findall in re.findall("href=\\\"(https://.+?)\\\"", s):
        urllist.append(re.sub(r"<[^<]+?>", "", re.sub(r"[^a-zA-Z0-9<>]+$", "", findall)))
    return urllist


def downloadfile(i, x, count):
    filename = "{4}\\{0}_{1}p_{2}_{3}".format(i["id"], count, sanitize(i["title"]), os.path.basename(x["path"]), output)
    if os.path.exists(filename):
        filesize = os.stat(filename).st_size
    else:
        filesize = 0
    serverhead = req.head("https://data.kemono.party" + x['path'])
    try:
        serverfilesize = int(serverhead.headers["Content-Length"])
        if filesize < serverfilesize:
            with req.get(f"https://data.kemono.party{x['path']}", stream=True, headers={"Range": f"bytes={filesize}-"}) as r:
                r.raise_for_status()
                with open(filename, "ab") as f:
                    for chunk in r.iter_content(chunk_size=4096):
                        f.write(chunk)
                    print(" image " + str(count) + " successfully downloaded!")
            return
        else:
            print(" image " + str(count) + " already downloaded!")
            return
    except Exception as e:
        print(" error downloading file!")
        print(e)


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
                unique_urls.append(requests.head(url).headers["Location"])
                seen.add(url.split("/")[-1].split("?")[0])
        elif url.startswith("https://drive.google.com/file/"):
            if url.split("?")[0].split("/")[-2] not in seen:
                unique_urls.append(url)
                seen.add(url.split("?")[0].split("/")[-2])
        elif url.startswith("https://www.dropbox.com"):
            download_from_dropbox(url)
        else:  # TODO: add MEGA, or some sort of other file hosting website(s). gdrive and dropbox seem like the most popular ones atm
            pass
    for url in unique_urls:
        if url.startswith("https://drive.google.com/drive/folders/"):
            # Google Drive folder downloading
            print(" Google Drive link found! attempting to download its files...")
            unique_ids = [url.split("/")[-1].split("?")[0]]
            drive_ids_to_download = [unique_ids[0]]
            drive_id_names = {
                unique_ids[0]: ".",
            }
            while len(unique_ids) > 1:
                for myid in unique_ids:
                    unique_ids, names = get_google_drive_subfolder_ids("https://drive.google.com/drive/folders/" + myid)
                    for xd in range(len(unique_ids)):
                        drive_ids_to_download.append(unique_ids[xd])
                        drive_id_names[unique_ids[xd]] = names[xd]
            for ids in drive_ids_to_download:
                gdrive = requests.get("https://drive.google.com/drive/folders/" + ids).text
                driveids = re.findall(r'jsdata=" M2rjcd;_;\d (?:.+?);(.+?);', gdrive)
                for driveid in driveids:
                    if not driveid.startswith("driveweb|"):
                        download_file_from_google_drive(driveid, dir=drive_id_names[ids])
        elif url.startswith("https://drive.google.com/file/"):
            print(" Google Drive link found! attempting to download its files...")
            download_file_from_google_drive(url.split("?")[0].split("/")[-2])
    for x in i["attachments"]:
        count += 1
        while not os.path.exists("{4}\\{0}_{1}p_{2}_{3}".format(int(i["id"]) - 1, count, sanitize(i["title"]), os.path.basename(x["path"]), output)):
            try:
                downloadfile(i, x, count)
                break
            except HTTPError:
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


parser = argparse.ArgumentParser(description="Downloads (deleted) videos from YTPMV creators")
parser.add_argument("-u", "--url", help="user URL", metavar='<url>', required=True)
parser.add_argument("-c", "--cookies", help="", metavar='<cookies>', required=True)  # required because of DDoS-GUARD
parser.add_argument("-p", "--proxy", help="proxy\n supported types: http, https, socks5 (requires pysocks)", metavar='<proxy>')  # SOCKS proxy support is through PySocks - pip install pysocks
parser.add_argument("-o", "--output", help="output folder, defaults to user ID", metavar='<output>')
parser.add_argument("--test-download-services", dest="testdownloadservices", nargs="+", help="test download services\nsupported: gdrive, dropbox", metavar="<service>")
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

if args.testdownloadservices:
    i = {
        "title": "Test"
    }
    if "gdrive" in args.testdownloadservices:
        unique_ids = ["1sMVOcUesv4Ua_KJ-eQ_CMS_5KkrZGFdF"]
        drive_ids_to_download = [unique_ids[0].split("?")[0].split("/")[-1]]
        while len(unique_ids) > 0:
            for i in unique_ids:
                unique_ids = get_google_drive_subfolder_ids("https://drive.google.com/drive/folders/" + i)
                for ids in unique_ids:
                    drive_ids_to_download.append(ids)
        print(drive_ids_to_download)
    if "dropbox" in args.testdownloadservices:
        download_from_dropbox("https://www.dropbox.com/s/yg405bpznyobo3u/test.txt?dl=0")  # File
        download_from_dropbox("https://www.dropbox.com/sh/ne3c7bxtkt5tg4s/AABYPNGfHoil4HO_btudw0wPa?dl=0")  # Folder
    exit()

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
        post = i["id"]
        count = 0
        parse_json(i, count)
