import requests, json
#city = "臺中市"
city = input("請輸入縣市：")
city = city.replace("台","臺")
token = "rdec-key-123-45678-011121314"
url = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001?Authorization=" + token + "&format=JSON&locationName=" + str(city)
Data = requests.get(url)
#print(Data.text)
Weather = json.loads(Data.text)["records"]["location"][0]["weatherElement"][0]["time"][0]["parameter"]["parameterName"]
Rain = json.loads(Data.text)["records"]["location"][0]["weatherElement"][1]["time"][0]["parameter"]["parameterName"]
print(Weather + "，降雨機率：" + Rain + "%")
