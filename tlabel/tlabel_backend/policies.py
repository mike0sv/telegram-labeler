import random

from tlabel import settings
from tlabel_backend.models import Dataset, DatasetRow


class Policy:
    @staticmethod
    def apply(queryset):
        raise NotImplemented


_policies = {}


def policy(name, finisher=False):
    def register(cls):
        _policies[name] = cls
        if finisher:
            cls.finisher = True
        return cls

    return register


@policy('label_once')
class LabelOnce(Policy):
    @staticmethod
    def apply(queryset):
        return queryset.filter(labels=None)


@policy('random', True)
class Random(Policy):
    @staticmethod
    def apply(queryset):
        ids = queryset.values_list('id', flat=True)
        return queryset.filter(pk=random.choice(ids)).first()


@policy('first', True)
class First(Policy):
    @staticmethod
    def apply(queryset):
        return queryset.first()


def apply_policies(policy_list, dataset: Dataset = None):
    queryset = DatasetRow.objects
    if dataset is not None:
        queryset = queryset.filter(dataset=dataset)

    for p in policy_list:
        queryset = _policies[p].apply(queryset)

    if not isinstance(queryset, DatasetRow) and queryset is not None:
        return _policies[settings.DEFAULT_FINISHER_POLICY].apply(queryset)
    return queryset
