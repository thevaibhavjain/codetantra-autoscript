from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
import requests, time, json
from bs4 import BeautifulSoup

with open("config.json", "r") as f:
    config = json.load(f)

json_token = ""
active_sessions = []
BASE_URL = f"https://{config['university_name_codetantra']}.codetantra.com"

service = Service(config["webdriver_executable_path"])

chrome_options = Options()
chrome_options.add_argument("--use-fake-ui-for-media-stream")

driver = webdriver.Chrome(options=chrome_options, service=service)
driver.maximize_window()


USERNAME = config["username"]
PASSWORD = config["password"]

def login(username, password):
    url = BASE_URL + "/r/l/p"
    data = f"i={username}&p={password}"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Referer": config["myclass_url"]
    }
    response = requests.post(url, headers=headers, data=data)
    return response.headers["Set-Cookie"]

def fetch_meetings(wtj_token):
    url = BASE_URL + "/secure/rest/dd/mf"
    time_curr = int(time.time()*1000)
    data = '{"minDate":'+ str(time_curr-(15*3600000)) +',"maxDate":' + str(time_curr+(15*3600000)) + ',"filters":{"showSelf":true,"status":"started,ended,scheduled"}}'
    headers={
        "cookie": wtj_token,
        "Referer": BASE_URL + "/secure/tla/mi.jsp",
    }
    response = requests.post(url, headers=headers, data=data)
    for i in response.json()["ref"]:
        if i["status"] == "started": return (i["_id"], i["title"])
    return None, None

def fetch_meeting(cookie, meeting_id):
    url = BASE_URL + "/secure/tla/jnr.jsp?m="+meeting_id
    headers = {
        "cookie": cookie,
        "Referer": BASE_URL + "/secure/tla/mi.jsp",
    }
    response = requests.get(url, headers=headers)
    return response.content.decode('utf-8')

def get_session_url(raw_data):
    soup = BeautifulSoup(raw_data, "html.parser")
    frame = soup.find("iframe", {"id": "frame"})
    return frame.get("src")

def get_session_token(url):
    response = requests.head(url, allow_redirects=False)
    return response.headers['location']

def findnclick_xpath(xpath):
    time.sleep(10)
    listen = driver.find_element_by_xpath(xpath)
    listen.click()

def connect2class(url):
    driver.get(url)
    findnclick_xpath("/html/body/div[2]/div/div/div[1]/div/div/span/button[1]")
    findnclick_xpath("/html/body/div[2]/div/div/div[1]/div/span/button[1]")
    findnclick_xpath("/html/body/div/main/section/div/header/div/div[1]/div[1]/button")
    findnclick_xpath("/html/body/div[1]/main/section/div[1]/div/div/div[2]/div[1]/div[2]/div/div/div/div/div/div[2]/span")

def main():
    global json_token
    while True:
        print("[*] Fetching meetings..")
        try:
            mid, title = fetch_meetings(json_token)
        except Exception:
            json_token = login(USERNAME, PASSWORD)
            continue
        if (mid, title) != (None, None) and mid not in active_sessions:
            print("[+] Live meeting found: ", title)
            meeting_data = fetch_meeting(json_token, mid)
            print("[*] Getting session url...")
            sess_url = get_session_url(meeting_data)
            try:
                sess_url = get_session_token(sess_url)
            except Exception:
                print('[-] Class locating failed.. Retrying in 10 sec')
                time.sleep(10)
                continue
            print("[+] Connecting to the class...")
            connect2class(sess_url)
            active_sessions.append(mid)
        else: print("[-] No live meeting found.. skipping")
        time.sleep(config["refresh_time"])

if __name__ == '__main__':
    json_token = login(USERNAME, PASSWORD)
    main()
