"""Правила прохождения теста.

Все проверки выполняются здесь, на сервере. Views и API только вызывают эти функции
и превращают исключения в ответы с понятным текстом.
"""
from django.db import IntegrityError, transaction
from django.utils import timezone

from .models import Attempt, ExamEvent, StudentAnswer


class AttemptError(Exception):
    """Нарушено правило прохождения теста. Текст показывается пользователю."""


class KioskRequiredError(AttemptError):
    """Тест можно проходить только из защищённого клиента."""


def log_event(attempt, event_type, details=None):
    return ExamEvent.objects.create(attempt=attempt, event_type=event_type, details=details or {})


def seconds_left(attempt):
    if attempt.is_finished:
        return 0
    return max(0, int((attempt.deadline - timezone.now()).total_seconds()))


def expire_if_overdue(attempt):
    """Завершает попытку со статусом EXPIRED, если время по часам сервера вышло."""
    if attempt.is_finished or timezone.now() < attempt.deadline:
        return False
    finish_attempt(attempt, status=Attempt.Status.EXPIRED)
    log_event(attempt, ExamEvent.Type.TIME_EXPIRED)
    return True


def expire_overdue_attempts():
    expired = 0
    for attempt in Attempt.objects.filter(status=Attempt.Status.IN_PROGRESS).select_related('test'):
        expired += expire_if_overdue(attempt)
    return expired


def check_client(attempt, from_kiosk):
    if attempt.test.require_kiosk and not from_kiosk:
        log_event(attempt, ExamEvent.Type.NOT_KIOSK)
        raise KioskRequiredError('Этот тест можно проходить только в защищённом клиенте.')


def start_attempt(test, student, *, from_kiosk):
    """Начинает попытку или возвращает уже идущую попытку этого теста.

    Возвращает пару (попытка, создана_ли_новая).
    """
    if not student.is_student:
        raise AttemptError('Проходить тесты могут только студенты.')
    if not test.is_published:
        raise AttemptError('Тест не опубликован.')
    if not test.groups.filter(students=student).exists():
        raise AttemptError('Тест не назначен вашей учебной группе.')
    if test.require_kiosk and not from_kiosk:
        raise KioskRequiredError('Этот тест можно проходить только в защищённом клиенте.')

    active = Attempt.objects.filter(student=student, status=Attempt.Status.IN_PROGRESS).first()
    if active and not expire_if_overdue(active):
        if active.test_id != test.id:
            raise AttemptError(f'Сначала завершите тест «{active.test}».')
        # Повторный вход (перезагрузка, второе окно): продолжаем ту же попытку и оставляем след в журнале.
        log_event(active, ExamEvent.Type.SECOND_SESSION)
        return active, False

    if test.attempts.filter(student=student).count() >= test.max_attempts:
        raise AttemptError('Попытки закончились.')
    if not test.questions.exists():
        raise AttemptError('В тесте нет вопросов.')

    try:
        with transaction.atomic():
            attempt = Attempt.objects.create(
                test=test, student=student, total_questions=test.questions.count()
            )
    except IntegrityError:
        # Параллельный запрос успел создать попытку — сработало ограничение в базе.
        raise AttemptError('У вас уже есть активная попытка.')
    return attempt, True


def ensure_in_progress(attempt):
    expire_if_overdue(attempt)
    if attempt.status == Attempt.Status.EXPIRED:
        raise AttemptError('Время вышло, попытка завершена.')
    if attempt.is_finished:
        raise AttemptError('Попытка уже завершена, изменить её нельзя.')


def save_answer(attempt, question_id, option_ids, *, from_kiosk):
    check_client(attempt, from_kiosk)
    ensure_in_progress(attempt)

    question = attempt.test.questions.filter(pk=question_id).first()
    if question is None:
        raise AttemptError('Вопрос не относится к этому тесту.')

    option_ids = set(option_ids)
    options = list(question.options.filter(pk__in=option_ids))
    if len(options) != len(option_ids):
        raise AttemptError('Вариант ответа не относится к этому вопросу.')
    if question.question_type == question.Type.SINGLE and len(options) != 1:
        raise AttemptError('В этом вопросе нужно выбрать ровно один вариант.')

    answer, _ = StudentAnswer.objects.get_or_create(attempt=attempt, question=question)
    answer.selected_answers.set(options)
    answer.save(update_fields=['answered_at'])
    return answer


def grade_answer(answer):
    selected = set(answer.selected_answers.values_list('pk', flat=True))
    correct = set(answer.question.options.filter(is_correct=True).values_list('pk', flat=True))
    answer.is_correct = bool(correct) and selected == correct
    answer.points = answer.question.points if answer.is_correct else 0
    answer.save(update_fields=['is_correct', 'points'])


@transaction.atomic
def finish_attempt(attempt, status=Attempt.Status.COMPLETED):
    """Проверяет ответы, считает баллы и закрывает попытку."""
    answers = attempt.answers.select_related('question')
    for answer in answers:
        grade_answer(answer)

    attempt.score = sum(a.points for a in answers)
    attempt.correct_answers = sum(a.is_correct for a in answers)
    attempt.max_score = sum(q.points for q in attempt.test.questions.all())
    attempt.total_questions = attempt.test.questions.count()
    attempt.status = status
    attempt.finished_at = timezone.now()
    attempt.save()
    return attempt


def finish_by_student(attempt, *, from_kiosk):
    check_client(attempt, from_kiosk)
    ensure_in_progress(attempt)
    return finish_attempt(attempt)


def record_client_event(attempt, event_type, details):
    if event_type not in ExamEvent.CLIENT_TYPES:
        raise AttemptError('Неизвестный тип события.')
    if attempt.is_finished:
        raise AttemptError('Попытка уже завершена.')
    return log_event(attempt, event_type, details)
