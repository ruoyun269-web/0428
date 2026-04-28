import requests
from bs4 import BeautifulSoup

url = "https://firebase0418.vercel.app/me"
Data = requests.get(url)
Data.encoding = "utf-8"
sp = BeautifulSoup(Data.text, "html.parser")

# 找出所有的 td
result = sp.select("td")

# 先印出總共抓到幾個，確認有沒有抓對
print(f"總共找到 {len(result)} 個 td 標籤\n")

for item in result:
    # 只印出當前這個標籤的純文字，並去掉多餘空白
    print(item.text.strip())