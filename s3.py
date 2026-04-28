import requests
from bs4 import BeautifulSoup

url = "https://firebase0418.vercel.app/me"
Data = requests.get(url)
Data.encoding = "utf-8"

sp = BeautifulSoup(Data.text, "html.parser")

# 使用 find 找唯一的 id
result = sp.find(id="h2text")

if result:
    print(result.text)
else:
    print("找不到指定的 ID")