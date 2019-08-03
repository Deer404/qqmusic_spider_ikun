# -*- coding:utf-8 -*-
# author:Deer404
# contact: 919187569.com
# datetime:2019/8/2 16:08
# software: PyCharm

"""
文件说明：

"""
import grequests
import requests
import json
import pymysql
import warnings
import jieba ##词云依赖库
from wordcloud import WordCloud,ImageColorGenerator
import numpy as np
from PIL import Image
import jieba.analyse
import matplotlib
class MusicComment:
    def __init__(self, url=None):
        self.urlist = []
        self.url = url
        self.tablesql = "create table if not exists comment( id int primary KEY auto_increment," \
                        "nickname varchar(255) NOT NULL ,comment LONGTEXT NOT NULL,commentid varchar(255) NOT NULL)"
        self.db = self.db = pymysql.connect("localhost", "root", "123456", "qqmusic")
        self.cursor = self.db.cursor()
        self.commentidlist = []
        self.comments = ''

    def request_Comment(self, url):
        response = requests.get(url).text
        response = json.loads(response)
        for item in response['comment']['commentlist']:
            commentId = item['commentid']
            commentContent = item['rootcommentcontent']
            nickName = item['nick']
            if item['middlecommentcontent'] is not None:
                for item in item['middlecommentcontent']:
                    commentContent = item['subcommentcontent']
                    nickName = item['replynick']
                    break;
            else:
                subCommentContent = ""
            self.commentidlist.append(commentId)
            self.add_Table(commentContent=commentContent, nickName=nickName, commentId=commentId)
        lastCommentId = self.commentidlist[-1]
        self.commentidlist = []
        return lastCommentId

    def create_Table(self):
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            self.cursor.execute(self.tablesql)

    def add_Table(self, commentContent, nickName, commentId):
        print(commentContent + "|" + nickName + "|" + commentId)
        sql = 'insert into comment(nickname,comment,commentid) VALUES (%s,%s,%s)'
        self.cursor.execute(sql, (nickName, commentContent, commentId))
        self.db.commit()

    def next_page(self, commentid, pagenum):
        pageurl = "https://c.y.qq.com/base/fcgi-bin/fcg_global_comment_h5.fcg?g_tk=5381&loginUin=0&hostUin=0&format=json&inCharset=utf8&outCharset=GB2312" \
                  "&notice=0&platform=yqq.json&needNewCode=0&cid=205360772&reqtype=2&biztype=1&topid=234369105&cmd=" \
                  "8&needmusiccrit=0&pagenum=" + pagenum + "&pagesize=25&lasthotcommentid=" + commentid + "+&domain=qq.com&ct=24&cv=10101010"
        # print(pageurl)
        return pageurl

    def wipe_data(self):  # 清除表数据 不可撤回噢
        deletesql = "truncate table comment"
        self.cursor.execute(deletesql)
        self.db.commit()

    def convert_wordcloud(self):
        print("开始生成词云")
        sql = "select * from comment"
        self.cursor.execute(sql)
        result = self.cursor.fetchall()
        for item in result:
            comment = item[2]
            self.comments = self.comments + comment
        keys = jieba.analyse.textrank(self.comments, topK=300, withWeight=True)
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

    def run(self):
        self.create_Table()
        lastCommentId = self.request_Comment(self.url)
        for i in range(1, 1):
            pageurl = self.next_page(lastCommentId, str(i))
            lastCommentId = self.request_Comment(pageurl)
        self.convert_wordcloud()

if __name__ == "__main__":
    music = MusicComment(
        "https://c.y.qq.com/base/fcgi-bin/fcg_global_comment_h5.fcg?g_tk=5381&loginUin=0&hostUin=0&format=json&inCharset=utf8&outCharset=GB2312&notice=0&platform=yqq.json&needNewCode=0&cid=205360772&reqtype=2&biztype=1&topid=234369105&cmd=8&needmusiccrit=0&pagenum=0&pagesize=25&lasthotcommentid=song_234369105_332733448_1564654091_1152921504868412103_1564667447&domain=qq.com&ct=24&cv=10101010")
    music.run()
