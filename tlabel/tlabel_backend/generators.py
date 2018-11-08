import glob
import io
import os

from tlabel import settings
from tlabel_backend.models import Dataset, DatasetRow
from tlabel_backend.sync_bot_api import BotMessage


def read_file(path, mode='rb'):
    with open(path, mode) as f:
        payload = f.read()
        return io.BytesIO(payload) if 'b' in mode else io.StringIO(payload)


class Generator:
    def __init__(self, dataset: Dataset):
        self.dataset = dataset

    def generate(self):
        raise NotImplemented

    def labels(self):
        return settings.DEFAULT_CLASSES

    def create_message(self, row: DatasetRow) -> BotMessage:
        raise NotImplemented


class LocalImageGenerator(Generator):
    def _generate(self, base_path, path):
        print(base_path, path)
        for p in glob.glob(os.path.join(path, '*')):
            if os.path.isdir(p):
                yield from self._generate(base_path, p)
            elif os.path.isfile(p):
                fname = os.path.basename(p)
                yield DatasetRow(row_id=fname, dataset=self.dataset, path=p)

    def generate(self):
        yield from self._generate(settings.DEFAULT_DATA_DIR, self.dataset.path)

    def create_message(self, row: DatasetRow):
        return BotMessage(str(row.row_id), photo=read_file(row.path, 'rb'))
