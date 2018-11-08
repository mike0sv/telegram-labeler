import glob
import io
import os

from tlabel import settings
from tlabel_backend.models import Dataset, DatasetRow
from tlabel_backend.sync_bot_api import BotMessage
from PIL import Image

from tlabel_backend.utils import timeit


def read_file(path, mode='rb'):
    with open(path, mode) as f:
        payload = f.read()
        return io.BytesIO(payload) if 'b' in mode else io.StringIO(payload)


@timeit
def read_image(path, max_size=None):
    if max_size is None:
        return read_file(path)
    im = Image.open(path)

    sx, sy = im.size
    if sx > max_size or sy > max_size:
        if sx > sy:
            ratio = max_size / sx
        else:
            ratio = max_size / sy
        im.thumbnail((int(sx * ratio), int(sy * ratio)), Image.ANTIALIAS)

    stream = io.BytesIO()
    im.save(stream, 'JPEG')
    stream.seek(0)
    return stream


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
        for p in glob.glob(os.path.join(path, '*')):
            if os.path.isdir(p):
                yield from self._generate(base_path, p)
            elif os.path.isfile(p):
                fname = os.path.basename(p)
                yield DatasetRow(row_id=fname, dataset=self.dataset, path=p)

    def generate(self):
        yield from self._generate(settings.DEFAULT_DATA_DIR, self.dataset.path)

    def create_message(self, row: DatasetRow):
        return BotMessage(str(row.row_id), photo=read_image(row.path, 500))
