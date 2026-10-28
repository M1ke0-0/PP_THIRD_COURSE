from datetime import timedelta

from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import User
from study_groups.models import Group
from testing.models import Question, Test

from .models import Attempt, ExamEvent
from .services import expire_overdue_attempts

KIOSK = {'HTTP_X_EXAM_CLIENT_KEY': 'test-key'}


@override_settings(EXAM_CLIENT_KEY='test-key')
class AttemptApiTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user('teacher', password='x', role=User.Role.TEACHER)
        self.student = User.objects.create_user('student', password='x', role=User.Role.STUDENT)
        self.other = User.objects.create_user('other', password='x', role=User.Role.STUDENT)
        group = Group.objects.create(name='ПИ-21')
        group.students.add(self.student, self.other)

        self.test = Test.objects.create(
            title='Python', teacher=self.teacher, is_published=True, max_attempts=1, duration=10
        )
        self.test.groups.add(group)
        self.single = self.test.questions.create(text='2 + 3?', points=1, order=1)
        self.right = self.single.options.create(text='5', is_correct=True)
        self.wrong = self.single.options.create(text='4')
        self.multi = self.test.questions.create(
            text='Изменяемые типы', question_type=Question.Type.MULTIPLE, points=2, order=2
        )
        self.multi_right = [
            self.multi.options.create(text='list', is_correct=True),
            self.multi.options.create(text='dict', is_correct=True),
        ]
        self.multi.options.create(text='tuple')

        self.client = APIClient()
        self.client.force_authenticate(self.student)

    def start(self, test=None, **headers):
        return self.client.post(f'/api/tests/{(test or self.test).pk}/start/', **headers)

    def answer(self, attempt_id, question, options, **headers):
        return self.client.post(
            f'/api/attempts/{attempt_id}/answer/',
            {'question': question.pk, 'options': [o.pk for o in options]},
            format='json', **headers,
        )

    def test_full_pass_is_graded(self):
        attempt_id = self.start().data['id']
        self.assertEqual(self.answer(attempt_id, self.single, [self.right]).status_code, 200)
        self.assertEqual(self.answer(attempt_id, self.multi, self.multi_right[:1]).status_code, 200)

        result = self.client.post(f'/api/attempts/{attempt_id}/finish/').data['result']

        self.assertEqual(result['score'], 1)
        self.assertEqual(result['max_score'], 3)
        self.assertEqual(result['correct_answers'], 1)
        self.assertEqual(result['percent'], 33.3)
        self.assertFalse(result['is_passed'])

    def test_correct_answers_are_not_sent_to_student(self):
        data = self.start().data
        self.assertNotIn('is_correct', data['questions'][0]['options'][0])

    def test_unpublished_test_cannot_be_started(self):
        self.test.is_published = False
        self.test.save()
        self.assertEqual(self.start().status_code, 404)

    def test_student_outside_group_cannot_start(self):
        outsider = User.objects.create_user('outsider', password='x', role=User.Role.STUDENT)
        self.client.force_authenticate(outsider)
        self.assertEqual(self.start().status_code, 404)

    def test_teacher_cannot_use_student_api(self):
        self.client.force_authenticate(self.teacher)
        self.assertEqual(self.start().status_code, 403)

    def test_attempt_limit(self):
        attempt_id = self.start().data['id']
        self.client.post(f'/api/attempts/{attempt_id}/finish/')
        response = self.start()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['detail'], 'Попытки закончились.')

    def test_second_start_resumes_attempt_and_is_logged(self):
        first = self.start()
        second = self.start()
        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first.data['id'], second.data['id'])
        self.assertTrue(ExamEvent.objects.filter(event_type=ExamEvent.Type.SECOND_SESSION).exists())

    def test_cannot_start_other_test_while_attempt_active(self):
        other_test = Test.objects.create(title='Сети', teacher=self.teacher, is_published=True)
        other_test.groups.set(self.test.groups.all())
        other_test.questions.create(text='?')
        self.start()
        self.assertEqual(self.start(other_test).status_code, 400)

    def test_finished_attempt_cannot_be_changed(self):
        attempt_id = self.start().data['id']
        self.client.post(f'/api/attempts/{attempt_id}/finish/')
        self.assertEqual(self.answer(attempt_id, self.single, [self.right]).status_code, 400)

    def test_option_from_other_question_is_rejected(self):
        attempt_id = self.start().data['id']
        self.assertEqual(self.answer(attempt_id, self.single, [self.multi_right[0]]).status_code, 400)

    def test_single_choice_requires_one_option(self):
        attempt_id = self.start().data['id']
        self.assertEqual(self.answer(attempt_id, self.single, [self.right, self.wrong]).status_code, 400)

    def test_overdue_attempt_expires_on_server(self):
        attempt_id = self.start().data['id']
        self.answer(attempt_id, self.single, [self.right])
        Attempt.objects.filter(pk=attempt_id).update(started_at=timezone.now() - timedelta(minutes=11))

        response = self.answer(attempt_id, self.multi, self.multi_right)

        attempt = Attempt.objects.get(pk=attempt_id)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(attempt.status, Attempt.Status.EXPIRED)
        self.assertEqual(attempt.score, 1)  # ответ, данный до конца времени, засчитан
        self.assertTrue(attempt.events.filter(event_type=ExamEvent.Type.TIME_EXPIRED).exists())

    def test_expire_command_closes_abandoned_attempts(self):
        attempt_id = self.start().data['id']
        Attempt.objects.filter(pk=attempt_id).update(started_at=timezone.now() - timedelta(hours=1))
        self.assertEqual(expire_overdue_attempts(), 1)
        self.assertEqual(Attempt.objects.get(pk=attempt_id).status, Attempt.Status.EXPIRED)

    def test_time_left(self):
        attempt_id = self.start().data['id']
        data = self.client.get(f'/api/attempts/{attempt_id}/time-left/').data
        self.assertEqual(data['status'], 'IN_PROGRESS')
        self.assertGreater(data['seconds_left'], 590)

    def test_student_cannot_see_other_students_attempt(self):
        attempt_id = self.start().data['id']
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get(f'/api/attempts/{attempt_id}/').status_code, 404)

    def test_client_event_is_logged(self):
        attempt_id = self.start().data['id']
        response = self.client.post(
            f'/api/attempts/{attempt_id}/events/', {'event_type': 'FOCUS_LOST'}, format='json'
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(ExamEvent.objects.filter(event_type=ExamEvent.Type.FOCUS_LOST).exists())

    def test_client_cannot_send_server_only_event(self):
        attempt_id = self.start().data['id']
        response = self.client.post(
            f'/api/attempts/{attempt_id}/events/', {'event_type': 'TIME_EXPIRED'}, format='json'
        )
        self.assertEqual(response.status_code, 400)


@override_settings(EXAM_CLIENT_KEY='test-key')
class KioskOnlyTests(AttemptApiTests):
    """Тест с require_kiosk: обычный браузер не может ни начать его, ни отвечать."""

    def setUp(self):
        super().setUp()
        self.test.require_kiosk = True
        self.test.save()

    def start(self, test=None, **headers):
        return super().start(test, **{**KIOSK, **headers})

    def answer(self, attempt_id, question, options, **headers):
        return super().answer(attempt_id, question, options, **{**KIOSK, **headers})

    def test_full_pass_is_graded(self):
        # finish тоже должен прийти из киоска
        attempt_id = self.start().data['id']
        self.answer(attempt_id, self.single, [self.right])
        response = self.client.post(f'/api/attempts/{attempt_id}/finish/', **KIOSK)
        self.assertEqual(response.data['result']['score'], 1)

    def test_attempt_limit(self):
        attempt_id = self.start().data['id']
        self.client.post(f'/api/attempts/{attempt_id}/finish/', **KIOSK)
        self.assertEqual(self.start().status_code, 400)

    def test_finished_attempt_cannot_be_changed(self):
        attempt_id = self.start().data['id']
        self.client.post(f'/api/attempts/{attempt_id}/finish/', **KIOSK)
        self.assertEqual(self.answer(attempt_id, self.single, [self.right]).status_code, 400)

    def test_browser_cannot_start(self):
        response = self.client.post(f'/api/tests/{self.test.pk}/start/')
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Attempt.objects.exists())

    def test_wrong_key_is_rejected(self):
        response = self.client.post(f'/api/tests/{self.test.pk}/start/', HTTP_X_EXAM_CLIENT_KEY='guess')
        self.assertEqual(response.status_code, 403)

    def test_browser_answer_is_rejected_and_logged(self):
        attempt_id = self.start().data['id']
        response = self.client.post(
            f'/api/attempts/{attempt_id}/answer/',
            {'question': self.single.pk, 'options': [self.right.pk]}, format='json',
        )
        self.assertEqual(response.status_code, 403)
        self.assertTrue(ExamEvent.objects.filter(event_type=ExamEvent.Type.NOT_KIOSK).exists())
