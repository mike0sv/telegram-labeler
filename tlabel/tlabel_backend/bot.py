import os
import traceback

import requests
import telegram
import telegram.utils.request

# from tlabel_backend.models import TGBot
from tlabel import settings
from tlabel_backend import policies


def make_bot(tgbot: 'TGBot') -> telegram.Bot:
    if settings.TG_USE_PROXY and settings.TG_PROXY_ADDRESS:
        request_kwargs = {
            'proxy_url': settings.TG_PROXY_ADDRESS,

        }
        if settings.TG_PROXY_USERNAME is not None:
            proxy_auth = {
                'username': settings.TG_PROXY_USERNAME,
                'password': settings.TG_PROXY_PASSWORD,
                'cert_reqs': None
            }
            if settings.TG_PROXY_ADDRESS.startswith('socks'):
                request_kwargs['urllib3_proxy_kwargs'] = proxy_auth
            else:
                request_kwargs.update(proxy_auth)

        request = telegram.utils.request.Request(**request_kwargs)
    else:
        request = None

    bot = telegram.Bot(tgbot.token, request=request)

    return bot


def get_self(tgbot: 'TGBot'):
    return tgbot.bot.getMe()


def get_unanswered_posts(labeler: 'Labeler'):
    return Label.objects.filter(labeler=labeler, label=None)


def update_user_data(api: 'TelegramBotApi', labeler: 'Labeler'):
    try:
        username, name, last_name = api.get_user_data(labeler.tg_id)
        labeler.last_name = last_name
        labeler.name = name
        labeler.username = username
    except:
        print('Error getting user data')
        traceback.print_exc()
    labeler.save()


def get_labeler(api: 'TelegramBotApi', tg_id):
    labeler = Labeler.objects.filter(tg_id=tg_id).first()
    if labeler is None:
        labeler = Labeler(tg_id=tg_id, bot=api.tgbot)  # todo More Data
        labeler.save()
    if labeler.last_name == '' and labeler.name == '' and labeler.username == '':
        update_user_data(api, labeler)
    return labeler


def get_next_row() -> 'DatasetRow':
    row = policies.apply_policies(settings.DEFAULT_POLICIES.split(settings.DELIMITER))  # todo select dataset
    return row


def send_row(api: 'TelegramBotApi', tg_id):
    labeler = get_labeler(api, tg_id)
    unanswered = get_unanswered_posts(labeler).first()
    if unanswered is not None:
        api.send_text(tg_id, 'Answer this one for me, please', reply_to_message_id=unanswered.message_id)
        print('User not replied to {}'.format(unanswered))
        return

    # todo pre-buffer
    row = get_next_row()
    if row is None:
        api.send_text(tg_id, 'No more objects to label')
        return

    message_id = api.send_message(tg_id, row.to_message(), row.get_possible_classes())
    label = Label(labeler=labeler, row=row, message_id=message_id)
    label.save()
    print('Sending row {row} to labeler {labeler}'.format(row=row, labeler=labeler))


def on_callback_query(api: 'TelegramBotApi', update):
    labeler = get_labeler(api, api.get_callback_chat_id(update))
    query_data = api.get_callback_data(update)
    message_id = api.get_callback_message_id(update)
    print('Got label {feedback} to message {msg_id} for labeler {usr}'.format(
        feedback=query_data, msg_id=message_id, usr=labeler))
    label = Label.objects.filter(labeler=labeler, message_id=message_id).first()

    try:
        label.label = query_data
        label.save()
    except:
        traceback.print_exc()
    try:
        api.remove_keyboard(labeler.tg_id, message_id)
    except:
        print('Error editing reply')

    send_row(api, labeler.tg_id)


def get_public_host():
    r = requests.get('http://whatismyip.akamai.com/')
    if r.status_code != 200:
        r.raise_for_status()
    return r.text


def check_certs():
    if settings.TG_WEBHOOK:
        if not os.path.isfile(settings.TG_WEBHOOK_CERT_KEY) or not os.path.isfile(settings.TG_WEBHOOK_CERT_PEM):
            raise Exception('Missing certificates for bot at \n{}\n{}'.format(settings.TG_WEBHOOK_CERT_KEY,
                                                                              settings.TG_WEBHOOK_CERT_PEM))

        from OpenSSL import crypto

        with open(settings.TG_WEBHOOK_CERT_PEM, 'rb') as c:
            cert = crypto.load_certificate(crypto.FILETYPE_PEM, c.read())
            subject = cert.get_subject()
            issued_to = subject.CN  # the Common Name field
            if issued_to != get_public_host():
                raise Exception(
                    'Not valid certificates: issued to "{}", but host ip is "{}"'.format(issued_to, settings.HOST_IP))


from tlabel_backend.models import TGBot, Labeler, Label, DatasetRow
from tlabel_backend.sync_bot_api import TelegramBotApi, BotMessage
