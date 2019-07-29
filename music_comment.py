# -*- coding:utf-8 -*-
# author:Deer404
# contact: 919187569.com
# datetime:2019/7/27 20:48
# software: PyCharm

"""
文件说明：
    爬取QQ音乐某一首歌的评论
"""
import selenium
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
# import requests
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pymysql
import warnings
import jieba
from wordcloud import WordCloud,ImageColorGenerator
import numpy as np
from PIL import Image
import jieba.analyse
# import ipproxyPool
import multiprocessing
class Musiccoment:
    def __init__(self):
        self.options = Options()
        # self.options.add_argument('--headless')
        # self.proxy = "--proxy-server={}".format(ipproxyPool.get_proxy())
        # self.options.add_argument(self.proxy)
        self.browser = webdriver.Chrome(options=self.options)
        self.wait = WebDriverWait(self.browser, 10)
        self.db = pymysql.connect("localhost", "root", "123456", "qqmusic")
        self.cursor = self.db.cursor()
        self.tablesql = "create table if not exists comment( id int primary KEY auto_increment,name varchar(255) NOT NULL ,comment LONGTEXT NOT NULL,subcomment LONGTEXT )"
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            self.cursor.execute(self.tablesql)
        self.comments = ""

    def web(self, url,page):
        print("开始爬取")
        self.browser.get(url)
        self.browser.refresh()
        commentmain = self.wait.until(
            EC.presence_of_element_located((By.XPATH, "//ul[@class='comment__list js_hot_list']")))
        html = self.browser.page_source
        self.soup_source(html)
        if page != 0:
            total = page
        else:
            total = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, "//a[@class='next js_pageindex']/preceding-sibling::a[1]"))).text
        # nextbutton = self.wait.until(EC.element_to_be_clickable((By.XPATH,"//a[@class='next js_pageindex']")))
        for i in range((int(total) - 1)):
            try:
                self.next_page()
            except selenium.common.exceptions.StaleElementReferenceException:
                self.next_page()

    def soup_source(self, html):
        soup = BeautifulSoup(html, 'lxml')
        commentlist = soup.find(class_="comment__list js_all_list").find_all('li')
        for comment in commentlist:
            comment_name = ""
            comment_text = ""
            subcomment = ""
            if comment.find(class_="c_tx_thin js_nick js_nick_only") is not None:
                try:
                    comment_name = comment.find(class_="c_tx_thin js_nick js_nick_only").text
                except TypeError:
                    comment_name = ""
            if comment.find(class_="c_tx_normal comment__text js_hot_text") is not None:
                comment_text = comment.find(class_="c_tx_normal comment__text js_hot_text").text
            if comment.find(class_="js_subcomment") is not None:
                subcomment = comment.find(class_="js_subcomment").text
            self.insert_to_db(comment_name,comment_text,subcomment)

    def insert_to_db(self,name,text,subtext):
        print(name+","+text+","+subtext)
        sql = "insert into comment(name,comment,subcomment) VALUES (%s,%s,%s)"
        self.cursor.execute(sql,(name,text,subtext))
        self.db.commit()

    def next_page(self):
        try:
            nextbutton = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, "//strong[@class='current']/following-sibling::a[1]")))
            nextbutton.click()
        except selenium.common.exceptions.ElementClickInterceptedException:
            self.next_page()
        commentmain = self.wait.until(
            EC.presence_of_all_elements_located((By.XPATH, "//div[@class='main']")))
        self.soup_source(self.browser.page_source)

    def convert_wordcloud(self):
        print("开始生成词云")
        sql = "select * from comment"
        self.cursor.execute(sql)
        result = self.cursor.fetchall()
        for item in result:
            comment = item[2]
            subcomment = item[3]
            self.comments = self.comments +comment+subcomment
        keys= jieba.analyse.textrank(self.comments, topK=300, withWeight=True)
        keywords = dict()
        for i in keys:
            keywords[i[0]] = i[1]
        if "徐坤蔡" in keywords.keys():
            keywords['蔡徐坤'] = keywords.pop("徐坤蔡")
        # jieba.add_word("蔡徐坤")
        # cut_text = " ".join(jieba.cut(self.comments,cut_all=True))
        girl_img = np.array(Image.open('girl.png'))
        image_colors = ImageColorGenerator(girl_img)
        wordcloud = WordCloud(
            scale=10,
            mask=girl_img,
            font_path="C:/Windows/Fonts/simfang.ttf",
            max_words=150,
            random_state=42,
            max_font_size=60,
            background_color="white",
            width=1920,
            height=1080).generate_from_frequencies(keywords)
        wordcloud.recolor(color_func=image_colors)
        wordcloud.to_file("评论词云.png")
        print("生成成功")
    def run(self, url,page=0):
        starttime = time.time()
        self.web(url,page)
        self.convert_wordcloud()
        print("耗时" + str(time.time() - starttime) + "秒")


if __name__ == '__main__':
    music = Musiccoment()
    music.run("https://y.qq.com/n/yqq/song/004BxrBT3coQnC.html",1)
