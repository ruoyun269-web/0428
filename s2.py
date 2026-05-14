import requests
from bs4 import BeautifulSoup

url = "https://math0326.vercel.app/me"
Data = requests.get(url)
Data.encoding = "utf-8"

sp = BeautifulSoup(Data.text, "html.parser")
result = sp.find_all("td") 

for item in result:
    print(item.text.strip())
    print()
