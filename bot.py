import os
import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegraph import Telegraph, upload_file

# লগিং সেটআপ
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# পরিবেশ থেকে টোকেন এবং API তথ্য নেওয়া
TOKEN = os.environ.get("TOKEN")
API_ID = os.environ.get("API_ID")
API_HASH = os.environ.get("API_HASH")

def start(update, context):
    update.message.reply_text("আমি একটি টেলিগ্রাফ বট! ছবি বা টেক্সট পাঠান, আমি Telegra.ph-এ আপলোড করে লিঙ্ক দেব।")

def set_custom_title(update, context):
    if context.args:
        title = " ".join(context.args)
        context.user_data['title'] = title
        update.message.reply_text(f"শিরোনাম সেট করা হয়েছে: {title}")
    else:
        update.message.reply_text("দয়া করে একটি শিরোনাম দিন। যেমন: /sct আমার শিরোনাম")

def handle_text(update, context):
    text = update.message.text
    title = context.user_data.get('title', 'Untitled')
    html_content = f"<p>{text}</p>"
    telegraph = context.bot_data['telegraph']
    try:
        response = telegraph.create_page(
            title=title,
            html_content=html_content
        )
        page_url = response['url']
        update.message.reply_text(f"আপনার টেক্সট পেজ: {page_url}")
        if 'title' in context.user_data:
            del context.user_data['title']
    except Exception as e:
        logger.error(f"পেজ তৈরিতে সমস্যা: {e}")
        update.message.reply_text("পেজ তৈরিতে সমস্যা হয়েছে।")

def handle_image(update, context):
    if update.message.document:
        file = update.message.document
        if file.mime_type.startswith('image/'):
            try:
                # ফাইল ডাউনলোড করা
                file_path = context.bot.get_file(file.file_id).download()
                logger.info(f"ফাইল ডাউনলোড সফল: {file_path}")
                # Telegra.ph-এ আপলোড করা
                response = upload_file(file_path)
                if response and len(response) > 0:
                    link = f"https://telegra.ph{response[0]}"
                    logger.info(f"লিঙ্ক তৈরি: {link}")
                    update.message.reply_text(f"আপনার ছবির লিঙ্ক: {link}")
                else:
                    logger.error("কোনো লিঙ্ক ফেরত পাওয়া যায়নি।")
                    update.message.reply_text("আপলোডে সমস্যা হয়েছে।")
            except Exception as e:
                logger.error(f"আপলোডে সমস্যা: {e}")
                update.message.reply_text(f"আপলোডে ত্রুটি: {str(e)}")
            finally:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f"ফাইল মুছে ফেলা হয়েছে: {file_path}")
        else:
            update.message.reply_text("দয়া করে একটি ছবি পাঠান (ডকুমেন্ট হিসেবে)।")
    else:
        update.message.reply_text("দয়া করে একটি ছবি পাঠান (ডকুমেন্ট হিসেবে)।")

def main():
    if not TOKEN:
        logger.error("টোকেন পাওয়া যায়নি। পরিবেশ ভেরিয়েবলে TOKEN সেট করুন।")
        return

    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # Telegraph অ্যাকাউন্ট তৈরি
    telegraph = Telegraph()
    try:
        telegraph.create_account(short_name='MyBot')
        dp.bot_data['telegraph'] = telegraph
        logger.info("Telegraph অ্যাকাউন্ট সফলভাবে তৈরি হয়েছে।")
    except Exception as e:
        logger.error(f"Telegraph অ্যাকাউন্ট তৈরিতে সমস্যা: {e}")
        return

    # হ্যান্ডলার যোগ করা
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("sct", set_custom_title))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text))
    dp.add_handler(MessageHandler(Filters.document, handle_image))

    # Polling শুরু করা
    try:
        updater.start_polling(allowed_updates=[])  # সংঘর্ষ এড়ানোর জন্য allowed_updates নির্দিষ্ট করা
        logger.info("বট সফলভাবে চালু হয়েছে।")
        updater.idle()
    except Exception as e:
        logger.error(f"Polling ত্রুটি: {e}")

if __name__ == '__main__':
    main()
