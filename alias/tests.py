from django.test import TestCase
from .models import (Slug,
                     Alias,
                     TestModel,
                     get_aliases,
                     alias_replace)
from django.utils import (timezone)
from datetime import (timedelta)
from django.core.exceptions import ValidationError


# Create your tests here.

def custom_set_up():
    TestModel(name='User', surname='surUser').save()
    TestModel(name='Ivan', surname='Ivanov').save()
    TestModel(name=22, surname=21).save()
    users = TestModel.objects.all()
    slugs = []
    for user in users:
        slugs.append(Slug(slug='id{}-test_model'.format(user.id), content_object=user))
    Slug.objects.bulk_create(slugs)


class TestModelTestCase(TestCase):
    def setUp(self):
        TestModel(name='User', surname='surUser').save()
        TestModel(name='Ivan', surname='Ivanov').save()
        TestModel(name=22, surname=21).save()

    def test_user_creation(self):
        user = TestModel.objects.get(name='User')
        ivan = TestModel.objects.get(surname='Ivanov')
        self.assertEqual(user.name, 'User')
        self.assertEqual(ivan.name, 'Ivan')

    def test_user_validationError(self):
        models_with_validation_error = (TestModel(name='Kitty'),
                                        TestModel(surname='Kitty'),
                                        TestModel(),)
        for model in models_with_validation_error:
            with self.assertRaises(ValidationError):
                model.full_clean()
        # TODO: Parameter 'self' unfilled, why?

    def test_user_saveError(self):
        models_with_validation_error = (TestModel(name='Kitty'),
                                        TestModel(surname='Kitty'),
                                        TestModel(),)
        for model in models_with_validation_error:
            with self.assertRaises(BaseException):
                model.save()


class SlugTestCase(TestCase):
    def setUp(self):
        custom_set_up()

    def test_Slug_work(self):
        users = TestModel.objects.all()
        slug = Slug(slug='qwerty', content_object=users[0])
        slug.save()
        user_by_slug = TestModel.objects.filter(slug_model__slug='qwerty').get()
        self.assertEqual(users[0], user_by_slug)


class AliasTestCase(TestCase):
    time = timezone.now()
    time_start = time - timedelta(days=1)
    time_end = time + timedelta(days=1)
    delta = timedelta(microseconds=1)
    slugs = Slug.objects.all()

    def setUp(self):
        custom_set_up()

    def test_Alias_work(self):
        slugs = self.slugs
        alias = Alias(alias='Test1', target=slugs[0], start=timezone.now() - timedelta(days=50), end=None)
        alias.save()
        alias = Alias.objects.get(alias='Test1', start__lte=timezone.now(), end__gt=timezone.now())
        self.assertEqual(slugs[0], alias.target)

    def test_Alias_overlap_cases(self):
        cases = []
        cases.append({'alias': 'case1',
                      'target': self.slugs[0],
                      'start': self.time_start + self.delta,
                      'end': self.time_end + self.delta})
        cases.append({'alias': 'case1',
                      'target': self.slugs[0],
                      'start': self.time_start - self.delta,
                      'end': self.time_end - self.delta})
        cases.append({'alias': 'case1',
                      'target': self.slugs[0],
                      'start': self.time_start - self.delta,
                      'end': self.time_end + self.delta})
        cases.append({'alias': 'case1',
                      'target': self.slugs[0],
                      'start': self.time_start + self.delta,
                      'end': self.time_end - self.delta})

        Alias.objects.create(alias='case1', target=self.slugs[0], start=self.time_start, end=self.time_end)
        for case in cases:
            with self.assertRaises(ValidationError):
                Alias.objects.create(**case)

    def test_Alias_boundary_value_cases(self):
        cases = []
        cases.append({'alias': 'case1',
                      'target': self.slugs[0],
                      'start': self.time_end,
                      'end': self.time_end + self.delta})
        cases.append({'alias': 'case1',
                      'target': self.slugs[0],
                      'start': self.time_start - self.delta,
                      'end': self.time_start})
        Alias.objects.create(alias='case1', target=self.slugs[0], start=self.time_start, end=self.time_end)
        for case in cases:
            Alias.objects.create(**case)
        self.assertEqual(3, len(Alias.objects.all()))

    def test_get_aliases_cases(self):
        delta = timedelta(days=1)
        Alias.objects.create(alias='case1', target=self.slugs[0], start=self.time_start-delta, end=self.time_start)
        Alias.objects.create(alias='case1', target=self.slugs[0], start=self.time_start, end=self.time_start+delta)
        Alias.objects.create(alias='case1', target=self.slugs[0], start=self.time_start+delta, end=self.time_end)
        Alias.objects.create(alias='case1', target=self.slugs[0], start=self.time_end, end=self.time_end+delta)
        # print(Alias.objects.all())
        aliases1 = get_aliases(target=self.slugs[0], since=self.time_start, to=self.time_end).order_by('start')
        aliases2 = Alias.objects.filter(start__gte=self.time_start, end__lte=self.time_end).order_by('start')
        self.assertQuerysetEqual(aliases1, aliases2, transform=lambda x: x)

    def test_alias_replace_cases(self):
        delta = timedelta(days=1)
        Alias.objects.create(alias='case1', target=self.slugs[0], start=self.time_start-delta)
        alias = Alias.objects.get(alias='case1', start=self.time_start-delta)
        alias_replace(existing_alias=alias, replace_at=self.time_start, new_alias_value='qwerty')
        cases = []
        cases.append({'existing_alias': alias, 'replace_at': self.time_start - 2 * delta, 'new_alias_value': 'qwerty1'})
        cases.append({'existing_alias': alias, 'replace_at': self.time_start - delta, 'new_alias_value': 'qwerty2'})
        for case in cases:
            with self.assertRaises(BaseException):
                alias_replace(**case)
