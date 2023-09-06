import json, os, time
import requests
from pprintpp import pprint as pp


def from_json(path):
    with open(path, "r") as f:
        return json.loads(f.read())


def to_json(item, path):
    with open(path, "w") as f:
        json.dump(item, f, indent=2)
    return path


def fmt_json(src, dst):
    to_json(from_json(src), dst)


def join(root, suffix, *args, mkdir=False):
    path = os.path.abspath(os.path.join(root, suffix, *args))
    if mkdir:
        directory = os.path.dirname(path)
        os.makedirs(directory, exist_ok=True)
    return path


def simple_json_request(url, payload: dict, auth, debug=False):
    if debug:
        pp(payload)
    r = requests.post(
        url,
        json=payload,
        auth=auth
        
    )
    status_code = r.status_code
    print(status_code)
    return status_code, r.json()


def download_url(url, file_path, retry_count=5, debug=True):
    for retry in range(retry_count + 1):
        response = requests.get(url)

        if response.status_code == 200:
            with open(file_path, "wb") as file:
                file.write(response.content)
                if debug:
                    print(f"Downloaded {url} to {file_path}")
            return True
        elif response.status_code == 403 and retry < retry_count:
            wait_time = 2**retry
            print(f"Retrying after {wait_time} seconds...")
            time.sleep(wait_time)
        else:
            print(f"Failed to download {url}. Status code: {response.status_code}")
            break
    else:
        return False
