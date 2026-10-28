from rest_framework import serializers

from attempts.models import Attempt, ExamEvent
from attempts.services import seconds_left
from testing.models import AnswerOption, Question, Test


class TestSerializer(serializers.ModelSerializer):
    teacher = serializers.CharField(source='teacher.get_full_name')
    question_count = serializers.IntegerField(source='questions.count')
    attempts_used = serializers.SerializerMethodField()

    class Meta:
        model = Test
        fields = [
            'id', 'title', 'description', 'teacher', 'question_count', 'duration',
            'max_attempts', 'attempts_used', 'passing_score', 'require_kiosk',
        ]

    def get_attempts_used(self, test):
        return test.attempts.filter(student=self.context['request'].user).count()


class OptionSerializer(serializers.ModelSerializer):
    """Вариант ответа без поля is_correct — правильные ответы студенту не отдаются."""

    class Meta:
        model = AnswerOption
        fields = ['id', 'text']


class QuestionSerializer(serializers.ModelSerializer):
    options = OptionSerializer(many=True)

    class Meta:
        model = Question
        fields = ['id', 'text', 'question_type', 'points', 'options']


class AttemptSerializer(serializers.ModelSerializer):
    test = serializers.CharField(source='test.title')
    deadline = serializers.DateTimeField()
    seconds_left = serializers.SerializerMethodField()
    questions = QuestionSerializer(source='test.questions', many=True)
    answers = serializers.SerializerMethodField()
    result = serializers.SerializerMethodField()

    class Meta:
        model = Attempt
        fields = [
            'id', 'test', 'status', 'started_at', 'deadline', 'seconds_left',
            'questions', 'answers', 'result',
        ]

    def get_seconds_left(self, attempt):
        return seconds_left(attempt)

    def get_answers(self, attempt):
        """Сохранённые ответы: {id вопроса: [id выбранных вариантов]}."""
        return {
            answer.question_id: list(answer.selected_answers.values_list('pk', flat=True))
            for answer in attempt.answers.all()
        }

    def get_result(self, attempt):
        if not attempt.is_finished:
            return None
        return {
            'score': attempt.score,
            'max_score': attempt.max_score,
            'correct_answers': attempt.correct_answers,
            'total_questions': attempt.total_questions,
            'percent': attempt.percent,
            'passing_score': attempt.test.passing_score,
            'is_passed': attempt.is_passed,
        }


class AnswerInputSerializer(serializers.Serializer):
    question = serializers.IntegerField()
    options = serializers.ListField(child=serializers.IntegerField(), min_length=1)


class EventInputSerializer(serializers.Serializer):
    event_type = serializers.ChoiceField(choices=ExamEvent.CLIENT_TYPES)
    details = serializers.DictField(required=False, default=dict)
