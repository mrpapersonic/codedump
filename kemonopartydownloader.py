# example args.url: https://kemono.party/fanbox/user/5375435/post/2511461
import argparse
import http.cookiejar
import os
import re
import requests  # pip install requests
import time
from urllib.error import HTTPError


def sanitize(filename):
    return re.sub(r"[\/:*?\"<>|]", "_", filename)


def downloadfile(i, x, count):
    filename = "{4}\\{0}_{1}p_{2}_{3}".format(i["id"], count, sanitize(i["title"]), os.path.basename(x["path"]), output)
    if os.path.exists(filename):
        filesize = os.stat(filename).st_size
    else:
        filesize = 0
    if str(filesize) != req.head(f"https://data.kemono.party{x['path']}").headers["Content-Length"]:
        with req.get(f"https://data.kemono.party{x['path']}", stream=True, headers={"Range": f"bytes={filesize}-"}) as r:
            r.raise_for_status()
            with open(filename, "ab") as f:
                for chunk in r.iter_content(chunk_size=4096):
                    f.write(chunk)
                print("image " + str(count) + " successfully downloaded!")
        return
    else:
        print("image " + str(count) + " already downloaded!")
        return


parser = argparse.ArgumentParser(description="Downloads (deleted) videos from YTPMV creators")
parser.add_argument("-u", "--url", help="user URL", metavar='<url>', required=True)
parser.add_argument("-c", "--cookies", help="", metavar='<url>', required=True)  # required because of DDoS-GUARD
parser.add_argument("-p", "--proxy", help="proxy\n supported types: http, https, socks5 (requires pysocks)", metavar='<url>')  # SOCKS proxy support is through PySocks - pip install pysocks
parser.add_argument("-o", "--output", help="output folder, defaults to user ID", metavar='<url>')
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
    print("do not input user IDs here! use a link instead")
    exit()
except Exception:
    pass

if args.url.split("/")[-2] == "post":
    service = args.url.split("/")[-5]
    user = args.url.split("/")[-3]
    post = args.url.split("/")[-1]
    userdata = req.get("https://kemono.party/api/{0}/user/{1}/post/{2}".format(service, user, post)).json()
elif args.url.split("/")[-2] == "user":
    service = args.url.split("/")[-3]
    user = args.url.split("/")[-1]
    userdata = req.get("https://kemono.party/api/{0}/user/{1}".format(service, user)).json()

if not args.output:
    output = user
else:
    output = args.output

if not os.path.isdir(output):
    if os.path.exists(output):
        os.remove(output)
    os.mkdir(output)

for i in userdata:
    print(i["id"])
    post = i["id"]
    count = 0
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
