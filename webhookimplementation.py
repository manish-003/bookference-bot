from flask import Flask, request
import telepot
import urllib3
import requests
from bs4 import BeautifulSoup

def getdata(bname):
    searchurl=f"https://www.goodreads.com/search?q={bname}"
    searchpage= requests.get(searchurl).content
    soup = BeautifulSoup(searchpage, 'lxml')
    tag=soup.find('a',class_='bookTitle')
    bookurl= "https://www.goodreads.com"+tag.get('href')
    bookpage= requests.get(bookurl).content
    soup= BeautifulSoup(bookpage, 'lxml')
    title= soup.find('h1', attrs={'data-testid': 'bookTitle'}).text
    authors= ", ".join([i.text for i in soup.find('div', class_='BookPageMetadataSection__contributor').find_all('span',class_='ContributorLink__name')])
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
    return (imgsrc,post,bookurl)

def bookinfo(bookname):
    (img,caption,link) = getdata(bookname)
    link=link.split("?")[0]
    link="<a href='"+link+"'>read more..</a>"
    caplen =len(caption)
    linklen = len(link)
    print(f"querry:{bookname}, postlen:{caplen}")
    if (caplen + linklen) >1024:
        limit = 1024 - linklen -5
        caption = caption[:limit] + '...\n'
    caption+=link
    return (img,caption)

proxy_url = "http://proxy.server:3128"
telepot.api._pools = {
    'default': urllib3.ProxyManager(proxy_url=proxy_url, num_pools=3, maxsize=10, retries=False, timeout=30),
}
telepot.api._onetime_pool_spec = (urllib3.ProxyManager, dict(proxy_url=proxy_url, num_pools=1, maxsize=1, retries=False, timeout=30))

secret = "<a secret number>"
bot = telepot.Bot('<your bot api token>')
bot.setWebhook("https://manish003.pythonanywhere.com/{}".format(secret), max_connections=1)

app = Flask(__name__)

@app.route('/{}'.format(secret), methods=["POST"])
def telegram_webhook():
    update = request.get_json()
    if "message" in update:
        chat_id = update["message"]["chat"]["id"]
        if "text" in update["message"]:
            text = update["message"]["text"]
            img, caption = bookinfo(text)
            bot.sendPhoto(chat_id,img,caption,parse_mode="html")
        else:
            bot.sendMessage(chat_id, "From the web: sorry, I didn't understand that kind of message")
    return "OK"
