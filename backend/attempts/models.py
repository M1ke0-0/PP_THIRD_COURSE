from datetime import timedelta

from django.conf import settings
from django.db import models
from django.db.models import Q


class Attempt(models.Model):
    class Status(models.TextChoices):
        IN_PROGRESS = 'IN_PROGRESS', 'В процессе'
        COMPLETED = 'COMPLETED', 'Завершена'
        EXPIRED = 'EXPIRED', 'Время вышло'

    test = models.ForeignKey('testing.Test', on_delete=models.CASCADE, related_name='attempts', verbose_name='тест')
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='attempts', verbose_name='студент'
    )
    started_at = models.DateTimeField('начата', auto_now_add=True)
    finished_at = models.DateTimeField('завершена', null=True, blank=True)
    score = models.PositiveIntegerField('набрано баллов', default=0)
    max_score = models.PositiveIntegerField('максимум баллов', default=0)
    correct_answers = models.PositiveIntegerField('правильных ответов', default=0)
    total_questions = models.PositiveIntegerField('всего вопросов', default=0)
    status = models.CharField('статус', max_length=16, choices=Status.choices, default=Status.IN_PROGRESS)

    class Meta:
        verbose_name = 'попытка'
        verbose_name_plural = 'попытки'
        ordering = ['-started_at']
        constraints = [
            # Вторая вкладка или второй компьютер не смогут открыть параллельную попытку.
            models.UniqueConstraint(
                fields=['student'],
                condition=Q(status='IN_PROGRESS'),
                name='one_active_attempt_per_student',
            ),
        ]

    def __str__(self):
        return f'{self.student} — {self.test} ({self.get_status_display()})'

    @property
    def deadline(self):
        return self.started_at + timedelta(minutes=self.test.duration)

    @property
    def is_finished(self):
        return self.status != self.Status.IN_PROGRESS

    @property
    def percent(self):
        if not self.max_score:
            return 0
        return round(self.score / self.max_score * 100, 1)

    @property
    def is_passed(self):
        return self.is_finished and self.percent >= self.test.passing_score


class StudentAnswer(models.Model):
    attempt = models.ForeignKey(Attempt, on_delete=models.CASCADE, related_name='answers', verbose_name='попытка')
    question = models.ForeignKey('testing.Question', on_delete=models.CASCADE, verbose_name='вопрос')
    selected_answers = models.ManyToManyField('testing.AnswerOption', verbose_name='выбранные варианты')
    is_correct = models.BooleanField('верно', default=False)
    points = models.PositiveIntegerField('баллы', default=0)
    answered_at = models.DateTimeField('время ответа', auto_now=True)

    class Meta:
        verbose_name = 'ответ студента'
        verbose_name_plural = 'ответы студентов'
        constraints = [
            models.UniqueConstraint(fields=['attempt', 'question'], name='unique_answer_per_question'),
        ]

    def __str__(self):
        return f'{self.attempt_id}: {self.question}'


class ExamEvent(models.Model):
    class Type(models.TextChoices):
        FOCUS_LOST = 'FOCUS_LOST', 'Окно потеряло фокус'
        NAVIGATION_BLOCKED = 'NAVIGATION_BLOCKED', 'Попытка перейти на другой сайт'
        NOT_KIOSK = 'NOT_KIOSK', 'Запрос не из защищённого клиента'
        SECOND_SESSION = 'SECOND_SESSION', 'Повторный вход во время попытки'
        TIME_EXPIRED = 'TIME_EXPIRED', 'Время вышло'

    # События, которые может прислать клиент. Остальные создаёт только сервер.
    CLIENT_TYPES = [Type.FOCUS_LOST, Type.NAVIGATION_BLOCKED]

    attempt = models.ForeignKey(Attempt, on_delete=models.CASCADE, related_name='events', verbose_name='попытка')
    event_type = models.CharField('событие', max_length=32, choices=Type.choices)
    created_at = models.DateTimeField('время', auto_now_add=True)
    details = models.JSONField('подробности', default=dict, blank=True)

    class Meta:
        verbose_name = 'событие экзамена'
        verbose_name_plural = 'журнал событий'
        ordering = ['created_at']

    def __str__(self):
        return f'{self.get_event_type_display()} ({self.created_at:%H:%M:%S})'
