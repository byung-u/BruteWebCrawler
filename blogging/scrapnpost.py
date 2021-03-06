#!/usr/bin/env python3
import json
import os
import praw
import re
import urllib.request

from bs4 import BeautifulSoup
from datetime import datetime
from random import choice
from requests import get, codes
from selenium import webdriver
from seleniumrequests import Chrome

USER_AGENTS = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:11.0) Gecko/20100101 Firefox/11.0',
               'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:22.0) Gecko/20100 101 Firefox/22.0',
               'Mozilla/5.0 (Windows NT 6.1; rv:11.0) Gecko/20100101 Firefox/11.0',
               ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_4) AppleWebKit/536.5 (KHTML, like Gecko  ) '
                'Chrome/19.0.1084.46 Safari/536.5'),
               ('Mozilla/5.0 (Windows; Windows NT 6.1) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/  19.0.1084.46'
                'Safari/536.5'), )

ADSENSE_MIDDLE = '''<script async src="//pagead2.googlesyndication.com/pagead/js/adsbygoogle.js"></script>
<!-- insert middle -->
<ins class="adsbygoogle"
     style="display:inline-block;width:728px;height:90px"
     data-ad-client="ca-pub-2477248594987452"
     data-ad-slot="3727980969"></ins>
<script>
(adsbygoogle = window.adsbygoogle || []).push({});
</script>'''


def match_soup_class(target, mode='class'):
    def do_match(tag):
        classes = tag.get(mode, [])
        return all(c in classes for c in target)
    return do_match


def get_realestate_daum():
    url = 'http://realestate.daum.net/news'

    r = get(url)
    if r.status_code != codes.ok:
        print('[daum] request error')
        return None

    result = ""
    news_url = []
    soup = BeautifulSoup(r.text, 'html.parser')
    for f in soup.find_all(match_soup_class(['link_news'])):
        news_url = []
        try:
            href = f['href']
        except TypeError:
            continue
        if href in news_url:
            continue
        news_url.append(href)

        title = f.text
        title = title.replace("'", "").replace('"', '').replace('·', ',')
        result = '%s<br><a href="%s" target="_blank">%s</a>' % (result, href, title)
    return result


def get_realestate_mbn():
    result = ""
    url = 'http://news.mk.co.kr/newsList.php?sc=30000020'
    r = get(url)
    if r.status_code != codes.ok:
        print('[mbn] request error')
        return None

    soup = BeautifulSoup(r.content.decode('euc-kr', 'replace'), 'html.parser')
    news_url = []
    for f in soup.find_all(match_soup_class(['art_list'])):
        if f.a['href'] in news_url:
            continue
        news_url.append(f.a['href'])

        href = f.a['href']
        title = f.a['title']
        title = title.replace("'", "").replace('"', '').replace('·', ',')
        result = '%s<br><a href="%s" target="_blank">%s</a>' % (result, href, title)
    return result


def get_realestate_hankyung():
    result = ""
    url = 'http://land.hankyung.com/'
    r = get(url)
    if r.status_code != codes.ok:
        print('[hankyung] request error')
        return None

    soup = BeautifulSoup(r.content.decode('euc-kr', 'replace'), 'html.parser')
    news_url = []

    sessions = soup.select('div > h2 > a')
    for s in sessions:
        if s['href'] in news_url:
            continue
        if s['href'] == 'http://www.hankyung.com/news/kisarank/':
            continue
        news_url.append(s['href'])

        href = s['href']
        title = s.text.strip()
        title = title.replace("'", "").replace('"', '').replace('·', ',')
        result = '%s<br><a href="%s" target="_blank">%s</a>' % (result, href, title)
    return result


def get_realestate_naver():
    result = ""
    base_url = 'http://land.naver.com'
    url = 'http://land.naver.com/news/headline.nhn'
    r = get(url)
    if r.status_code != codes.ok:
        print('[hankyung] request error')
        return None

    soup = BeautifulSoup(r.text, 'html.parser')
    news_url = []

    sessions = soup.select('div > div > div > div > div > dl > dt > a')
    # content > div.spot_headline > div.section_news > div > div.news_area.NE\3d a\3a hla > div:nth-child(2) > dl > dt > a
    for s in sessions:
        if s['href'] in news_url:
            continue
        href = '%s%s' % (base_url, s['href'])
        news_url.append(href)
        title = s.text.strip()
        title = title.replace("'", "").replace('"', '').replace('·', ',')
        result = '%s<br><a href="%s" target="_blank">%s</a>' % (result, href, title)
    sessions = soup.select('div > ul > li > dl > dt > a')
    # content > div.section_headline.NE\3d a\3a mnn > ul > li:nth-child(6) > dl > dt:nth-child(2) > a

    for s in sessions:
        if s['href'] in news_url:
            continue
        if len(s.text) == 0:
            continue
        href = '%s%s' % (base_url, s['href'])
        news_url.append(href)
        title = s.text.strip()
        title = title.replace("'", "").replace('"', '').replace('·', ',')
        result = '%s<br><a href="%s" target="_blank">%s</a>' % (result, href, title)

    return result


def tistory_post(token, title, content, category):
    webdriver = Chrome()
    response = webdriver.request('POST', 'https://www.tistory.com/apis/post/write', data={"access_token": token, "blogName": "scrapnpost", 'title': title, 'content': content, 'category': category, 'visibility': '2'})
    webdriver.quit()
    print(response)


def get_tistory_token():
    # http://www.tistory.com/guide/api/index
    chromedriver_path = os.environ.get('CHROMEDRIVER_PATH')
    driver = webdriver.Chrome(chromedriver_path)
    driver.implicitly_wait(3)
    driver.get('https://www.tistory.com/auth/login?redirectUrl=http%3A%2F%2Fwww.tistory.com%2F')
    # <input type="email" id="loginId" name="loginId" class="tf_g" value="" placeholder="이메일 아이디" required="">
    tid = os.environ.get('TISTORY_ID')
    tpw = os.environ.get('TISTORY_PAW')
    driver.find_element_by_name('loginId').send_keys(tid)
    # <input type="password" id="loginPw" name="password" class="tf_g" placeholder="비밀번호" required="">
    driver.find_element_by_name('password').send_keys(tpw)
    driver.find_element_by_xpath('//*[@id="authForm"]/fieldset/div/button').click()

    client_id = os.environ.get('TISTORY_CLIENT_ID')
    redirect = os.environ.get('TISTORY_REDIRECT')

    req_url = 'https://www.tistory.com/oauth/authorize/?client_id=%s&redirect_uri=%s&response_type=token' % (client_id, redirect)
    driver.get(req_url)

    ################################################################################
    # XXX: 중요
    # 티스토리는 브라우져 인증이 필요함
    # 맨처음 시도할 때는 아래의 코드의 주석을 풀고 한번 해줘야함
    # driver.find_element_by_xpath('//*[@id="contents"]/div[4]/button[1]').click()
    ################################################################################
    redirect_url = driver.current_url
    print(redirect_url)
    temp = re.split('access_token=', redirect_url)
    token = re.split('&state=', temp[1])[0]
    driver.quit()
    return token


def get_financial_einfomax():
    result = ""
    base_url = 'http://news.einfomax.co.kr/news'
    url = 'http://news.einfomax.co.kr/news/articleList.html?sc_section_code=S1N16&view_type=sm'
    r = get(url)
    if r.status_code != codes.ok:
        print('[einfomax] request error')
        return None

    soup = BeautifulSoup(r.content.decode('euc-kr', 'replace'), 'html.parser')
    news_url = []

    for f in soup.find_all(match_soup_class(['ArtList_Title'])):
        try:
            href = f.a['href']
        except TypeError:
            continue
        if href in news_url:
            continue
        news_url.append(href)
        title = f.a.text
        title = title.replace("'", "").replace('"', '').replace('·', ',')
        result = '%s<br><a href="%s/%s" target="_blank">%s</a>' % (result, base_url, href, title)
    return result


def get_financial_chosun():
    result = ""
    url = 'http://biz.chosun.com/index.html'
    r = get(url)
    if r.status_code != codes.ok:
        print('[chosun] request error')
        return None

    soup = BeautifulSoup(r.content.decode('utf-8', 'replace'), 'html.parser')
    news_url = []
    for f in soup.find_all(match_soup_class(['mc_art_lst'])):
        for li in f.find_all('li'):
            if li.a['href'].endswith('main_hot3'):
                # 경제, 금융: main_hot1, main_hot2
                break

            try:
                href = li.a['href']
            except TypeError:
                continue
            if href in news_url:
                continue
            news_url.append(href)
            title = li.a.text.strip()
            title = title.replace("'", "").replace('"', '').replace('·', ',')
            result = '%s<br><a href="%s" target="_blank">%s</a>' % (result, href, title)
    return result


def get_financial_joins():
    result = ""
    base_url = 'http://news.joins.com'
    url = 'http://news.joins.com/money?cloc=joongang|home|section3'
    r = get(url)
    if r.status_code != codes.ok:
        print('[joins] request error')
        return None

    soup = BeautifulSoup(r.content.decode('utf-8', 'replace'), 'html.parser')
    news_url = []
    for f in soup.find_all(match_soup_class(['default_realtime'])):

        for li in f.find_all('li'):
            try:
                href = li.a['href']
            except TypeError:
                continue
            if href in news_url:
                continue
            news_url.append(href)
            title = ' '.join(li.text.strip().split()[1:-2])
            title = title.replace("'", "").replace('"', '').replace('·', ',')
            result = '%s<br><a href="%s%s" target="_blank">%s</a>' % (result, base_url, href, title)
    return result


def get_reddit(category='it'):
    result = ''
    client_id = os.environ.get('REDDIT_CLIENT_ID')
    client_secret = os.environ.get('REDDIT_CLIENT_SECRET')
    reddit_id = os.environ.get('REDDIT_ID')
    reddit_pw = os.environ.get('REDDIT_PAW')
    reddit = praw.Reddit(client_id=client_id,
                         client_secret=client_secret, password=reddit_pw,
                         user_agent='USERAGENT', username=reddit_id)

    if category == 'it':
        # for submission in reddit.subreddit('redditdev+learnpython').top('all'):
        for idx, sub in enumerate(reddit.subreddit('python+programming').hot(limit=30)):
            # temp = '<a href="%s">%d. %s</a>' % (sub.url, idx + 1, sub.title)
            temp = '<a href="%s" target="_blank">[%d] %s (⬆ %s)</a><br><pre>%s</pre><br>' % (sub.url, idx + 1, sub.title, sub.score, naver_papago_smt(sub.title))
            result = '%s<br>%s' % (result, temp)

        content = '<font color="red">[레딧(Reddit) Python & Programming]</font>%s<br>' % result
    elif category == 'korea':
        for idx, sub in enumerate(reddit.subreddit('korea').hot(limit=60)):
            temp = '<a href="%s" target="_blank">[%d] %s (⬆ %s)</a><br><pre>%s</pre><br>' % (sub.url, idx + 1, sub.title, sub.score, naver_papago_smt(sub.title))
            result = '%s<br>%s' % (result, temp)

        content = '<font color="red">[레딧(Reddit) Korea]</font>%s<br>' % result
    return content


def get_hacker_news():
    result = ''
    # p=1, rank 1~30
    # p=2, rank 30~60 ...
    for i in range(1, 2):
        url = 'https://news.ycombinator.com/news?p=%d' % i
        r = get(url)
        if r is None:
            return
        soup = BeautifulSoup(r.text, 'html.parser')
        for f in soup.find_all(match_soup_class(['athing'])):
            title = f.text.strip()
            for s in f.find_all(match_soup_class(['storylink'])):
                href = s['href']
                temp = '<a href="%s" target="_blank">%s</a><br><pre>%s</pre><br>' % (href, title, naver_papago_smt(title))
                result = '%s<br>%s' % (result, temp)
    content = '<font color="red">[해커뉴스(Hacker News)]</font>%s<br>' % result
    return content


def get_realestate_hani():
    result = '<font color="blue">[한겨례 부동산 뉴스]</font><br>'
    base_url = 'http://www.hani.co.kr'
    url = ' http://www.hani.co.kr/arti/economy/property/home01.html'
    r = get(url)
    soup = BeautifulSoup(r.content.decode('utf-8', 'replace'), 'html.parser')
    for article in soup.find_all(match_soup_class(['article-area'])):
        href = '%s%s' % (base_url, article.a['href'])
        article = article.text.strip().split('\n')
        # print(href, article[0])
        result = '%s<br><a href="%s" target="_blank">%s</a>' % (result, href, article[0])
    return result


def get_realestate_nocut():
    result = '<font color="blue">[노컷뉴스 부동산 뉴스]</font><br>'
    base_url = 'http://www.nocutnews.co.kr'
    url = 'http://www.nocutnews.co.kr/news/list?c1=203&c2=204&ltype=1'
    r = get(url)
    soup = BeautifulSoup(r.content.decode('utf-8', 'replace'), 'html.parser')
    news = soup.find(match_soup_class(['newslist']))
    for dt in news.find_all('dt'):
        href = '%s%s' % (base_url, dt.a['href'])
        # print(href, dt.text.strip())
        result = '%s<br><a href="%s" target="_blank">%s</a>' % (result, href, dt.text.strip())
    return result


def get_realestate_nate(cur_time):
    result = '<font color="blue">[네이트 부동산 뉴스]</font><br>'
    url = 'http://news.nate.com/subsection?cate=eco03&mid=n0303&type=c&date=%s&page=1' % cur_time
    r = get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    for news in soup.find_all(match_soup_class(['mlt01'])):
        span = news.find('span', attrs={'class': 'tb'})
        title = span.find('strong', attrs={'class': 'tit'})
        result = '%s<br><a href="%s" target="_blank">%s</a>' % (result, news.a['href'], title.text)
    return result


def get_realestate_donga():
    result = '<font color="blue">[동아일보 부동산 뉴스]</font><br>'
    url = 'http://news.donga.com/List/Economy/RE'
    r = get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    for alist in soup.find_all(match_soup_class(['articleList'])):
        title = alist.find('span', attrs={'class': 'tit'})
        result = '%s<br><a href="%s" target="_blank">%s</a>' % (result, alist.a['href'], title.text.strip())
    return result


def realestate_news1():
    daum_news = get_realestate_daum()
    # print('[DAUm]<br>', daum_news)
    mbn_news = get_realestate_mbn()
    # print('[MBN]<br>', mbn_news)
    hankyung_news = get_realestate_hankyung()
    # print('[HanKyung]<br>', hankyung_news)
    naver_news = get_realestate_naver()
    # print('[Naver]<br>', naver)

    content = '<font color="red">[Daum]</font>%s<br><br><font color="red">[매일경제]</font>%s<br><br><font color="red">[한국경제]</font>%s<br><br><font color="red">[Naver]</font>%s<br><br>' % ( daum_news, mbn_news, hankyung_news, naver_news)
    return content


def realestate_news2(cur_time):
    result = ''

    content = get_realestate_hani()
    result = '%s<br><br><br>%s' % (result, content)
    content = get_realestate_donga()
    result = '%s<br><br><br>%s' % (result, content)
    content = get_realestate_nocut()
    result = '%s<br><br><br>%s' % (result, content)
    content = get_realestate_nate(cur_time)
    result = '%s<br><br><br>%s' % (result, content)

    return result


def financial_news():
    einfomax = get_financial_einfomax()
    # print(einfomax)
    chosun = get_financial_chosun()
    # print(chosun)
    joins = get_financial_joins()
    # print(joins)

    content = '<font color="red">[연합인포맥스]</font>%s<br><font color="red">[조선일보]</font>%s<br><font color="red">[중앙일보]</font>%s<br>' % (einfomax, chosun, joins)
    return content


def naver_papago_nmt(words):
    client_id = os.environ.get('NAVER_CLIENT_ID')
    client_secret = os.environ.get('NAVER_CLIENT_SECRET')
    encText = urllib.parse.quote(words)
    data = 'source=en&target=ko&text=' + encText
    url = 'https://openapi.naver.com/v1/papago/n2mt'
    request = urllib.request.Request(url)
    request.add_header('X-Naver-Client-Id', client_id)
    request.add_header('X-Naver-Client-Secret', client_secret)
    response = urllib.request.urlopen(request, data=data.encode("utf-8"))
    rescode = response.getcode()
    if(rescode == 200):
        response_body = response.read()
        translated = json.loads(response_body.decode('utf-8'))
        return (translated['message']['result']['translatedText'])
    else:
        print('Error Code:' + rescode)


def naver_papago_smt(words):
    client_id = os.environ.get('NAVER_CLIENT_ID')
    client_secret = os.environ.get('NAVER_CLIENT_SECRET')
    encText = urllib.parse.quote(words)
    data = 'source=en&target=ko&text=' + encText
    url = "https://openapi.naver.com/v1/language/translate"
    request = urllib.request.Request(url)
    request.add_header('X-Naver-Client-Id', client_id)
    request.add_header('X-Naver-Client-Secret', client_secret)
    try:
        response = urllib.request.urlopen(request, data=data.encode("utf-8"))
    except urllib.error.HTTPError as e:
        print('urlopen failed', str(e))
        return ' '

    rescode = response.getcode()
    if(rescode == 200):
        response_body = response.read()
        translated = json.loads(response_body.decode('utf-8'))
        return (translated['message']['result']['translatedText'])
    else:
        print('Error Code:' + rescode)
        return ' '


def get_exhibit_image(href):
    try:
        page = urllib.request.urlopen(href)
    except:
        return None
    base_url = href.split('/')
    base_url = '%s//%s' % (base_url[0], base_url[2])

    soup = BeautifulSoup(page, 'html.parser')
    for img in soup.find_all('img', {'src': re.compile(r'(jpe?g)|(png)$')}):
        if img['src'].find('logo') != -1:
            if img['src'].find('http') != -1:
                return img['src']
            else:
                img_link = '%s/%s' % (base_url, img['src'])
                return img_link
    else:
        icon_link = soup.find("link", rel="shortcut icon")
        try:
            icon_image_link = icon_link['href']
            return icon_image_link
        except TypeError:
            return None


def get_oversea_exhibition():
    result = ''
    now = datetime.now()
    yesterday = '%4d%02d%02d' % (now.year, now.month, now.day - 1)
    today = '%4d%02d%02d' % (now.year, now.month, now.day)
    key = os.environ.get('KOTRA_API_KEY')
    request_url = 'http://www.gep.or.kr/rest/overseasExhibition?serviceKey=%s&from=%s&to=%s&pageRows=20&pageNumber=1&type=json' % (key, yesterday, today)
    req = urllib.request.Request(request_url)
    try:
        res = urllib.request.urlopen(req)
    except UnicodeEncodeError:
        print('[OpenAPI] UnicodeEncodeError')
        return

    data = res.read().decode('utf-8')
    soup = BeautifulSoup(data, 'html.parser')
    js = json.loads(str(soup))
    for exhibit in js['overseasExhibitionListArray']:

        href = exhibit['homepage']
        if not href.startswith('http://'):
            href = 'http://%s' % href

        img_link = get_exhibit_image(href)
        if img_link is None:
            img_link = '#'

        exitem = exhibit['exhibitionItem']
        exitem = exitem.replace(r'\r', '<br>').replace(r'\r\n', '<br>').replace('\\r\\n', '<br>')

        temp = '<a href="%s" target="_blank"><font color="red">%s(%s)</font></a><br>전시항목: %s<br>일정: %s<br>스폰서: %s<br>주소: %s  ☎ :%s (%s %s)<br><a href="mailto:%s">Email: %s</a> (%s년 부터 %s 개최)<br><center><a href="%s" target="_blank"> <img border="0" src="%s" width="150" height="100"></a></center><br>' % (
               href, exhibit['exhibitionTitleKor'], exhibit['exhibitionTitleEng'],
               exitem, exhibit['openingTerm'], exhibit['sponsor'],
               exhibit['address'], exhibit['telephone'],
               exhibit['openingCountry'], exhibit['openingCity'],
               exhibit['email'], exhibit['email'],
               exhibit['firstOpeningYear'], exhibit['openingCycle'],
               href, img_link)
        # print(temp)
        result = '%s<br>%s' % (result, temp)
    return result


def get_sacticket():  # 예술의 전당
    result = '<h2>예술의 전당</h2>'
    driver = webdriver.PhantomJS()
    driver.implicitly_wait(3)

    url = 'https://www.sacticket.co.kr/SacHome/ticket/reservation'
    driver.get(url)
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    for p in soup.find_all(match_soup_class(['ticket_list_con'])):
        for poster in p.find_all(match_soup_class(['poster'])):
            for pa in poster.find_all('img'):
                thumbnail = (pa['src'])
        if thumbnail.endswith('no_result.png'):
            continue
        # print(thumbnail)

        for content in p.find_all(match_soup_class(['content'])):
            try:
                c_info = content.a['onclick'].split("'")
                page_id = c_info[1]
                page_type = c_info[3]
                if page_type == 'E':
                    category = "[전시]"
                    link = 'https://www.sacticket.co.kr/SacHome/exhibit/detail?searchSeq=%s' % page_id
                elif page_type == 'P':
                    category = "[공연]"
                    link = 'https://www.sacticket.co.kr/SacHome/perform/detail?searchSeq=%s' % page_id
                else:
                    continue

                for idx, ca in enumerate(content.find_all('a')):
                    if idx == 0:
                        title = ca.text
                    elif idx == 1:
                        if ca.text != '무료':
                            price = '유료'
                        else:
                            price = ca.text

                temp = '<font color="red">%s</font><br>%s %s<br><br><center><a href="%s" target="_blank"> <img border="0" src="%s" width="150" height="150"></a></center>' % (title, category, price, link, thumbnail)
                result = '%s<br>%s' % (result, temp)
            except:
                continue
    driver.quit()
    return result


def get_coex_exhibition():
    result = '<h2>코엑스</h2>'
    url = 'http://www.coex.co.kr/blog/event_exhibition?list_type=list'
    r = get(url)
    if r is None:
        return
    soup = BeautifulSoup(r.text, 'html.parser')
    exhibition_url = 'http://www.coex.co.kr/blog/event_exhibition'
    for a in soup.find_all('a', href=True):
        thumbnail = ''
        if a['href'].startswith(exhibition_url) is False:
            continue

        for img in a.find_all('img'):
            thumbnail = img['src']

        if len(thumbnail) == 0:
            continue

        for idx, li in enumerate(a.find_all('li')):
            if idx % 5 == 0:
                category = li.text
            elif idx % 5 == 1:
                spans = li.find_all('span', attrs={'class': 'subject'})
                for span in spans:
                    subject = span.text
                spans = li.find_all('span', attrs={'class': 'url'})
                for span in spans:
                    url = span.text
                url = 'http://%s' % url
            elif idx % 5 == 2:
                period = li.text
            elif idx % 5 == 3:
                price = li.text
            elif idx % 5 == 4:
                location = li.text
                temp = '<a href="%s" target="_blank"><font color="red">%s (%s)</font></a><br>%s, %s, %s<br><br><center><a href="%s" target="_blank"> <img border="0" src="%s" width="150" height="150"></a></center>' % (url, subject, category, period, location, price, url, thumbnail)
                result = '%s<br>%s' % (result, temp)
    return result


def get_aladin_book(query_type='ItemNewAll', max_result=30):  # max 50
    tkey = os.environ.get('ALADIN_TTB_KEY')
    url = 'http://www.aladin.co.kr/ttb/api/ItemList.aspx?ttbkey=%s&QueryType=%s&MaxResults=%d&start=1&SearchTarget=Book&output=js&Cover=big&Version=20131101' % (tkey, query_type, max_result)

    content = ''
    r = get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    books = json.loads(str(soup))

    for book in books['item']:
        title = book['title']
        link = book['link']
        desc = book['description']
        img_link = book['cover']
        publisher = book['publisher']
        priceSales = book['priceSales']
        # priceStandard = book['priceStandard']
        categoryName = book['categoryName']
        author = book['author']

        temp = '<a href="%s" target="_blank"><font color="red">%s</font></a><br>%s, %s, %s 원<br>%s<br><br>%s<br><br><center><a href="%s" target="_blank"> <img border="0" align="middle" src="%s" width="200" height="250"></a></center>' % (link, title, author, publisher, priceSales, categoryName, desc, link, img_link)
        content = '%s<br><br>%s' % (content, temp)
    return content


def get_kdi_research():  # 한국개발연구원
    result = ''
    thema = {'A': '거시/금융',
             'B': '재정/복지',
             'C': '노동/교육',
             'D': '국제/무역',
             'E': '산업조직',
             'F': '경제발전/성장',
             'G': '북한경제/경제체계',
             'H': '농업/환경/자원',
             'I': '지역경제',
             'J': '기타'}

    base_url = 'http://www.kdi.re.kr'
    for t, value in thema.items():
        result = '%s<br><br><strong><font color="red">[%s]</font></strong>' % (result, value)
        url = 'http://www.kdi.re.kr/research/subjects_list.jsp?tema=%s' % t
        r = get(url)
        soup = BeautifulSoup(r.text, 'html.parser')
        sessions = soup.select('li > div > a')
        # li.Js_AjaxParents:nth-child(1) > div:nth-child(1) > a:nth-child(3)
        for s in sessions:
            result_url = '%s%s' % (base_url, s['href'])
            result = '%s<br><a href="%s" target="_blank">%s</a>' % (result, result_url, s.text.strip())
    return result


def get_visit_korea():  # 대한민국 구석구석 행복여행
    result = ''
    base_url = 'http://korean.visitkorea.or.kr/kor/bz15/where/festival'
    url = 'http://korean.visitkorea.or.kr/kor/bz15/where/festival/festival.jsp'
    r = get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    for s in soup.find_all(match_soup_class(['item'])):
        if s.h3 is None:
            continue
        result_url = '%s/%s' % (base_url, s.a['href'])
        desc = repr(s.h3)[4: -6]
        img = s.find('img')
        thumbnail = img['src']
        for info in s.find_all(match_soup_class(['info2'])):
            for span in info.find_all('span', {'class': 'date'}):
                result = '%s<br><strong><a href="%s" target="_blank"><font color="red">%s</font></a></strong><br>%s<br>' % (
                         result, result_url, desc, span.text)
                result = '%s<center><a href="%s" target="_blank"> <img border="0" src="%s" width="150" height="150"></a></center>' % (
                         result, result_url, thumbnail)
                # print(result_url, desc, span.text)
                break
    return result


def get_domestic_exhibition():
    content = ''
    coex = get_coex_exhibition()
    content = '%s<br><br>%s' % (content, coex)

    sac = get_sacticket()
    content = '%s<br><br>%s' % (content, sac)

    return content


def get_opinion_hani():
    result = '<font color="blue">[한겨례 사설, 칼럼]</font>'
    base_url = 'http://www.hani.co.kr'
    url = 'http://www.hani.co.kr/arti/opinion/home01.html?_fr=mt0'
    r = get(url)
    soup = BeautifulSoup(r.content.decode('utf-8', 'replace'), 'html.parser')
    for article in soup.find_all(match_soup_class(['article'])):
        # print(article)
        for li in article.find_all('li'):
            li_href = '%s%s' % (base_url, li.a['href'])
            li_text = li.text.strip().split('\n')
            result = '%s<br><a href="%s" target="_blank">%s</a>' % (result, li_href,  li_text[0])
        href = '%s%s' % (base_url, article.a['href'])
        article = article.text.strip().split('\n')
        # print(href, article[0])
        result = '%s<br><a href="%s" target="_blank">%s</a>' % (result, href, article[0])
    return result


def get_opinion_donga():
    result = '<font color="blue">[동아일보 사설, 칼럼]</font>'
    url = 'http://news.donga.com/Column/'
    r = get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    for alist in soup.find_all(match_soup_class(['articleList'])):
        title = alist.find('span', attrs={'class': 'tit'})
        result = '%s<br><a href="%s" target="_blank">%s</a>' % (result, alist.a['href'], title.text.strip())
    return result


def get_opinion_mbn():
    result = '<font color="blue">[매일경제 사설, 칼럼]</font>'
    base_url = 'http://opinion.mk.co.kr/'
    url = 'http://opinion.mk.co.kr/list.php?sc=30500003'
    r = get(url)
    soup = BeautifulSoup(r.content.decode('euc-kr', 'replace'), 'html.parser')
    for f in soup.find_all(match_soup_class(['article_list'])):
        for dt in f.find_all('dt'):
            href = '%s%s' % (base_url, dt.a['href'])
            # print(href, dt.text)
            result = '%s<br><a href="%s" target="_blank">%s</a>' % (result, href, dt.text)
    return result


def get_opinion_hankyung():
    result = '<font color="blue">[한국경제 사설, 칼럼]</font>'
    url = 'http://news.hankyung.com/opinion'
    r = get(url)
    soup = BeautifulSoup(r.content.decode('utf-8', 'replace'), 'html.parser')
    for inner_list in soup.find_all(match_soup_class(['inner_list'])):
        for li in inner_list.find_all('li'):
            li_title = li.find('strong', attrs={'class': 'tit'})
            if li_title is None:
                break
            result = '%s<br><a href="%s" target="_blank">%s</a>' % (result, li.a['href'], li_title.text)

        title = inner_list.find('strong', attrs={'class': 'tit'})
        result = '%s<br><a href="%s" target="_blank">%s</a>' % (result, inner_list.a['href'], title.text)
    return result


def get_opinion_chosun():
    result = '<font color="blue">[조선일보 사설, 칼럼]</font>'
    base_url = 'http://biz.chosun.com'
    url = 'http://biz.chosun.com/svc/list_in/list.html?catid=1F&op_s'
    r = get(url)
    soup = BeautifulSoup(r.content.decode('utf-8', 'replace'), 'html.parser')
    for f in soup.find_all(match_soup_class(['list_vt'])):
        for li in f.find_all('li'):
            dt = li.find('dt')
            href = '%s%s' % (base_url, li.a['href'])
            result = '%s<br><a href="%s" target="_blank">%s</a>' % (result, href, dt.a.text)
    return result


def get_opinion_joins():
    result = '<font color="blue">[중앙일보 사설, 칼럼]</font>'
    base_url = 'http://news.joins.com'
    url = 'http://news.joins.com/opinion?cloc=joongang|home|section1'
    r = get(url)
    soup = BeautifulSoup(r.content.decode('utf-8', 'replace'), 'html.parser')
    for head in soup.find_all(match_soup_class(['opinion_home_headline'])):
        for li in head.find_all('li'):
            href = '%s%s' % (base_url, li.a['href'])
            result = '%s<br><a href="%s" target="_blank">%s</a>' % (result, href, li.a.text)
            # print(li.a['href'], li.a.text)

    for today in soup.find_all(match_soup_class(['opinion_home_today'])):
        for li in today.find_all('li'):
            href = '%s%s' % (base_url, li.a['href'])
            title = li.find('strong', attrs={'class': 'mg'})
            result = '%s<br><a href="%s" target="_blank">%s</a>' % (result, href, title.text)
            # print(li.a['href'], title.text)
    return result


def get_opinion_hankook():
    result = '<font color="blue">[한국일보 사설, 칼럼]</font>'
    base_url = 'http://www.hankookilbo.com'
    url = 'http://www.hankookilbo.com/op.aspx'
    r = get(url)
    soup = BeautifulSoup(r.content.decode('utf-8', 'replace'), 'html.parser')
    for col in soup.find_all(match_soup_class(['editorial_column'])):
        for li in col.find_all('li'):
            href = '%s%s' % (base_url, li.a['href'])
            result = '%s<br><a href="%s" target="_blank">%s</a>' % (result, href, li.a.text)
    return result


def get_opinion_gyunghyang():
    result = '<font color="blue">[경향신문 사설, 칼럼]</font>'
    url = 'http://news.khan.co.kr/kh_news/khan_art_list.html?code=990000'
    r = get(url, headers={'User-Agent': choice(USER_AGENTS)})
    soup = BeautifulSoup(r.content.decode('euc-kr', 'replace'), 'html.parser')
    for news_list in soup.find_all(match_soup_class(['news_list'])):
        for li in news_list.find_all('li'):
            try:
                title = li.a['title']
                result = '%s<br><a href="%s" target="_blank">%s</a>' % (result, li.a['href'], title.strip())
                # print(li.a['href'], title)
            except KeyError:
                title = li.text.split('\n')
                result = '%s<br><a href="%s" target="_blank">%s</a>' % (result, li.a['href'], title[1].strip())
                # print(li.a['href'], title[1])
    return result


def get_opinion_kookmin(cur_time):
    result = '<font color="blue">[국민일보 사설]</font>'
    base_url = 'http://news.kmib.co.kr/article'
    url = 'http://news.kmib.co.kr/article/list.asp?sid1=opi&sid2=&sdate=%s' % cur_time
    r = get(url, headers={'User-Agent': choice(USER_AGENTS)})
    soup = BeautifulSoup(r.content.decode('euc-kr', 'replace'), 'html.parser')
    for nws_list in soup.find_all(match_soup_class(['nws_list'])):
        for dl in nws_list.find_all('dl'):
            if dl.text == '등록된 기사가 없습니다.':
                result = '%s<br>현재 %s<br>' % (result, dl.text)
                return result
            dt = dl.find('dt')
            href = '%s/%s' % (base_url, dt.a['href'])
            result = '%s<br><a href="%s" target="_blank">%s</a>' % (result, href, dt.a.text)
    return result


def get_opinion_segye():
    result = '<font color="blue">[세계일보 사설, 칼럼]</font>'
    base_url = 'http://www.segye.com'
    url = 'http://www.segye.com/opinion'
    r = get(url, headers={'User-Agent': choice(USER_AGENTS)})
    soup = BeautifulSoup(r.content.decode('utf-8', 'replace'), 'html.parser')
    for title_1 in soup.find_all(match_soup_class(['title_1'])):
        href = '%s%s' % (base_url, title_1.a['href'])
        result = '%s<br><a href="%s" target="_blank">%s</a>' % (result, href, title_1.a.text)
    for title_2 in soup.find_all(match_soup_class(['title_2'])):
        href = '%s%s' % (base_url, title_2.a['href'])
        # print(href, title_2.a.text)
        result = '%s<br><a href="%s" target="_blank">%s</a>' % (result, href, title_2.a.text)
    return result


def get_opinion_moonhwa():
    result = '<font color="blue">[문화일보 사설, 칼럼]</font>'
    url = 'http://www.munhwa.com/news/section_list.html?sec=opinion&class=0'
    r = get(url, headers={'User-Agent': choice(USER_AGENTS)})
    soup = BeautifulSoup(r.content.decode('euc-kr', 'replace'), 'html.parser')
    for d14b_333 in soup.find_all(match_soup_class(['d14b_333'])):
        result = '%s<br><a href="%s" target="_blank">%s</a>' % (result, d14b_333['href'], d14b_333.text)
    return result


def opinion_news(cur_time):
    result = '언론사 목록<br><strong> 경향신문, 국민일보, 동아일보, 매일경제, 문화일보, 세계신문, 중앙일보, 조선일보, 한겨례, 한국경제, 한국일보</strong><br><br>'

    content = get_opinion_gyunghyang()  # 경향신문
    result = '%s<br><br><br>%s' % (result, content)

    content = get_opinion_kookmin(cur_time)  # 국민일보
    result = '%s<br><br><br>%s' % (result, content)

    content = get_opinion_donga()  # 동아일보
    result = '%s<br><br><br>%s' % (result, content)

    content = get_opinion_mbn()  # 매일경제
    result = '%s<br><br><br>%s' % (result, content)

    # add advertise
    # result = '%s<br><br>%s<br><br>' % (result, ADSENSE_MIDDLE)

    content = get_opinion_moonhwa()  # 문화일보
    result = '%s<br><br><br>%s' % (result, content)

    content = get_opinion_segye()  # 세계신문
    result = '%s<br><br><br>%s' % (result, content)

    content = get_opinion_joins()  # 중앙일보
    result = '%s<br><br><br>%s' % (result, content)

    content = get_opinion_chosun()  # 조선일보
    result = '%s<br><br><br>%s' % (result, content)

    # add advertise
    # result = '%s<br><br>%s<br><br>' % (result, ADSENSE_MIDDLE)

    content = get_opinion_hani()  # 한겨례
    result = '%s<br><br><br>%s' % (result, content)

    content = get_opinion_hankyung()  # 한국경제
    result = '%s<br><br><br>%s' % (result, content)

    content = get_opinion_hankook()  # 한국일보
    result = '%s<br><br><br>%s' % (result, content)

    return result


def once_a_4days(now, cur_time, token):
    # every 4 days
    if now.day % 4 == 1:
        title = '[%s] 전체 신간 리스트 - 국내도서 30권(알라딘)' % cur_time
        content = get_aladin_book()
        tistory_post(token, title, content, '765395')

        title = '[%s] 주목할 만한 신간 리스트 - 국내도서 20권(알라딘)' % cur_time
        content = get_aladin_book('ItemNewSpecial', 20)
        tistory_post(token, title, content, '765395')

        title = '[%s] 베스트셀러 - 30권(알라딘)' % cur_time
        content = get_aladin_book('Bestseller', 30)
        tistory_post(token, title, content, '765395')
    elif now.day % 4 == 2:
        content = get_oversea_exhibition()
        title = '[%s] 해외 전시 정보' % cur_time
        tistory_post(token, title, content, '765395')
    elif now.day % 4 == 3:
        title = '[%s] 코엑스, 예술의 전당(공연, 전시)' % cur_time
        content = get_domestic_exhibition()
        tistory_post(token, title, content, '765395')
    else:
        title = '[%s] 국내 축제, 행사 일정 (대한민국 구석구석 행복여행)' % cur_time
        content = get_visit_korea()  # 대한민국 구석구석 행복여행
        tistory_post(token, title, content, '765395')


def weekday(cur_time, token):
    title = '[%s] 부동산 뉴스 모음(Daum, 매일경제, 한국경제, Naver)' % cur_time
    content = realestate_news1()
    tistory_post(token, title, content, '765348')

    title = '[%s] 부동산 뉴스 모음(한겨례, 동아일보, 노컷뉴스, Nate)' % cur_time
    content = realestate_news2(cur_time)
    tistory_post(token, title, content, '765348')

    title = '[%s] 경제 금융 뉴스 모음(연합인포맥스, 조선일보, 중앙일보)' % cur_time
    content = financial_news()
    tistory_post(token, title, content, '765357')

    content = get_reddit('korea')
    title = '[%s] Reddit에 올라온 한국 관련 소식' % cur_time
    tistory_post(token, title, content, '765357')  # economy

    content = get_reddit()
    title = '[%s] Reddit (Programming & Python)' % cur_time
    tistory_post(token, title, content, '765668')  # IT news

    content = get_hacker_news()
    title = '[%s] Hacker News (Ranking 1~30)' % cur_time
    tistory_post(token, title, content, '765668')  # IT news

    content = opinion_news(cur_time)
    title = '[%s] 국내 주요언론사 사설, 칼럼 (ㄱ,ㄴ순)' % cur_time
    tistory_post(token, title, content, '767067')  # 사설, 칼럼


def weekend(cur_time, token):

    content = get_reddit('korea')
    title = '[%s] Reddit에 올라온 한국 관련 소식' % cur_time
    tistory_post(token, title, content, '765357')  # economy

    content = get_reddit()
    title = '[%s] Reddit (Programming & Python)' % cur_time
    tistory_post(token, title, content, '765668')  # IT news

    content = get_hacker_news()
    title = '[%s] Hacker News (Ranking 1~30)' % cur_time
    tistory_post(token, title, content, '765668')  # IT news


def main():
    now = datetime.now()
    cur_time = '%4d%02d%02d' % (now.year, now.month, now.day)
    week_num = datetime.today().weekday()

    token = get_tistory_token()

    # once_a_4days(now, cur_time, token)
    if week_num < 5:
        weekday(cur_time, token)
    else:
        weekend(cur_time, token)

    # content = get_kdi_research()
    # title = '[%s] KDI 한국개발연구원 연구주제별 보고서' % cur_time
    # tistory_post(token, title, content, '766948')  # korea department


if __name__ == '__main__':
    main()
