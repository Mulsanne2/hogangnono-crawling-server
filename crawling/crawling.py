from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchWindowException, StaleElementReferenceException, NoSuchElementException
import time
from config import config
import json

def initialize_driver():
    user_agent = config.USER_AGENT

    options = Options()
    options.add_argument(f"user-agent={user_agent}")
    options.add_argument("--start-maximized")
    options.add_experimental_option("detach", True)

    return webdriver.Chrome(options=options)

def login_hogangnono(driver):
    driver.get(config.HOGANGNONO_MAIN_URL)
    time.sleep(0.5)

    driver.find_element(By.CSS_SELECTOR, ".css-wyfpkg").click()  # SMS 설치 팝업창 닫기
    time.sleep(0.5)

    driver.find_element(By.CSS_SELECTOR, ".btn-login").click()  # 우측 상단 로그인 버튼 클릭
    time.sleep(0.5)

    driver.find_element(By.CSS_SELECTOR, ".css-0").click()  # 페이스북 로그인 버튼 클릭
    time.sleep(1)

    original_window = driver.window_handles[0]  # 메인 창 저장

    # 페이스북 로그인 창으로 전환
    for window_handle in driver.window_handles:
        driver.switch_to.window(window_handle)
        if "Facebook" in driver.title:
            break

    time.sleep(0.5)

    driver.find_element(By.CSS_SELECTOR, "#email").send_keys(config.EMAIL)  # 이메일 입력
    driver.find_element(By.CSS_SELECTOR, "#pass").send_keys(config.PASSWORD)  # 비밀번호 입력
    driver.find_element(By.CSS_SELECTOR, "#loginbutton").click()  # 로그인 버튼 클릭

    time.sleep(0.5)
    # 원래 창으로 전환(아래 오류 방지)
    # urllib3.exceptions.ProtocolError: ('Connection aborted.', ConnectionResetError(10054, '현재 연결은 원격 호스트에 의해 강제로 끊겼습니다', None, 10054, None))
    try:
        driver.switch_to.window(original_window)
    except NoSuchWindowException:
        pass

    time.sleep(0.5)
    driver.get(config.HOGANGNONO_MAIN_URL)  # 메인 화면으로 이동을 통해 검색창 html 확보 셋팅
    time.sleep(0.5)

def search_apartment_review(driver, apartment):
    driver.find_element(By.CLASS_NAME, "keyword").send_keys(apartment, Keys.ENTER)  # 특정 아파트 검색
    time.sleep(0.5)

    driver.find_elements(By.CLASS_NAME, "label-container")[0].click()  # 특정 아파트 클릭
    time.sleep(0.5)

    driver.get(driver.current_url + "/2/review")  # 특정 아파트의 후기 페이지로 이동
    time.sleep(1)

def crawling_review(driver):
    review_list = []

    for i in range(10):
        try:  # 더보기 버튼이 있으면 클릭
            more_button = driver.find_element(By.CLASS_NAME, "css-wri049")
            more_button.click()
        except StaleElementReferenceException or NoSuchElementException:  # 더보기 버튼이 없으면 exception 발생. 따라서 스크롤 하도록 로직 구성
            element = driver.find_element(By.CSS_SELECTOR, ".css-5k4zdz.scroll-content > .css-0")
            driver.execute_script("arguments[0].scrollIntoView();", element)
        time.sleep(0.5)

    html = driver.page_source

    soup = BeautifulSoup(html, "html.parser")

    reviews = soup.select(".css-5k4zdz.scroll-content > .css-0")  # 리뷰 전체를 가지고 있는 가장 큰 class

    for review in reviews:
        text_elements = review.select(".css-dei5sc > .css-9uvvzn > .css-1maot43.e1gnm0r1")  # 리뷰 text가 담긴 class

        for text_element in text_elements:
            text = text_element.get_text(strip=True)
            review_list.append({"review" : text})

    review_json = json.dumps(review_list, ensure_ascii=False, indent=4)
    return review_json
