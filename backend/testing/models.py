from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class TestQuerySet(models.QuerySet):
    def available_for(self, student):
        """Опубликованные тесты, назначенные хотя бы одной группе студента."""
        return self.filter(is_published=True, groups__students=student).distinct()


class Test(models.Model):
    title = models.CharField('название', max_length=200)
    description = models.TextField('описание', blank=True)
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tests',
        limit_choices_to={'role__in': ['TEACHER', 'ADMIN']},
        verbose_name='преподаватель',
    )
    duration = models.PositiveIntegerField(
        'время прохождения, мин', default=30, validators=[MinValueValidator(1)]
    )
    max_attempts = models.PositiveIntegerField(
        'количество попыток', default=1, validators=[MinValueValidator(1)]
    )
    passing_score = models.PositiveIntegerField(
        'проходной балл, %', default=60, validators=[MaxValueValidator(100)]
    )
    is_published = models.BooleanField('опубликован', default=False)
    require_kiosk = models.BooleanField(
        'только из защищённого клиента',
        default=False,
        help_text='Начать тест и отвечать можно только из клиента-киоска.',
    )
    groups = models.ManyToManyField(
        'study_groups.Group',
        through='TestGroup',
        related_name='tests',
        blank=True,
        verbose_name='учебные группы',
    )
    created_at = models.DateTimeField('создан', auto_now_add=True)
    updated_at = models.DateTimeField('изменён', auto_now=True)

    objects = TestQuerySet.as_manager()

    class Meta:
        verbose_name = 'тест'
        verbose_name_plural = 'тесты'
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class TestGroup(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE, verbose_name='тест')
    group = models.ForeignKey('study_groups.Group', on_delete=models.CASCADE, verbose_name='группа')

    class Meta:
        verbose_name = 'назначение группе'
        verbose_name_plural = 'назначения группам'
        constraints = [
            models.UniqueConstraint(fields=['test', 'group'], name='unique_test_group'),
        ]

    def __str__(self):
        return f'{self.test} — {self.group}'


class Question(models.Model):
    class Type(models.TextChoices):
        SINGLE = 'SINGLE', 'Один правильный ответ'
        MULTIPLE = 'MULTIPLE', 'Несколько правильных ответов'

    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='questions', verbose_name='тест')
    text = models.TextField('текст вопроса')
    question_type = models.CharField('тип', max_length=16, choices=Type.choices, default=Type.SINGLE)
    points = models.PositiveIntegerField('баллы', default=1, validators=[MinValueValidator(1)])
    order = models.PositiveIntegerField('порядковый номер', default=0)

    class Meta:
        verbose_name = 'вопрос'
        verbose_name_plural = 'вопросы'
        ordering = ['order', 'id']

    def __str__(self):
        return self.text[:60]


class AnswerOption(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options', verbose_name='вопрос')
    text = models.CharField('текст варианта', max_length=500)
    is_correct = models.BooleanField('правильный', default=False)

    class Meta:
        verbose_name = 'вариант ответа'
        verbose_name_plural = 'варианты ответа'
        ordering = ['id']

    def __str__(self):
        return self.text
