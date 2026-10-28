from django.conf import settings
from django.db import models


class Group(models.Model):
    name = models.CharField('название', max_length=64, unique=True)
    description = models.TextField('описание', blank=True)
    students = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='GroupStudent',
        related_name='study_groups',
        verbose_name='студенты',
    )

    class Meta:
        verbose_name = 'учебная группа'
        verbose_name_plural = 'учебные группы'
        ordering = ['name']

    def __str__(self):
        return self.name


class GroupStudent(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, verbose_name='группа')
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'STUDENT'},
        verbose_name='студент',
    )
    added_at = models.DateTimeField('добавлен', auto_now_add=True)

    class Meta:
        verbose_name = 'студент группы'
        verbose_name_plural = 'студенты группы'
        constraints = [
            models.UniqueConstraint(fields=['group', 'student'], name='unique_group_student'),
        ]

    def __str__(self):
        return f'{self.student} — {self.group}'
