import requests
from bs4 import BeautifulSoup

url = "https://firebase0418.vercel.app/me"
Data = requests.get(url)
Data.encoding = "utf-8"
sp = BeautifulSoup(Data.text, "html.parser")

# 使用 select 找出所有在 td 裡面的 iframe
result = sp.select("td iframe")

for item in result:
    # 這裡要縮排
    print(item.get("src"))