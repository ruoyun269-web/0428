import os
import json
import re
import requests
import urllib3
import firebase_admin
from datetime import datetime
from bs4 import BeautifulSoup
from flask import Flask, render_template, request
from firebase_admin import credentials, firestore

# 禁用安全檢查警告（針對台中市政府等部分網站）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

# --- Firebase 初始化優化 ---
def init_firebase():
    if not firebase_admin._apps:
        # 1. 優先檢查實體檔案
        if os.path.exists('serviceAccountKey.json'):
            cred = credentials.Certificate('serviceAccountKey.json')
            firebase_admin.initialize_app(cred)
        # 2. 備援：檢查環境變數 FIREBASE_CONFIG
        else:
            firebase_config = os.getenv('FIREBASE_CONFIG')
            if firebase_config:
                try:
                    cred_dict = json.loads(firebase_config)
                    cred = credentials.Certificate(cred_dict)
                    firebase_admin.initialize_app(cred)
                except Exception as e:
                    print(f"Firebase Config Error: {e}")
            else:
                print("Warning: No Firebase credentials found.")

init_firebase()
db = firestore.client()

# --- 1. 首頁 ---
@app.route("/")
def index():
    link = "<h1>歡迎進入鍾若筠的網站 20260508</h1>"
    link += "<h3>🚀 本次作業要求</h3>"
    link += "<strong style='color:red;'>(1) </strong><a href='/spiderMovie'>執行 spiderMovie (爬取並存入資料庫)</a><br>"
    link += "<strong style='color:red;'>(2) </strong><a href='/searchMovie'>執行 searchMovie (資料庫搜尋)</a><br>"
    link += "<h3>📍 台中生活資訊</h3>"
    link += "<a href='/road'>台中市十大肇事路口</a><br>"
    link += "<a href='/road1'>肇事路口查詢 (進階表單版)</a><br>"
    link += "<a href='/weather'>天氣預報查詢</a><hr>"
    link += "<h3>📚 其他原有功能</h3>"
    link += "<a href='/mis'>課程</a> | <a href='/today'>現在日期時間</a> | <a href='/me'>關於我</a><br>"
    link += "<a href='/read'>讀取Firestore資料</a> | <a href='/spider'>抓取老師課程連結</a><br>"
    link += "<a href='/movie1'>即時爬取電影(不存資料庫)</a><br>"
    return link

# --- 2. spiderMovie (爬取並存入 Firebase) ---
@app.route("/spiderMovie")
def spiderMovie():
    url = "https://www.atmovies.com.tw/movie/next/"
    try:
        Data = requests.get(url, timeout=15)
        Data.encoding = "utf-8"
        sp = BeautifulSoup(Data.text, "html.parser")
        result = sp.select(".filmListAllX li")
        count = 0
        now_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        for item in result:
            img_tag = item.find("img")
            name = img_tag.get("alt") if img_tag else "未知電影"
            img_url = img_tag.get("src") if img_tag else ""
            if img_url and not img_url.startswith("http"):
                img_url = "https://www.atmovies.com.tw" + img_url
            
            a_tag = item.find("a")
            href = a_tag.get("href") if a_tag else "#"
            full_link = "https://www.atmovies.com.tw" + href
            
            info_text = item.get_text()
            date_match = re.search(r"\d{4}/\d{2}/\d{2}", info_text)
            release_date = date_match.group() if date_match else "未公佈"
            
            # 存入 Firestore，以片名為 ID 避免重複
            doc_ref = db.collection("電影資料庫").document(name)
            doc_ref.set({
                "title": name, 
                "poster": img_url, 
                "link": full_link,
                "release_date": release_date, 
                "update_time": now_time
            })
            count += 1
        info = f"<h2>爬取成功！目前更新了 {count} 部電影。</h2>"
    except Exception as e:
        info = f"發生錯誤：{e}"
    return info + "<br><a href='/'>返回首頁</a>"

# --- 3. searchMovie (從 Firebase 搜尋) ---
@app.route("/searchMovie", methods=["GET", "POST"])
def searchMovie():
    if request.method == "POST":
        keyword = request.form.get("movie_key", "").strip()
        docs = db.collection("電影資料庫").get()
        res = f"<h3>關鍵字「{keyword}」查詢結果：</h3><table border='1' style='border-collapse:collapse; width:80%;'>"
        res += "<tr style='background-color:#f2f2f2;'><th>片名</th><th>海報</th><th>介紹</th><th>上映日</th></tr>"
        found = False
        for doc in docs:
            movie = doc.to_dict()
            if keyword.lower() in movie.get("title", "").lower():
                found = True
                res += f"<tr><td>{movie.get('title')}</td>"
                res += f"<td><img src='{movie.get('poster')}' width='100'></td>"
                res += f"<td><a href='{movie.get('link')}' target='_blank'>查看介紹</a></td>"
                res += f"<td>{movie.get('release_date')}</td></tr>"
        res += "</table>"
        if not found: 
            res = f"<h3>資料庫中找不到與「{keyword}」相關的電影。</h3>"
        return res + "<br><a href='/searchMovie'>重新搜尋</a> | <a href='/'>返回首頁</a>"
    
    return '''
        <h2>搜尋電影 (資料庫)</h2>
        <form method="post">
            <input name="movie_key" placeholder="輸入電影片名" required>
            <button type="submit">搜尋</button>
        </form><br><a href="/">返回</a>
    '''

# --- 4. 交通與天氣 ---
@app.route("/road")
def road():
    R = "<h1>台中市十大肇事路口 (鍾若筠)</h1><br>"
    url = "https://datacenter.taichung.gov.tw/swagger/OpenData/a1b899c0-511f-4e3d-b22b-814982a97e41"
    try:
        response = requests.get(url, verify=False, timeout=10).json()
        R += "<i>前 10 筆列表：</i><br><ul>"
        for item in response[:10]:
            R += f"<li>{item['路口名稱']} (原因：{item.get('主要肇因', '未知')})</li>"
        R += "</ul>"
    except Exception as e:
        R += f"連線錯誤：{e}"
    return R + "<br><hr><a href='/'>回首頁</a>"

@app.route("/road1")
def road1():
    q = request.args.get("q", "")
    results = ""
    if q:
        url = "https://datacenter.taichung.gov.tw/swagger/OpenData/a1b899c0-511f-4e3d-b22b-814982a97e41"
        try:
            res = requests.get(url, timeout=15, verify=False).json()
            results = "<h3>查詢結果：</h3><table border='1' style='border-collapse:collapse;'>"
            results += "<tr><th>路口名稱</th><th>主要肇因</th></tr>"
            for item in res:
                if q in item.get("路口名稱", ""):
                    results += f"<tr><td>{item['路口名稱']}</td><td>{item.get('主要肇因')}</td></tr>"
            results += "</table>"
        except:
            results = "查詢出錯"
    
    html = f"""
    <h1>台中市易肇事路口查詢 (鍾若筠)</h1>
    <form action="/road1" method="get">
        請輸入路名：<input type="text" name="q" value="{q}">
        <button type="submit">查詢</button>
    </form>
    <hr>
    {results}
    <br><a href="/">回首頁</a>
    """
    return html

@app.route("/weather")
def weather():
    city = request.args.get("city", "臺中市").replace("台", "臺")
    token = "CWA-7B8D6964-106B-4180-84E1-6821215D3941" # 建議換成你申請的氣象局 Token
    url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001?Authorization={token}&format=JSON&locationName={city}"
    try:
        data = requests.get(url, timeout=10).json()
        loc = data["records"]["location"][0]
        state = loc["weatherElement"][0]["time"][0]["parameter"]["parameterName"]
        result = f"<h3>{city} 目前天氣：{state}</h3>"
    except:
        result = "查無資料或 Token 無效"
    return f"<h2>縣市天氣查詢</h2><form><input name='city' placeholder='臺中市'><button>查詢</button></form>{result}<br><a href='/'>回首頁</a>"

# --- 5. 基礎功能 ---
@app.route("/mis")
def course(): return "<h1>資訊管理導論 - 鍾若筠</h1><a href='/'>返回首頁</a>"

@app.route("/today")
def today(): return f"<h1>現在時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</h1><a href='/'>回首頁</a>"

@app.route("/me")
def me(): return "<h1>關於鍾若筠的頁面</h1><a href='/'>回首頁</a>"

@app.route("/read")
def read():
    try:
        docs = db.collection("電影資料庫").limit(5).get()
        items = [f"電影：{doc.to_dict().get('title')}<br>" for doc in docs]
        res = "".join(items) if items else "資料庫目前沒資料"
    except:
        res = "讀取失敗"
    return "<h3>最近 5 筆電影資料：</h3>" + res + "<br><a href='/'>返回首頁</a>"

if __name__ == "__main__":
    app.run(debug=True)