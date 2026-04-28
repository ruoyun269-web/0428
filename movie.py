import requests
from bs4 import BeautifulSoup

url = "https://www.atmovies.com.tw/movie/next/"
Data = requests.get(url)
Data.encoding = "utf-8"

sp = BeautifulSoup(Data.text, "html.parser")
result = sp.select(".filmListAllX li")

for item in result:
    # 這裡必須縮排（按一次 Tab）
    print(item.find("img").get("alt"))
    
    # 這裡也要對齊，且屬性名稱是 "href"
    print("https://www.atmovies.com.tw" + item.find("a").get("href"))
    print("https://www.atmovies.com.tw" + item.find("img").get("src"))
    
    print()