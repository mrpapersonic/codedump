import argparse
import internetarchive  # pip install internetarchive
import json
import os
import re  # pip install re
import urllib.request
import youtube_dl  # pip install youtube-dl
import itertools
from urllib.error import HTTPError

class MyLogger(object):
    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        pass

ACCENT_CHARS = dict(zip('ÂÃÄÀÁÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖŐØŒÙÚÛÜŰÝÞßàáâãäåæçèéêëìíîïðñòóôõöőøœùúûüűýþÿ',
                        itertools.chain('AAAAAA', ['AE'], 'CEEEEIIIIDNOOOOOOO', ['OE'], 'UUUUUY', ['TH', 'ss'],
                                        'aaaaaa', ['ae'], 'ceeeeiiiionooooooo', ['oe'], 'uuuuuy', ['th'], 'y')))

def sanitize_filename(s, restricted=False, is_id=False):
    # from youtube-dl utils
    def replace_insane(char):
        if restricted and char in ACCENT_CHARS:
            return ACCENT_CHARS[char]
        if char == '?' or ord(char) < 32 or ord(char) == 127:
            return ''
        elif char == '"':
            return '' if restricted else '\''
        elif char == ':':
            return '_-' if restricted else ' -'
        elif char in '\\/|*<>':
            return '_'
        if restricted and (char in '!&\'()[]{}$;`^,#' or char.isspace()):
            return '_'
        if restricted and ord(char) > 127:
            return '_'
        return char

    # Handle timestamps
    s = re.sub(r'[0-9]+(?::[0-9]+)+', lambda m: m.group(0).replace(':', '_'), s)
    result = ''.join(map(replace_insane, s))
    if not is_id:
        while '__' in result:
            result = result.replace('__', '_')
        result = result.strip('_')
        # Common case of "Foreign band name - English song title"
        if restricted and result.startswith('-_'):
            result = result[2:]
        if result.startswith('-'):
            result = '_' + result[len('-'):]
        result = result.lstrip('.')
        if not result:
            result = '_'
    return result

def matroska_find(filelist):
    for myfile in filelist:
        if os.path.splitext(myfile)[1] == ".mkv" or os.path.splitext(myfile)[1] == ".webm":
            return True
    return False

def ytdl_hook(d):
    if d["status"] == "finished":
        print(" downloaded {0}:    100% ".format(os.path.basename(d["filename"])))
    if d["status"] == "downloading":
        print(" downloading {0}: {1}\r".format(os.path.basename(d["filename"]), d["_percent_str"]), end="")
    if d["status"] == "error":
        print(" an error occurred downloading {0}!")


parser = argparse.ArgumentParser(description="Downloads (deleted) videos from YTPMV creators")
parser.add_argument("-c", "--channel", help="channel URL", metavar='<url>', required=True)
parser.add_argument("-d", "--database", help="json database (https://finnrepo.a2hosted.com/YTPMV_Database)", metavar='<path>', required=True)
parser.add_argument("-o", "--output", help="output directory, defaults to the channel ID", metavar='<output>')
args = parser.parse_args()

if args.channel[:8] == "https://" or args.channel[:7] == "http://":
    channel = args.channel.split("/")[-1]
else:
    channel = args.channel

if args.output:
    output = args.output
else:
    output = channel

if not os.path.exists(output):
    os.mkdir(output)

ytdl_opts = {
    "outtmpl": "{0}/%(title)s-%(id)s.%(ext)s".format(output),
    "retries": 100,
    "nooverwrites": True,
    "call_home": False,
    "quiet": True,
    "writeinfojson": True,
    "writedescription": True,
    "writethumbnail": True,
    "writeannotations": True,
    "writesubtitles": True,
    "allsubtitles": True,
    "ignoreerrors": True,
    "addmetadata": True,
    "continuedl": True,
    "embedthumbnail": True,
    "format": "bestvideo+bestaudio/best",
    "restrictfilenames": True,
    "no_warnings": True,
    "progress_hooks": [ytdl_hook],
    "logger": MyLogger(),
    "ignoreerrors": False,
}

with open(args.database, "r", encoding="utf-8") as f:
    data = json.load(f)
    for i in data["videos"]:
        try:
            uploader = i["uploader_id"]
        except Exception:
            uploader = "unknown"
        finally:
            if uploader == channel:
                print("{0}:".format(i["id"]))
                isalreadydownloaded = 0
                for file in os.listdir(output):
                    if os.path.splitext(file)[1] == ".json":
                        if file.find("-" + i["id"] + ".info.json") != -1:
                            isalreadydownloaded = 1
                if isalreadydownloaded == 1:  # not sure how to bypass this without having to go out of the for loop, if anyone could tell me how that would be great!
                    print(" video already downloaded!")
                    continue
                with youtube_dl.YoutubeDL(ytdl_opts) as ytdl:
                    try:
                        result = ytdl.download(["https://youtube.com/watch?v={0}".format(i["id"])])  # TODO: add check for existing downloaded items and don't download them
                        continue
                    except Exception:
                        print(" video is not available! attempting to find Internet Archive pages of it...")
                if internetarchive.get_item("youtube-{0}".format(i["id"])).exists:  # download from internetarchive if available
                    fnames = [f.name for f in internetarchive.get_files("youtube-{0}".format(i["id"]))]
                    disallowednames = ["__ia_thumb.jpg", "youtube-{0}_archive.torrent".format(i["id"]), "youtube-{0}_files.xml".format(i["id"]), "youtube-{0}_meta.sqlite".format(i["id"]), "youtube-{0}_meta.xml".format(i["id"])]  # list of IA-created files we don't need
                    flist = []
                    for fname in fnames:
                        if matroska_find(fnames):
                            if fname[-4:] == ".mp4":
                                continue
                        else:
                            if fname[-7:] == ".ia.mp4":
                                continue
                        if fname.find("/") == -1:
                            if fname not in disallowednames and fname[-21:] != "{0}_thumb.jpg".format(i["id"]) and fname[-15:] != "{0}.ogv".format(i["id"]):
                                flist.append(fname)
                    if len(flist) >= 1:
                        internetarchive.download("youtube-{0}".format(i["id"]), files=flist, verbose=True, destdir=output, no_directory=True, ignore_existing=True)
                    else:
                        print(" video already downloaded!")
                        continue
                    if os.path.exists(output + "\\" + i["id"] + ".info.json"):  # will always exist no matter which setting was used to download
                        for fname in flist:
                            if os.path.exists(output + "\\" + fname) and not os.path.exists(output + "\\" + sanitize_filename(i["title"], restricted=True) + "-" + fname):
                                os.rename(output + "\\" + fname, output + "\\" + sanitize_filename(i["title"], restricted=True) + "-" + fname)
                    else:
                        print("ID file not found!")
                else:  # download the vid from waybackmachine (NOTE: only tested with youtube links after polymer, however SHOULD work with links created before then)
                    print(" video does not have a Internet Archive page! attempting to download from the Wayback Machine...")
                    try:
                        contenttype = urllib.request.urlopen("https://web.archive.org/web/2oe_/http://wayback-fakeurl.archive.org/yt/{0}".format(i["id"])).getheader("Content-Type")
                        if contenttype == "video/webm":
                            ext = "webm"
                        else:
                            ext = "mp4"
                        urllib.request.urlretrieve("https://web.archive.org/web/2oe_/http://wayback-fakeurl.archive.org/yt/{0}".format(i["id"]), "{3}\\{0}-{1}.{2}".format(sanitize_filename(i["title"], restricted=True), i["id"], ext, output))
                        print(" downloaded {0}-{1}.{2}".format(sanitize_filename(i["title"], restricted=True), i["id"], ext))
                    except HTTPError:
                        print(" video not available on the Wayback Machine!")
                    except Exception as e:
                        print(" unknown error downloading video!")
                        print(e)
                    # metadata
                    meta = {
                        "fulltitle": i["title"],
                        "description": i["description"],
                        "upload_date": i["upload_date"],
                        "uploader": i["uploader"]
                    }
                    metajson = json.dumps(meta)
                    with open("{2}\\{0}-{1}.info.json".format(sanitize_filename(i["title"], restricted=True), i["id"], output), "w") as jsonfile:
                        print(metajson, end="", file=jsonfile)
                    print(" saved {0}-{1}.info.json".format(sanitize_filename(i["title"], restricted=True), i["id"], output))
