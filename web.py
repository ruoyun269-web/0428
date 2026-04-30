from flask import Flask, render_template, request
from datetime import datetime
import os
import json
import firebase_admin
from firebase_admin import credentials, firestore
import requests
from bs4 import BeautifulSoup
import re

# --- Firebase 初始化 ---
# 判斷是在 Vercel 還是本地
if not firebase_admin._apps:
    if os.path.exists('serviceAccountKey.json'):
        cred = credentials.Certificate('serviceAccountKey.json')
    else:
        firebase_config = os.getenv('FIREBASE_CONFIG')
        if firebase_config:
            cred_dict = json.loads(firebase_config)
            cred = credentials.Certificate(cred_dict)
        else:
            raise ValueError("找不到 Firebase 設定！")
    firebase_admin.initialize_app(cred)

db = firestore.client()
app = Flask(__name__)

@app.route("/")
def index():
    link = "<h1>歡迎進入鍾若筠的網站20260409</h1>"
    link += "<a href=/mis>課程</a><hr>"
    link += "<a href=/today>現在日期時間</a><hr>"
    link += "<a href=/me>關於我</a><hr>"
    link += "<a href=/welcome?u=411312537&d=靜宜資管&c=資訊管理導論>Get傳值</a><hr>"
    link += "<a href=/account>POST傳值</a><hr>"
    link += "<a href=/math>數學運算(次方/根號)</a><hr>"
    link += "<br><a href=/read>讀取Firestore資料</a><br>"
    link += "<br><a href=/read2>讀取Firestore資料(根據姓名關鍵字'楊')</a><br>"
    link += "<br><a href=/search>搜尋老師資料(輸入姓名)</a><br>"
    link += "<br><a href=/spider>執行爬蟲：抓取老師課程連結</a><br>"
    link += "<br><a href=/movie1>爬取電影資訊 (即時搜尋)</a><br>"
    
    # 新增作業要求的功能連結
    link += "<br><strong style='color:red;'>(1) </strong><a href=/spiderMovie>執行 spiderMovie (爬取電影並存入資料庫)</a><br>"
    link += "<br><strong style='color:red;'>(2) </strong><a href=/searchMovie>執行 searchMovie (從資料庫搜尋電影)</a><br>"
    return link

# --- (1) spiderMovie: 爬取並存入資料庫 ---
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
            
            # 處理海報圖片
            img_url = img_tag.get("src") if img_tag else ""
            if img_url and not img_url.startswith("http"):
                img_url = "https://www.atmovies.com.tw" + img_url
            
            # 處理介紹頁連結
            a_tag = item.find("a")
            href = a_tag.get("href") if a_tag else "#"
            full_link = "https://www.atmovies.com.tw" + href
            
            # 取得上映日期
            info_text = item.get_text()
            date_match = re.search(r"\d{4}/\d{2}/\d{2}", info_text)
            release_date = date_match.group() if date_match else "未公佈"

            # 存入 Firestore (以片名為文件 ID)
            doc_ref = db.collection("電影資料庫").document(name)
            doc_ref.set({
                "title": name,
                "poster": img_url,
                "link": full_link,
                "release_date": release_date,
                "update_time": now_time
            })
            count += 1
            
        info = f"<h2>爬取並儲存成功！</h2>"
        info += f"<p>最近更新日期：{now_time}</p>"
        info += f"<p>目前資料庫中更新了 {count} 部電影。</p>"
        
    except Exception as e:
        info = f"發生錯誤：{e}"
        
    return info + "<br><a href='/'>返回首頁</a>"

# --- (2) searchMovie: 搜尋資料庫電影 ---
@app.route("/searchMovie", methods=["GET", "POST"])
def searchMovie():
    if request.method == "POST":
        keyword = request.form.get("movie_key", "").strip()
        collection_ref = db.collection("電影資料庫")
        docs = collection_ref.get()
        
        res = f"<h3>關鍵字「{keyword}」的資料庫查詢結果：</h3>"
        res += "<table border='1' cellpadding='10' style='border-collapse: collapse;'>"
        res += "<tr><th>編號</th><th>片名</th><th>海報</th><th>介紹頁</th><th>上映日期</th></tr>"
        
        num = 0
        found = False
        for doc in docs:
            movie = doc.to_dict()
            # 判斷關鍵字是否在片名中
            if keyword.lower() in movie.get("title", "").lower():
                found = True
                num += 1
                res += "<tr>"
                res += f"<td>{num}</td>"
                res += f"<td>{movie.get('title')}</td>"
                res += f"<td><img src='{movie.get('poster')}' width='100'></td>"
                res += f"<td><a href='{movie.get('link')}' target='_blank'>電影介紹</a></td>"
                res += f"<td>{movie.get('release_date')}</td>"
                res += "</tr>"
        
        res += "</table>"
        if not found:
            res = f"<h3>抱歉，資料庫中找不到包含「{keyword}」的電影。</h3>"
            
        return res + "<br><a href='/searchMovie'>重新搜尋</a> | <a href='/'>返回首頁</a>"
    else:
        # 搜尋表單介面
        return """
            <h2>搜尋資料庫中的電影</h2>
            <form action="/searchMovie" method="post">
                <input type="text" name="movie_key" placeholder="輸入電影片名關鍵字">
                <button type="submit">搜尋</button>
            </form><br><a href='/'>返回首頁</a>
        """

# --- 原有路由功能 ---

@app.route("/movie1", methods=["GET", "POST"])
def movie1():
    url = "https://www.atmovies.com.tw/movie/next/"
    try:
        Data = requests.get(url)
        Data.encoding = "utf-8"
        sp = BeautifulSoup(Data.text, "html.parser")
        result = sp.select(".filmListAllX li")
        keyword = request.form.get("movie_key", "").strip()
        info = "<h2>近期上映電影 (即時爬取)</h2>"
        info += f"<form action='/movie1' method='post'><input type='text' name='movie_key' value='{keyword}'><button type='submit'>搜尋</button></form><br>"
        info += "<table border='1'><tr><th>海報</th><th>名稱</th></tr>"
        for item in result:
            img_tag = item.find("img")
            name = img_tag.get("alt") if img_tag else "未知"
            if keyword and keyword not in name: continue
            img_url = img_tag.get("src") if img_tag else ""
            info += f"<tr><td><img src='{img_url}' width='100'></td><td>{name}</td></tr>"
        info += "</table>"
    except Exception as e:
        info = str(e)
    return info + "<br><a href='/'>返回首頁</a>"

@app.route("/spider")
def spider():
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    url = "https://www1.pu.edu.tw/~tcyang/course.html"
    try:
        Data = requests.get(url, verify=False)
        Data.encoding = "utf-8"
        sp = BeautifulSoup(Data.text, "html.parser")
        result = sp.select(".team-box a")
        info = "<h2>靜宜老師課程連結</h2><table border='1'><tr><th>老師姓名</th><th>連結</th></tr>"
        for i in result:
            name = i.text.strip()
            href = i.get("href")
            full_url = "https://www1.pu.edu.tw/~tcyang/" + href.replace("./", "")
            info += f"<tr><td>{name}</td><td>{full_url}</td></tr>"
        info += "</table>"
    except Exception as e:
        info = str(e)
    return info + "<br><a href='/'>返回首頁</a>"

@app.route("/search", methods=["GET", "POST"])
def search():
    if request.method == "POST":
        keyword = request.form.get("keyword")
        collection_ref = db.collection("靜宜資管")
        docs = collection_ref.get()
        res = f"<h3>搜尋：{keyword}</h3><hr>"
        for doc in docs:
            t = doc.to_dict()
            if keyword in t.get('name', ''):
                res += f"姓名：{t.get('name')}<br>研究室：{t.get('lab')}<br>郵件：{t.get('mail')}<hr>"
        return res + "<a href='/search'>重新搜尋</a> | <a href='/'>返回首頁</a>"
    return render_template("search.html")

@app.route("/read2")
def read2():
    res = ""
    docs = db.collection("靜宜資管").get()
    for doc in docs:
        t = doc.to_dict()
        if "楊" in t.get('name', ''):
            res += f"姓名：{t.get('name')}，研究室：{t.get('lab')}<br>"
    return (res if res else "查無資料") + "<br><a href='/'>返回首頁</a>"

@app.route("/read")
def read():
    docs = db.collection("靜宜資管").get()
    items = [f"文件內容：{doc.to_dict()}<br>" for doc in docs]
    return "".join(items) + "<br><a href='/'>返回首頁</a>"

@app.route("/mis")
def course():
    return "<h1>資訊管理導論</h1><a href='/'>返回首頁</a>"

@app.route("/today")
def today():
    return render_template("today.html", datetime=str(datetime.now()))

@app.route("/me")
def me():
    return render_template("mis2026b.html")

@app.route("/welcome")
def welcome():
    u, d, c = request.args.get("u"), request.args.get("d"), request.args.get("c")
    return render_template("welcome.html", name=u, dep=d, course=c)

@app.route("/account", methods=["GET", "POST"])
def account():
    if request.method == "POST":
        return f"帳號：{request.form['user']}; 密碼：{request.form['pwd']} <br><a href='/'>返回首頁</a>"
    return render_template("account.html")

@app.route("/math", methods=["GET", "POST"])
def calculate():
    if request.method == "POST":
        x, y, op = float(request.form.get("x")), float(request.form.get("y")), request.form.get("op")
        res = x ** y if op == "pow" else x ** (1/y)
        return f"結果：{res} <br><a href='/math'>重新計算</a>"
    return render_template("calculator.html")

if __name__ == "__main__":
    app.run(debug=True)