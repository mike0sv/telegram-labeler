import telegram
from cached_property import cached_property
from django.db import models
from django.utils.module_loading import import_string

from tlabel import settings


def make_str(*fields):
    def dec(cls):
        def __str__(self):
            return ' '.join(str(getattr(self, f)) for f in fields)

        setattr(cls, '__str__', __str__)
        return cls

    return dec


@make_str('name')
class Dataset(models.Model):
    name = models.TextField(unique=True)
    path = models.TextField(null=True)
    params = models.TextField(null=True)

    generator_class = models.TextField()
    policies = models.TextField()

    classes = models.TextField()

    def load_rows(self):
        for row in self.generator.generate():
            row.save()

    @cached_property
    def generator(self):
        return import_string(self.generator_class)(self)


class DatasetRow(models.Model):
    row_id = models.TextField()
    path = models.TextField()
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name='rows')
    override_classes = models.TextField(blank=True)

    class Meta:
        unique_together = (('row_id', 'dataset'),)

    def get_possible_classes(self):
        clss = self.override_classes
        if not clss:
            clss = self.dataset.classes
        return clss.split(settings.CLASS_DELIMITER)

    def to_message(self):
        return self.dataset.generator.create_message(self)


@make_str('name', 'botname')
class TGBot(models.Model):
    token = models.TextField()
    name = models.TextField()
    botname = models.TextField()

    @cached_property
    def bot(self) -> telegram.Bot:
        from tlabel_backend import bot
        return bot.make_bot(self)

    def update_bot(self):
        from tlabel_backend import bot
        info = bot.get_self(self)
        self.name = info['first_name']
        self.botname = info['username']


@make_str('name', 'last_name', 'username')
class Labeler(models.Model):
    bot = models.ForeignKey(TGBot, on_delete=models.CASCADE, related_name='users')
    tg_id = models.IntegerField()
    name = models.TextField(blank=True)
    last_name = models.TextField(blank=True)
    username = models.TextField(blank=True)

    class Meta:
        unique_together = (('bot', 'tg_id'),)


@make_str('label')
class Label(models.Model):
    row = models.ForeignKey(DatasetRow, on_delete=models.CASCADE, related_name='labels')
    labeler = models.ForeignKey(Labeler, on_delete=models.SET_NULL, null=True, related_name='labels')
    label = models.TextField(null=True, db_index=True)
    message_id = models.IntegerField(null=True)

    def dataset(self):
        return self.row.dataset

    def row_id(self):
        return self.row.row_id
