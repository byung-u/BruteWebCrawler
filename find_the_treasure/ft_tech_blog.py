#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
from requests import get, codes

from find_the_treasure.ft_sqlite3 import UseSqlite3


class TechBlog:
    def __init__(self, ft):
        self.sqlite3 = UseSqlite3('tech_blog')

    def spoqa(self, ft):
        send_msg = []
        base_url = 'https://spoqa.github.io/'
        url = 'https://spoqa.github.io/index.html'
        r = get(url)
        if r.status_code != codes.ok:
            ft.logger.error('[Tech blog spoqa] request error, code=%d', r.status_code)
            return
        soup = BeautifulSoup(r.text, 'html.parser')
        for p in soup.find_all(ft.match_soup_class(['posts'])):
            for auth in p.find_all(ft.match_soup_class(['post-author-info'])):
                post = auth.find(ft.match_soup_class(['post-title']))
                desc = auth.find(ft.match_soup_class(['post-description']))
                result_url = '%s%s' % (base_url, post.a['href'][1:])
                if self.sqlite3.already_sent_tech_blog(result_url):
                    # already exist
                    continue
                self.sqlite3.insert_tech_blog(result_url)

                result = '[Spoqa]\n%s\n%s' % (desc.string, result_url)
                result = ft.check_max_tweet_msg(result)
                send_msg.append(result)
        return send_msg

    def woowabros(self, ft):
        send_msg = []
        base_url = 'http://woowabros.github.io'
        url = 'http://woowabros.github.io/index.html'
        r = get(url)
        if r.status_code != codes.ok:
            ft.logger.error('[Tech blog woowabros] request error, code=%d', r.status_code)
            return
        soup = BeautifulSoup(r.text, 'html.parser')
        for l in soup.find_all(ft.match_soup_class(['list'])):
            for lm in l.find_all(ft.match_soup_class(['list-module'])):
                desc = lm.find(ft.match_soup_class(['post-description']))
                result_url = '[Woowabros]\n%s%s' % (base_url, lm.a['href'])
                if result_url is None or desc.string is None:
                    continue
                if self.sqlite3.already_sent_tech_blog(result_url):
                    # already exist
                    continue
                self.sqlite3.insert_tech_blog(result_url)

                result = '%s\n%s' % (desc.string, result_url)
                result = ft.check_max_tweet_msg(result)
                send_msg.append(result)
        return send_msg
