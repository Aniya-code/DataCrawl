import time
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def execution_time_decorator(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        return result, execution_time
    return wrapper

def video_counts(driver, video_unit_css_selector='#content > ytd-rich-grid-media') -> int:
    elements = driver.find_elements(By.CSS_SELECTOR, video_unit_css_selector)
    return len(elements)

def get_video_urls(driver, video_a_css_selector="#thumbnail > ytd-playlist-thumbnail a", video_url_keywords="/watch?"):
    video_url_list = []
    thumbnails = driver.find_elements(By.CSS_SELECTOR, video_a_css_selector)
    for thumbnail in thumbnails:
        href = thumbnail.get_attribute("href")
        if href and video_url_keywords in href:
            video_url_list.append(href)
    return video_url_list

@execution_time_decorator
def get_yt_all_video_urls(driver, video_homeurl: str):
    assert video_homeurl.endswith("videos"), "'video_homeurl' needs to be like：https://www.youtube.com/@TwoMadExplorers/videos"

    driver.get(video_homeurl)
    driver.execute_script('setInterval(() => { window.scrollTo(0, document.documentElement.scrollHeight); }, 100);')
    try:
        WebDriverWait(driver, 36000, 10).until_not(EC.presence_of_element_located((By.CSS_SELECTOR, 'ytd-continuation-item-renderer > tp-yt-paper-spinner')))
    except TimeoutException:
        pass
    return get_video_urls(driver)
    
if __name__ == "__main__":
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument('--disable-gpu')
    options.add_argument('--blink-settings=imagesEnabled=false')
    driver = webdriver.Chrome(options=options)

    # main
    video_urls, duration = get_yt_all_video_urls(driver, 'https://www.youtube.com/@stone_ji/videos')#'https://www.youtube.com/@memehongkong/videos')
    print(f"-Video count: {video_counts(driver)}") # test
    print(f"-Got video urls count: {len(video_urls)}") # test
    print(f"Duration: {duration}s!")
    with open('csvfile', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['url'])
        writer.writerows([url] for url in video_urls)

    driver.quit()