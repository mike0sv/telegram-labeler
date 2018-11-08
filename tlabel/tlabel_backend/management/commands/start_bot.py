import logging
import subprocess
import sys
import time

from django.core.management.base import BaseCommand
from telegram.ext import dispatcher

from tlabel import settings
from tlabel_backend.models import TGBot
from tlabel_backend.sync_bot_api import TelegramBotApi


class Command(BaseCommand):
    help = 'Run Bot'

    def add_arguments(self, parser):
        parser.add_argument('-b', '--bot', type=int, default=None)
        # parser.add_argument('-w', '--workers', type=int, default=0)
        # parser.add_argument('-s', '--stale', type=int, default=25)
        # parser.add_argument('-b', '--batch', type=int, default=100)
        # parser.add_argument('-s', '--sleep', type=int, default=5)
        # parser.add_argument('-m', '--mul', type=int, default=1)
        # parser.add_argument('-u', '--user', type=int, default=None)
        # parser.add_argument('--telepot', action='store_true', default=False)
        parser.add_argument('-d', '--debug', action='store_true')
        # parser.add_argument('-a', '--watch', action='store_true')

    def handle(self, *args, **options):
        if options['debug']:
            tglogger = logging.getLogger("telegram")
            tglogger.setLevel(level=logging.DEBUG)
            tglogger.addHandler(logging.StreamHandler(sys.stdout))
        if options['bot'] is None:
            tgbot = TGBot.objects.first()
        else:
            tgbot = TGBot.objects.filter(pk=options['bot']).first()
        print('Using bot {}'.format(tgbot))
        TelegramBotApi(tgbot).start_bot()
        # while True:
        #     time.sleep(1)
