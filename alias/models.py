from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import (models,
                       transaction)
from datetime import (datetime,
                      timedelta)
from django.utils import timezone
from django.db.models import Q
from django.db.models.query import QuerySet


# Create your models here.

class Slug(models.Model):
    slug = models.SlugField(unique=True, max_length=25)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    def __str__(self):
        return self.slug

    def clean(self):
        from django.core.exceptions import ValidationError
        try:
            ContentType.objects.get_for_model(self.content_type)
        except Exception:
            raise ValidationError({'content_type': 'incorrect ContentType'})
        try:
            self.content_type.get_object_for_this_type(id=self.object_id)
        except Exception:
            raise ValidationError({'object_id': "object id does not exists"})
        super(Slug, self).clean()

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        self.full_clean()
        super(Slug, self).save()


class ISlag(models.Model):
    slug_model = GenericRelation(Slug)

    class Meta:
        abstract = True


class TestModel(ISlag):
    name = models.CharField(max_length=25, default=None)
    surname = models.CharField(max_length=25, default=None)

    def __str__(self):
        return "id = {}, name = {}".format(self.id, self.name)


class Alias(models.Model):
    alias = models.SlugField(max_length=255)
    target = models.ForeignKey(Slug, on_delete=models.CASCADE)
    start = models.DateTimeField()
    end = models.DateTimeField(default=None, blank=True)

    def __str__(self):
        return "alias={} target= {}, date = [{}] - [{}]".format(self.alias, self.target, self.start, self.end)

    def clean(self):
        from django.core.exceptions import ValidationError
        super(Alias, self).clean()
        if self.end is None:
            self.end = timezone.make_aware(datetime.max)
        if self.start is None:
            raise ValidationError("Incorrect start date")
        if self.start >= self.end:
            date_error_1 = "End date same or bigger then Start date"
            raise ValidationError({'start': date_error_1,
                                   'end': date_error_1})
        date_collision = False
        alias = Alias.objects.filter(alias__exact=self.alias)
        for x in alias:
            if x.start < self.start and x.end > self.end:
                date_collision = True
        alias_start = alias.filter(start__range=(self.start, self.end)).exclude(start__exact=self.end)
        alias_end = alias.filter(end__range=(self.start, self.end)).exclude(end__exact=self.start)
        if alias_start or alias_end:
            date_collision = True
        if date_collision is True:
            date_error_2 = "There was date overlap error with Alias"
            raise ValidationError({'start': date_error_2,
                                   'end': date_error_2})

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        if self.end is None:
            self.end = timezone.make_aware(datetime.max)
        self.full_clean()
        super(Alias, self).save()


def get_aliases(target: Alias.objects, since: datetime, to: datetime) -> 'QuerySet':
    """
    get all Aliases of a specific object in a specific time range
    :param target: Alias.target object
    :param since: datetime
    :param to:  datetime
    :return: class 'django.db.models.query.QuerySet'
    """

    delta = timedelta(microseconds=1)
    aliases = Alias.objects.filter(target=target).filter(
        Q(start__range=(since, to - delta)) | Q(end__range=(since + delta, to)))
    return aliases


@transaction.atomic()
def alias_replace(existing_alias: Alias, replace_at: datetime, new_alias_value: str):
    """
    will set end for the existing_alias to replace_at moment, create a new Alias withalias=new_alias_value and
    start=replace_at, end=None.
    :param existing_alias:
    :param replace_at:
    :param new_alias_value:
    """
    ex = existing_alias
    if not (ex.start < replace_at < ex.end):
        raise ValueError("Alias.start < replace_at < Alias.end is {}".format(False))
    Alias.objects.filter(alias=ex.alias, target=ex.target, start=ex.start).update(end=replace_at)
    Alias.objects.create(alias=new_alias_value, target=existing_alias.target, start=replace_at)
