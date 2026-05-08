import os
import json
import re
import time
import requests
import urllib3
import firebase_admin
from datetime import datetime
from bs4 import BeautifulSoup
from flask import Flask, render_template, request
from firebase_admin import credentials, firestore

# 禁用安全檢查警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- Firebase 初始化 ---
if not firebase_admin._apps:
    if os.path.exists('serviceAccountKey.json'):
        cred = credentials.Certificate('serviceAccountKey.json')
    else:
        firebase_config = os.getenv('FIREBASE_CONFIG')
        if firebase_config:
            cred_dict = json.loads(firebase_config)
            cred = credentials.Certificate(cred_dict)
        else:
            cred = None
    
    if cred:
        firebase_admin.initialize_app(cred)

db = firestore.client()
app = Flask(__name__)

# --- 1. 首頁 ---
@app.route("/")
def index():
    link = "<h1>歡迎進入鍾若筠的網站 20260508</h1>"
    link += "<h3>🚀 本次作業要求</h3>"
    link += "<strong style='color:red;'>(1) </strong><a href=/spiderMovie>執行 spiderMovie (爬取電影並存入資料庫)</a><br>"
    link += "<strong style='color:red;'>(2) </strong><a href=/searchMovie>執行 searchMovie (從資料庫搜尋電影)</a><br>"
    link += "<h3>📍 台中生活資訊</h3>"
    link += "<a href='/road'>台中市十大肇事路口</a><br>"
    link += "<a href='/road1'>肇事路口查詢 (進階表單版)</a><br>"
    link += "<a href='/weather'>天氣預報查詢</a><hr>"
    link += "<h3>📚 其他原有功能</h3>"
    link += "<a href=/mis>課程</a> | <a href=/today>現在日期時間</a> | <a href=/me>關於我</a><br>"
    link += "<a href=/read>讀取Firestore資料</a> | <a href=/spider>抓取老師課程連結</a><br>"
    link += "<a href=/movie1>即時爬取電影(不存資料庫)</a><br>"
    return link

# --- 2. spiderMovie ---
@app.route("/spiderMovie")
def spiderMovie():
    url = "https://www.atmovies.com.tw/movie/next/"
    try:
        Data = requests.get(url)
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
            doc_ref = db.collection("電影資料庫").document(name)
            doc_ref.set({
                "title": name, "poster": img_url, "link": full_link,
                "release_date": release_date, "update_time": now_time
            })
            count += 1
        info = f"<h2>爬取成功！目前更新了 {count} 部電影。</h2>"
    except Exception as e:
        info = f"發生錯誤：{e}"
    return info + "<br><a href='/'>返回首頁</a>"

# --- 3. searchMovie ---
@app.route("/searchMovie", methods=["GET", "POST"])
def searchMovie():
    if request.method == "POST":
        keyword = request.form.get("movie_key", "").strip()
        docs = db.collection("電影資料庫").get()
        res = f"<h3>關鍵字「{keyword}」查詢結果：</h3><table border='1'>"
        res += "<tr><th>片名</th><th>海報</th><th>介紹</th><th>上映日</th></tr>"
        found = False
        for doc in docs:
            movie = doc.to_dict()
            if keyword.lower() in movie.get("title", "").lower():
                found = True
                res += f"<tr><td>{movie.get('title')}</td>"
                res += f"<td><img src='{movie.get('poster')}' width='100'></td>"
                res += f"<td><a href='{movie.get('link')}'>介紹</a></td>"
                res += f"<td>{movie.get('release_date')}</td></tr>"
        res += "</table>"
        if not found: res = "<h3>資料庫中找不到相關電影。</h3>"
        return res + "<br><a href='/searchMovie'>重新搜尋</a> | <a href='/'>返回首頁</a>"
    return '<h2>搜尋電影</h2><form method="post"><input name="movie_key"><button>搜尋</button></form><br><a href="/">返回</a>'

# --- 4. 交通與天氣 (已改名為鍾若筠) ---
@app.route("/road")
def road():
    # 這裡已經幫妳改好名字了
    R = "<h1>十大肇事路口(113年10月) 鍾若筠</h1><br>"
    url = "https://datacenter.taichung.gov.tw/swagger/OpenData/a1b899c0-511f-4e3d-b22b-814982a97e41"
    try:
        response = requests.get(url, verify=False, timeout=10).json()
        q = request.args.get("q", "")
        found = False
        for item in response:
            if q and q in item.get("路口名稱", ""):
                R += f"📍 <b>{item['路口名稱']}</b>，原因：{item['主要肇因']} <br>"
                found = True
        if not found:
            R += "<i>前 10 筆列表：</i><br>"
            for item in response[:10]:
                R += f"• {item['路口名稱']} <br>"
    except Exception as e:
        R += f"連線錯誤：{e}"
    return R + "<br><hr><a href='/'>回首頁</a>"

@app.route("/road1")
def road1():
    q = request.values.get("q", "")
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
    
    # 這裡的名字也改好了
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
    city = request.values.get("city", "臺中市").replace("台", "臺")
    token = "rdec-key-123-45678-011121314"
    url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001?Authorization={token}&format=JSON&locationName={city}"
    try:
        data = requests.get(url, timeout=10).json()
        loc = data["records"]["location"][0]
        state = loc["weatherElement"][0]["time"][0]["parameter"]["parameterName"]
        result = f"<h3>{city} 目前天氣：{state}</h3>"
    except:
        result = "查無資料"
    return f"<h2>縣市天氣查詢</h2><form><input name='city' placeholder='臺中市'><button>查詢</button></form>{result}<br><a href='/'>回首頁</a>"

# --- 5. 基礎功能 ---
@app.route("/mis")
def course(): return "<h1>資訊管理導論</h1><a href='/'>返回首頁</a>"

@app.route("/today")
def today(): return render_template("today.html", datetime=str(datetime.now()))

@app.route("/me")
def me(): return render_template("mis2026b.html")

@app.route("/read")
def read():
    docs = db.collection("靜宜資管").get()
    items = [f"內容：{doc.to_dict()}<br>" for doc in docs]
    return "".join(items) + "<br><a href='/'>返回首頁</a>"

@app.route("/spider")
def spider():
    url = "https://www1.pu.edu.tw/~tcyang/course.html"
    try:
        sp = BeautifulSoup(requests.get(url, verify=False).text, "html.parser")
        result = sp.select(".team-box a")
        info = "<h2>老師課程連結</h2>"
        for i in result:
            info += f"{i.text.strip()}<br>"
    except:
        info = "抓取失敗"
    return info + "<br><a href='/'>返回首頁</a>"

@app.route("/movie1", methods=["GET", "POST"])
def movie1():
    url = "https://www.atmovies.com.tw/movie/next/"
    try:
        sp = BeautifulSoup(requests.get(url).text, "html.parser")
        result = sp.select(".filmListAllX li")
        keyword = request.form.get("movie_key", "").strip()
        info = "<h2>即時電影搜尋</h2>"
        for item in result:
            name = item.find("img").get("alt") if item.find("img") else "未知"
            if keyword in name:
                info += f"{name}<br>"
    except:
        info = "錯誤"
    return info + "<br><a href='/'>返回首頁</a>"

if __name__ == "__main__":
    app.run(debug=True)