import pickle
from bs4 import BeautifulSoup
import os
import time
import sys
import logging as log
from . import engine
import random
import requests
from utils.time_conversion import secondstohour, countlasttime
from utils.change_color import red, green, yellow

class GainPageSize(engine.SpiderEngine):
    def __init__(self, config):
        self.config = config
        # all in args

        self.trytimes = config['trytimes']
        self.strSources = config['strSources']
        self.start = config['start']
        self.end = config['end']

        super(GainPageSize, self).__init__(config)

        self.end = len(self.results) if self.end == None or self.end > len(self.results) else self.end

        # spider_hassuccessed是程序刚开始时已经成功爬取的页数
        self.spider_hassuccessed = 0
        # pages_all是所有的页面数
        self.pages_all = 0
        for result in self.results[self.start:self.end]:
            self.pages_all += 1
            if result['page_size'] != 0:
                self.spider_hassuccessed += 1

    def start_spider(self):

        ip_gene = self.get_ip()
        # 用来标记当前页面尝试爬取次数
        flag = 0
        # 当前页面编号
        pagenow = 1
        idx = self.start
        t1 = time.time()
        # 很多情况下ip需要变化
        ipNeedChange = True

        while idx < self.end:
            company = self.results[idx]['company']
            if self.results[idx]['page_size'] == 0:
                if ipNeedChange:
                    # 获取ip
                    try:
                        ip = next(ip_gene)
                        # print(ip)
                        log.info(f" # {idx+1}-{pagenow}-{flag+1}: 提取IP成功: {ip['http']}")
                    except:
                        log.error(f"# {idx+1}-{pagenow}-{flag+1}: 提取IP失败")
                        ip_gene = self.get_ip()
                        continue

                # 爬取前需随机停顿1-3秒
                i = random.randint(1, 3)
                time.sleep(i)

                # 获取html
                html = self.get_html(idx, flag, applicant=company, ip=ip, strSources=self.strSources, pagenow=pagenow)
                if html == False:
                    ipNeedChange = True
                    flag = 0
                    continue
                html.encoding = 'utf-8'

                # 用BeautifulSoup解析网页
                soup = BeautifulSoup(html.text, 'lxml')

                # print(soup)
                try:
                    # 尝试找到页面中的页码最大序号
                    main_tb = soup.find("div", class_="next")
                    posion = main_tb.find('input')['onkeypress']
                    start = posion.find('zl_tz')+6
                    page_size = int(posion[start:-1])
                    self.results[idx]['page_size'] = page_size
                    # 顺便把首页内容也写入
                    self.results[idx]['patent'][1] = self.prase_page_cp_boxes(soup)
                except :
                    if soup.find("h1", class_="head_title") == None:
                        log.error(f"# {idx+1}-{pagenow}-{flag+1}: 没有您要查询的结果, {company} {ip['http']}")
                        ipNeedChange = False
                        flag += 1
                        # 如果对同一个页面连续尝试次数超过设置的trytimes,则判定该页爬取失败
                        if flag >= self.trytimes:
                            self.spider_all += 1
                            log.info(' # {}-{}-{}: {} {}\n'.format(idx+1, pagenow, flag, company, red('failed')))
                            idx += 1
                            flag = 0
                            t2 = time.time()
                            lasttime = countlasttime((t2-t1), self.spider_all, self.spider_hassuccessed, self.pages_all)
                            log.info(f' # 耗时{secondstohour(t2-t1)}, 成功爬取了{self.spider_success}/{self.spider_all}/{self.pages_all-self.spider_hassuccessed}家公司, 预计剩余{lasttime}\n')
                            ipNeedChange = True
                        continue
                    else:
                        log.error(f"# {idx+1}-{pagenow}-{flag+1}: 被认为是机器人")
                        flag = 0
                        ipNeedChange = True
                        continue

                log.info(' # {}-{}-{}: {}, {} 保存到文件 {}\n'.format(idx+1, pagenow, flag+1, company, green('success'), ip['http']))

                self.spider_success+=1
                self.spider_all+=1

                # 每成功爬取一个页面就保存到文件
                with open(self.pklfile, 'wb') as f:
                    pickle.dump(self.results, f)

                t2 = time.time()

                # 计算还需要消耗的时间
                lasttime = countlasttime((t2-t1), self.spider_all, self.spider_hassuccessed, self.pages_all)
                log.info(f' # 耗时{secondstohour(t2-t1)}, 成功爬取了{self.spider_success}/{self.spider_all}/{self.pages_all-self.spider_hassuccessed}家公司, 预计剩余{lasttime}\n')

                ipNeedChange = True
                idx += 1
                flag = 0
            else:
                log.info(' # {}-{}-{}: {} {}\n'.format(idx+1, pagenow, flag+1, company, yellow('has successed')))
                idx += 1
                flag = 0


