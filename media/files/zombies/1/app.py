import requests
import os
from tqdm import tqdm

BASE_URL = "https://sv4.tezkor.ru/atirgultikoni"
SAVE_DIR = "Atirgul_Tikoni"

EPISODES = [
    "1-3", "4-6", "7-8", "8-11", "12-20", "21",
    "22-27", "28-30", "31-33", "34-36", "37-40",
    "41-44", "45-48", "49-53", "54-57", "58-61"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

os.makedirs(SAVE_DIR, exist_ok=True)


def download(url, filename):
    if os.path.exists(filename):
        print(f"[✓] Skipped: {filename}")
        return

    r = requests.get(url, stream=True, headers=HEADERS)
    if r.status_code != 200:
        print(f"[!] Failed: {url}")
        return

    total = int(r.headers.get("Content-Length", 0))

    with open(filename, "wb") as f, tqdm(
        total=total,
        unit="B",
        unit_scale=True,
        unit_divisor=1024,
        desc=os.path.basename(filename)
    ) as bar:
        for chunk in r.iter_content(chunk_size=10240):
            if chunk:
                f.write(chunk)
                bar.update(len(chunk))


def main():
    for ep in EPISODES:
        video_url = f"{BASE_URL}/{ep}.mp4"
        save_path = os.path.join(SAVE_DIR, f"{ep}.mp4")

        print(f"\n[+] Downloading {ep}")
        download(video_url, save_path)


if __name__ == "__main__":
    main()
