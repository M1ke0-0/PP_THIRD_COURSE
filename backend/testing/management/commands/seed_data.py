from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import User
from attempts import services
from attempts.models import ExamEvent
from study_groups.models import Group
from testing.models import Question, Test

USERS = [
    # username, пароль, имя, фамилия, роль
    ('admin', 'admin12345', 'Анна', 'Админова', User.Role.ADMIN),
    ('teacher', 'teacher12345', 'Олег', 'Преподавателев', User.Role.TEACHER),
    ('student', 'student12345', 'Иван', 'Иванов', User.Role.STUDENT),
    ('petrov', 'student12345', 'Пётр', 'Петров', User.Role.STUDENT),
    ('sidorov', 'student12345', 'Алексей', 'Сидоров', User.Role.STUDENT),
]

# Вопрос: (текст, тип, баллы, [(вариант, правильный)])
PYTHON_QUESTIONS = [
    ('Что выведет print(2 + 3)?', Question.Type.SINGLE, 1,
     [('4', False), ('5', True), ('6', False), ('Ошибка', False)]),
    ('Какой тип используется для целых чисел?', Question.Type.SINGLE, 1,
     [('int', True), ('str', False), ('list', False), ('dict', False)]),
    ('Какие типы в Python изменяемые?', Question.Type.MULTIPLE, 2,
     [('list', True), ('tuple', False), ('dict', True), ('str', False)]),
    ('Как объявить функцию?', Question.Type.SINGLE, 1,
     [('function f():', False), ('def f():', True), ('func f():', False)]),
]

NETWORK_QUESTIONS = [
    ('Какой порт по умолчанию у HTTPS?', Question.Type.SINGLE, 1,
     [('80', False), ('443', True), ('22', False)]),
    ('Какие протоколы работают на транспортном уровне?', Question.Type.MULTIPLE, 2,
     [('TCP', True), ('UDP', True), ('IP', False), ('HTTP', False)]),
    ('Сколько бит в адресе IPv4?', Question.Type.SINGLE, 1,
     [('32', True), ('64', False), ('128', False)]),
]


class Command(BaseCommand):
    help = 'Создаёт демонстрационные данные: пользователей, группы, тесты и попытки.'

    @transaction.atomic
    def handle(self, *args, **options):
        if User.objects.filter(username='teacher').exists():
            self.stdout.write(self.style.WARNING('Демо-данные уже созданы.'))
            return

        users = {}
        for username, password, first_name, last_name, role in USERS:
            users[username] = User.objects.create_user(
                username=username, password=password, email=f'{username}@example.com',
                first_name=first_name, last_name=last_name, role=role,
                is_staff=role == User.Role.ADMIN, is_superuser=role == User.Role.ADMIN,
            )

        group = Group.objects.create(name='ПИ-21', description='Прикладная информатика, 2021')
        group.students.add(users['student'], users['petrov'], users['sidorov'])

        python_test = self._create_test(
            users['teacher'], group, PYTHON_QUESTIONS,
            title='Основы Python', description='Базовый синтаксис и типы данных.', duration=20,
            max_attempts=2,
        )
        network_test = self._create_test(
            users['teacher'], group, NETWORK_QUESTIONS,
            title='Компьютерные сети (экзамен)', description='Проходится только в защищённом клиенте.',
            duration=30, max_attempts=1, require_kiosk=True,
        )

        self._pass_test(python_test, users['petrov'], correct=True)
        self._pass_test(python_test, users['sidorov'], correct=False)
        attempt = self._pass_test(network_test, users['petrov'], correct=True, finish=False)
        services.log_event(attempt, ExamEvent.Type.FOCUS_LOST, {'source': 'blur'})
        services.finish_attempt(attempt)

        self.stdout.write(self.style.SUCCESS('Демо-данные созданы. Пароли — в README.'))

    def _create_test(self, teacher, group, questions, **fields):
        test = Test.objects.create(teacher=teacher, is_published=True, **fields)
        test.groups.add(group)
        for order, (text, question_type, points, options) in enumerate(questions, start=1):
            question = test.questions.create(text=text, question_type=question_type, points=points, order=order)
            for option_text, is_correct in options:
                question.options.create(text=option_text, is_correct=is_correct)
        return test

    def _pass_test(self, test, student, *, correct, finish=True):
        """Проходит тест через те же сервисы, что и API: все ответы верные или все неверные."""
        attempt, _ = services.start_attempt(test, student, from_kiosk=True)
        for question in test.questions.all():
            options = question.options.filter(is_correct=correct)
            if question.question_type == Question.Type.SINGLE:
                options = options[:1]
            services.save_answer(attempt, question.pk, [o.pk for o in options], from_kiosk=True)
        if finish:
            services.finish_attempt(attempt)
        return attempt
