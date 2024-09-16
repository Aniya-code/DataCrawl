import re
import csv
from time import sleep
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

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

def get_yt_all_video_urls(driver, video_homeurl: str):
    assert video_homeurl.endswith("videos"), "'video_homeurl' needs to be like: https://www.youtube.com/@TwoMadExplorers/videos"

    last_video_count = 0
    builder = ActionChains(driver)
    driver.get(video_homeurl)
    while (new_count:=video_counts(driver)) > last_video_count and new_count < 1020:
        last_video_count = new_count
        builder.key_down(Keys.END).perform()
        sleep(1.3) # 等待加载
        print(f"-Video count: {last_video_count}") # test

    video_urls = get_video_urls(driver)
    return video_urls
    
if __name__ == "__main__":
     # main
    ##########################################################
    # homeurl = 'https://www.youtube.com/@wenzhaoofficial/videos' # 1
    # homeurl = 'https://www.youtube.com/@JiangFengTimes/videos' # 2
    # homeurl = 'https://www.youtube.com/@funtv8964/videos' # 3
    # homeurl = 'https://www.youtube.com/@MuYangShow/videos' # 4
    # homeurl = 'https://www.youtube.com/@wongkim728/videos' # 5
    # homeurl = 'https://www.youtube.com/@memehongkong/videos' # 6
    # homeurl = 'https://www.youtube.com/@wangzhian/videos' # 7
    # homeurl = 'https://www.youtube.com/@stone_ji/videos' # 8
    # homeurl = 'https://www.youtube.com/@leonard2834/videos' # 9
    # homeurl = 'https://www.youtube.com/@Realpotterking/videos' #10 
    # homeurl = 'https://www.youtube.com/@user-xl8fu9dw5q/videos' #11
    # homeurls = [ 'https://www.youtube.com/@TianLiangTimes/videos', 'https://www.youtube.com/@xiaodaodalang/videos', 'https://www.youtube.com/@user-jt1zr1ey7v/videos', 'https://www.youtube.com/@Taiwan16888/videos',
    #            'https://www.youtube.com/@gongzishen/videos', 'https://www.youtube.com/@dogchinashow/videos', 'https://www.youtube.com/@WuJianMin/videos', 'https://www.youtube.com/@wuyuesanren/videos', 'https://www.youtube.com/@user-tp1lk6kj1g/videos']
    # 电台
    homeurls = ['https://www.youtube.com/@NTDCHINESE/videos', 'https://www.youtube.com/@DJYNews/videos', 'https://www.youtube.com/@voachinese/videos', 'https://www.youtube.com/@RFACHINESE/videos']
    for homeurl in homeurls:
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        driver = webdriver.Chrome(options=options)
                    
        username = re.search(r'@(.+?)/', homeurl).group(1)
                    
        crawled_url_path = f'data/yt_crawled_url/{username}_url_{datetime.now().strftime("%Y%m%d%H%M%S")}.csv'
                    ###########################################################
                    
        video_urls = get_yt_all_video_urls(driver, homeurl)
        with open(crawled_url_path, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['url'])
            writer.writerows([url] for url in video_urls)

        print(f"-Got video urls count: {len(video_urls)}")

        driver.quit()