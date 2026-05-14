import requests
from bs4 import BeautifulSoup

url = "https://math0326.vercel.app/me"
Data = requests.get(url)
Data.encoding = "utf-8"

sp = BeautifulSoup(Data.text, "html.parser")

# 改用 find_all 抓取所有 <img> 標籤
result = sp.find_all("img")

for item in result:
    src = item.get("src")
    if src:
        print(src)
        print()