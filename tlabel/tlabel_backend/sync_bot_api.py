import traceback

import telegram
from telegram.ext import Updater, MessageHandler, CallbackQueryHandler, Filters
from telegram.ext.filters import MergedFilter

from tlabel import settings


class BotMessage:
    TYPES = ('photo', 'audio', 'document', 'video', 'voice')
    METHODS = {
        'photo': telegram.Bot.send_photo,
        'audio': telegram.Bot.send_audio,
        'document': telegram.Bot.send_document,
        'video': telegram.Bot.send_video,
        'voice': telegram.Bot.send_voice
    }

    def __init__(self, text=None, photo=None, audio=None, document=None, video=None, voice=None):
        self.text = text
        media = [photo, audio, document, video, voice]
        existing_media = [m for m in media if m is not None]
        if len(existing_media) > 1:
            raise ValueError('Cannot send multiple media')
        elif len(existing_media) == 1:
            self.media_type, self.media = next((m, t) for m, t in zip(self.TYPES, media) if m is not None)
        else:
            self.media_type = 'text'
            self.media = None

    def send(self, bot: telegram.Bot, chat_id, keyboard):
        if self.media_type == 'text':
            return bot.send_message(chat_id, text=self.text, reply_markup=keyboard)
        else:
            kwargs = {'self': bot, 'chat_id': chat_id, self.media_type: self.media,
                      'reply_markup': keyboard, 'caption': self.text}
            return self.METHODS[self.media_type](**kwargs)


class TelegramBotApi:
    def __init__(self, tgbot: 'TGBot'):
        self.tgbot = tgbot
        self.bot = tgbot.bot
        self.token = tgbot.token

    def get_callback_chat_id(self, msg):
        return msg.effective_chat.id

    def send_text(self, chat_id, text, reply_to_message_id=None):
        self.bot.send_message(chat_id, text, reply_to_message_id=reply_to_message_id)

    def send_message(self, chat_id, message: BotMessage, feedbacks=None):
        if feedbacks:
            keyboard = telegram.InlineKeyboardMarkup(inline_keyboard=[[
                telegram.InlineKeyboardButton(text=f, callback_data=f) for f in feedbacks
            ]])
        else:
            keyboard = None

        sent = message.send(self.bot, chat_id, keyboard)
        return sent['message_id']

    def remove_keyboard(self, chat_id, message_id):
        self.bot.edit_message_reply_markup(chat_id, message_id, timeout=30)

    def get_callback_data(self, msg):
        return msg.callback_query.data

    def get_callback_message_id(self, msg):
        return msg.callback_query.message.message_id

    def get_user_data(self, user_id):
        chat = self.bot.get_chat(user_id)
        return chat.username or '', chat.first_name or '', chat.last_name or ''

    def start_bot(self):

        def on_text(bot, update):
            try:
                send_row(self, update.message.chat_id)
            except:
                traceback.print_exc()
                raise

        def on_callback(bot, update):
            try:
                on_callback_query(self, update)
            except:
                traceback.print_exc()
                raise

        print(self.bot.getMe())
        updater = Updater(bot=self.bot)

        updater.dispatcher.add_handler(MessageHandler(MergedFilter(Filters.text, or_filter=Filters.command), on_text))
        updater.dispatcher.add_handler(CallbackQueryHandler(on_callback))

        if settings.TG_WEBHOOK:
            check_certs()
            print('Webhook listening at port {}\nInfo at https://api.telegram.org/bot{}/getWebhookInfo'.format(
                settings.TG_WEBHOOK_PORT,
                self.token))
            host = get_public_host()
            updater.start_webhook(listen='0.0.0.0', port=settings.TG_WEBHOOK_PORT,
                                  url_path=self.token,
                                  cert=settings.TG_WEBHOOK_CERT_PEM, key=settings.TG_WEBHOOK_CERT_KEY,
                                  webhook_url='https://{}:{}/{}'.format(host,
                                                                        settings.TG_WEBHOOK_PORT,
                                                                        self.token))
        else:
            print('Start polling')
            updater.start_polling()


from tlabel_backend.models import TGBot
from tlabel_backend.bot import check_certs, get_public_host, send_row, on_callback_query
