

#
# Downloads FujiNet-PC latest release from GitHub
#

import sys
import os
import json
import urllib.request
import urllib.error
import fnmatch


RELEASE_JSON_URL = 'https://api.github.com/repos/FujiNetWIFI/fujinet-pc/releases/latest'


def usage():
    print(os.path.basename(sys.argv[0]), "[release_json_url]", "pattern")


def download_release(url: str, pattern: str):
    token = os.environ.get('GITHUB_TOKEN', None)
    headers = {'Accept': 'application/vnd.github.v3+json'}
    if token:
        headers['Authorization'] = 'token ' + token
    try:
        releases = urllib.request.urlopen(
            urllib.request.Request(url,
            headers=headers,
        )).read()
        _json = json.loads(releases)
    except urllib.error.HTTPError as e:
        _json = None
        print("Download error!")
        print("URL:", e.geturl())
        print("Response code:", e.getcode())
        print(e.info())
    if not isinstance(_json, dict):
        return 1
    assets = _json.get('assets',[])
    for asset in assets:
        name = asset.get('name','')
        if fnmatch.fnmatch(name, pattern):
            file_url = asset.get('browser_download_url')
            if file_url:
                urllib.request.urlretrieve(file_url, name)
                print(name)
    return 0

def main():
    if not (1 < len(sys.argv) < 4):
        usage()
        return -1

    url = sys.argv[1] if len(sys.argv) > 2 else RELEASE_JSON_URL
    pat = sys.argv[2] if len(sys.argv) > 2 else sys.argv[1]
    return download_release(url, pat)


if __name__ == "__main__":
    sys.exit(main())
