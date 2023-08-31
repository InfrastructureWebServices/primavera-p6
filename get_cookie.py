from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
from os import path
import json
dir = path.dirname(__file__)

with open('username.txt', 'r') as f:
    username = f.read()
with open('password.txt', 'r') as f:
    password = f.read()

def get_cookie():
    dir = path.dirname(__file__)
    ex_path = path.join(dir, "geckodriver")
    print(ex_path)
    service = Service(executable_path=ex_path)
    options = Options()
    options.add_argument('-headless')
    options.add_argument("-private")
    driver = webdriver.Firefox(service=service, options=options)

    driver.implicitly_wait(3)
    driver.get('https://au.itwocx.com/')

    user = driver.find_element(By.ID, 'Email') 
    user.send_keys(username)

    pw = driver.find_element(By.ID, 'Password') 
    pw.send_keys(password + Keys.ENTER)
    time.sleep(10)
    driver.get('https://au.itwocx.com/GLU-VCA')
    time.sleep(10)
    driver.get('https://au.itwocx.com/api/23.08/api/help/index#!/Document/Document_Search')
    time.sleep(10)
    cookies = driver.get_cookies()
    print(cookies)
    cookie_str = ""
    for i in cookies:
        cookie_str += i.get("name") + "=" + i.get("value") + "; "
        print(i)
    f = open(path.join(dir, 'cookie.txt'), 'w')
    f.write(cookie_str)
    f.close()


    driver.quit()