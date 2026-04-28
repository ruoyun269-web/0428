import requests
from bs4 import BeautifulSoup

url = "https://firebase0418.vercel.app/me"
Data = requests.get(url)
Data.encoding = "utf-8"
sp = BeautifulSoup(Data.text, "html.parser")

# 找出所有的 td 標籤
result = sp.select("td")

# 1. 迴圈外面可以先印一次，確認抓到了多少東西
print(f"找到 {len(result)} 個 td 標籤")

for item in result:
    # 2. 這裡只印出「當前這個」td 的文字內容
    print(item.text.strip()) # .strip() 可以去掉多餘的空白或換行
    
    # 這裡通常不需要再 print(result)，除非你想重複看整張清單