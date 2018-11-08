import os
import sys

from django.contrib.auth import get_user_model
from django.db import transaction

from tlabel import settings
from tlabel_backend.models import Dataset, TGBot

_to_run = list()


def run(f):
    _to_run.append(f)
    return f


def start():
    if len(sys.argv) > 1 and sys.argv[1] not in ('makemigrations', 'migrate'):
        print('Initializing...')
        for f in _to_run:
            f()


@run
def create_default_user():
    user = settings.DEFAULT_USER
    password = settings.DEFAULT_USER_PASSWORD
    UserModel = get_user_model()
    existing = UserModel.objects.filter(username=user).first()
    if existing is None:
        print('creating superuser {}'.format(user))
        user_data = {'username': user, 'password': password, 'email': ''}
        UserModel._default_manager.db_manager('default').create_superuser(**user_data)


@run
def create_datasets():
    gens = settings.DEFAULT_GENERATORS
    data_dir = settings.DEFAULT_DATA_DIR
    if not os.path.exists(data_dir):
        print('No data at path {}, skipping dataset creation'.format(data_dir))
        return
    for dataset_type in os.listdir(data_dir):
        if dataset_type not in gens:
            print('unknown dataset type {}'.format(dataset_type))
        else:
            gen_name = gens[dataset_type]

            type_path = os.path.join(data_dir, dataset_type)
            for dataset_name in os.listdir(type_path):
                if Dataset.objects.filter(name=dataset_name).first() is not None:
                    continue
                dataset_path = os.path.join(type_path, dataset_name)
                with transaction.atomic():
                    dataset = Dataset(name=dataset_name, path=dataset_path, generator_class=gen_name,
                                      classes=settings.DEFAULT_CLASSES, policies=settings.DEFAULT_POLICIES)
                    dataset.save()
                    dataset.load_rows()


@run
def create_default_bot():
    if settings.DEFAULT_BOT_TOKEN:
        bot = TGBot.objects.filter(token=settings.DEFAULT_BOT_TOKEN).first()
        if bot is None:
            print('Creating bot {}'.format(settings.DEFAULT_BOT_TOKEN))
            bot = TGBot(token=settings.DEFAULT_BOT_TOKEN)
            bot.update_bot()
            bot.save()
