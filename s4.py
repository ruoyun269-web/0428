import requests
from bs4 import BeautifulSoup

url = "https://firebase0418.vercel.app/me"
Data = requests.get(url)
Data.encoding = "utf-8"
sp = BeautifulSoup(Data.text, "html.parser")
result = sp.find(id="h2text")
print(result.text) # 確保這裡前面沒有多餘的空白或 Tab