import os
import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegraph import Telegraph, upload_file

# লগিং সেটআপ
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# পরিবেশ থেকে টোকেন এবং API তথ্য নেওয়া
TOKEN = os.environ.get("TOKEN")
API_ID = os.environ.get("API_ID")  # ভবিষ্যতের জন্য যোগ করা, এখন ব্যবহৃত হচ্ছে না
API_HASH = os.environ.get("API_HASH")  # ভবিষ্যতের জন্য যোগ করা, এখন ব্যবহৃত হচ্ছে না

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
        # শিরোনাম ব্যবহারের পর মুছে ফেলা
        if 'title' in context.user_data:
            del context.user_data['title']
    except Exception as e:
        logging.error(f"পেজ তৈরিতে সমস্যা: {e}")
        update.message.reply_text("পেজ তৈরিতে সমস্যা হয়েছে।")

def handle_image(update, context):
    if update.message.document:
        file = update.message.document
        if file.mime_type.startswith('image/'):
            # ফাইল ডাউনলোড করা
            file_path = context.bot.get_file(file.file_id).download()
            # Telegra.ph-এ আপলোড করা
            try:
                response = upload_file(file_path)
                link = f"https://telegra.ph{response[0]}"
                update.message.reply_text(f"আপনার ছবির লিঙ্ক: {link}")
            except Exception as e:
                logging.error(f"আপলোডে সমস্যা: {e}")
                update.message.reply_text("আপলোডে সমস্যা হয়েছে।")
            finally:
                # ফাইল মুছে ফেলা
                os.remove(file_path)
        else:
            update.message.reply_text("দয়া করে একটি ছবি পাঠান (ডকুমেন্ট হিসেবে)।")
    else:
        update.message.reply_text("দয়া করে একটি ছবি পাঠান (ডকুমেন্ট হিসেবে)।")

def main():
    if not TOKEN:
        logging.error("টোকেন পাওয়া যায়নি। পরিবেশ ভেরিয়েবলে TOKEN সেট করুন।")
        return

    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # Telegraph অ্যাকাউন্ট তৈরি
    telegraph = Telegraph()
    telegraph.create_account(short_name='MyBot')
    dp.bot_data['telegraph'] = telegraph
    logging.info("Telegraph অ্যাকাউন্ট সফলভাবে তৈরি হয়েছে।")

    # হ্যান্ডলার যোগ করা
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("sct", set_custom_title))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text))
    dp.add_handler(MessageHandler(Filters.document, handle_image))

    # বট চালু করা
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
