import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler , MessageHandler, filters
import requests
from bs4 import BeautifulSoup

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, i can fetch you book info from goodreads")

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

async def bookinfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bookname=update.message.text
    (img,caption,link) = getdata(bookname)
    link=link.split("?")[0]
    link="<a href='"+link+"'>read more</a>"
    caplen =len(caption)
    linklen = len(link)
    print(f"querry:{bookname}, postlen:{caplen}")
    if (caplen + linklen) >1024:
        limit = 1024 - linklen -5
        caption = caption[:limit] + '...\n'
    caption+=link
    print("len of final post:",len(caption))
    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=img ,caption=caption,parse_mode="html")

if __name__ == '__main__':
    application = ApplicationBuilder().token('Token').build()
    
    start_handler = CommandHandler('start', start)
    book_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), bookinfo)
    application.add_handler(start_handler)
    application.add_handler(book_handler)
    
    application.run_polling()
