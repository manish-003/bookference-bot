from flask import Flask, request
import telepot
from telepot.namedtuple import InlineQueryResultPhoto
import urllib3
from requests_html import HTMLSession
from bs4 import BeautifulSoup
import datetime as dt
import traceback

headers = {
  "User-Agent":
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36 Edge/18.19582"
}
session = HTMLSession()
def getdata(bname):
    try:
        searchurl=f"https://www.goodreads.com/search?q={bname}"
        searchpage= session.get(searchurl).content
        soup = BeautifulSoup(searchpage, 'lxml')
        tag=soup.find('a',class_='bookTitle')
        if not tag.get('href'):
            return (0,'404','404','404','404','404')
        bookurl= "https://www.goodreads.com"+tag.get('href').split('?')[0]
        bookpage= session.get(bookurl).content
        count = 0
        title =0
        while( (not title) and count<12):
            count+=1
            print("iterations", count, "querry:", bname)
            try:
                soup= BeautifulSoup(bookpage, 'lxml')
                title= soup.find('h1', attrs={'data-testid': 'bookTitle'}).text
            except:
                pass
        authors= ", ".join([i.text for i in soup.find('div', class_='ContributorLinksList').find_all('span',class_='ContributorLink__name')])
        imgsrc = soup.find('img',class_='ResponsiveImage').get('src') #comment following 4 lines to not download image
        rating = float(soup.find('div', class_="RatingStatistics__rating").text)
        star='⭐'
        stars = star*round(rating)
        desc = soup.find('div',class_='BookPageMetadataSection__description').find('span',class_='Formatted').get_text()
        post = \
f"""
<b>{title}</b>
<i>{authors}</i>
{stars} ({rating}/5)

{desc}
"""
        return (1,title, authors,imgsrc,post,bookurl)
    except Exception as e:
        ind_time = dt.datetime.utcnow() + dt.timedelta(hours=5, minutes=30)
        print(ind_time)
        print(traceback.format_exc())
        return (0,'404','404','404','404','404')

def searchq(bookname):
    baseurl = "https://www.goodreads.com"
    searchurl=f"https://www.goodreads.com/search?q={bookname}"
    searchpage= session.get(searchurl).content
    soup = BeautifulSoup(searchpage, 'lxml')
    images = soup.find_all('img',class_='bookCover', limit=6)
    titles=soup.find_all('a',class_='bookTitle', limit=6)
    authors = soup.find_all('a',class_='authorName', limit=6)
    res = [(images[i].get('src'),  titles[i].text.split(':')[0],  authors[i].text,  baseurl+titles[i].get('href')) for i in range(6)]
    return res

def mine(bookurl):
    bookpage= session.get(bookurl).content
    soup= BeautifulSoup(bookpage, 'lxml')
    rating = float(soup.find('div', class_="RatingStatistics__rating").text)
    desc = soup.find('div',class_='BookPageMetadataSection__description').find('span',class_='Formatted').get_text()
    return (rating,desc)

def capgen(bname,aname,burl):
    sr,desc = mine(burl)
    star = "⭐"*round(float(sr))
    post = \
f"""\
<b>{bname}</b>
<i>{aname}</i>
{star} ({sr}/5.00)

{desc}
"""
    link="<a href='"+burl+"'>read more..</a>"
    caption = post
    caplen =len(post)
    linklen = len(link)
    #print(f"querry:{bname}, postlen:{caplen}")
    if (caplen + linklen) >1024:
        limit = 1024 - linklen -5
        caption = post[:limit] + '...\n'
    caption+=link
    return caption

def bookinfo(bookname):
    (succ,title, authors, img,caption,link) = getdata(bookname)
    if not succ:
        return (0,'404','404','404','404')
    link=link.split("?")[0]
    link="<a href='"+link+"'>read more..</a>"
    caplen =len(caption)
    linklen = len(link)
    print(f"querry:{bookname}, postlen:{caplen}")
    if (caplen + linklen) >1024:
        limit = 1024 - linklen -5
        caption = caption[:limit] + '...\n'
    caption+=link
    return (1,title, authors, img,caption)

proxy_url = "http://proxy.server:3128"
telepot.api._pools = {
    'default': urllib3.ProxyManager(proxy_url=proxy_url, num_pools=3, maxsize=10, retries=False, timeout=30),
}
telepot.api._onetime_pool_spec = (urllib3.ProxyManager, dict(proxy_url=proxy_url, num_pools=1, maxsize=1, retries=False, timeout=30))

secret = ""
bot = telepot.Bot('')
bot.setWebhook("".format(secret), max_connections=1)

app = Flask(__name__)
answerer = telepot.helper.Answerer(bot)
@app.route('/{}'.format(secret), methods=["POST"])
def telegram_webhook():
    update = request.get_json()
    if "message" in update:
        chat_id = update["message"]["chat"]["id"]
        if "text" in update["message"]:
            text = update["message"]["text"]
            succ, title, authors, img, caption = bookinfo(text.lower())
            if succ:
                bot.sendPhoto(chat_id,img,caption,parse_mode="html")
            else:
                bot.sendMessage(chat_id, "I can't find your requested book")
        else:
            bot.sendMessage(chat_id, "sorry, I don't understand that kind of messages")
    if "inline_query" in update:
            query_id = update['inline_query']['id']
            query_string = update['inline_query']['query']
            if query_string:
                try:
                    res = searchq(query_string)
                    #[(images[i],titles[i],authors[i]) for i in range(12)]
                    resultspos = [
                    InlineQueryResultPhoto(
                            id = count ,
                            photo_url= i[0],
                            thumb_url = i[0],
                            title= i[1],
                            
                            description = i[3],
                            caption = capgen(i[1],i[2],i[3]),
                            parse_mode = 'html'
                    )
                    for count, i in enumerate(res) if all(res)
                    ]
                    bot.answerInlineQuery(query_id,resultspos,cache_time=18)
                except Exception as e:
                    print(e)
                    ind_time = dt.datetime.utcnow() + dt.timedelta(hours=5, minutes=30)
                    print(ind_time)
                    print(traceback.format_exc())

    return "OK"