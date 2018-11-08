from django.contrib import admin
from .models import DatasetRow, Dataset, Labeler, TGBot, Label


# Register your models here.


def make_admin(cls, columns):
    @admin.register(cls)
    class KekAdmin(admin.ModelAdmin):
        list_display = tuple(columns)

    return KekAdmin


DatasetAdmin = make_admin(Dataset, ['name', 'path'])
DatasetRowAdmin = make_admin(DatasetRow, ['row_id', 'dataset'])
LabelerAdmin = make_admin(Labeler, ['tg_id', 'name', 'last_name', 'username', 'bot'])
TGBotAdmin = make_admin(TGBot, ['name', 'botname'])
LabelAdmin = make_admin(Label, ['dataset', 'row_id', 'label'])
