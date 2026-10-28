from django.contrib import admin

from .models import AnswerOption, Question, Test, TestGroup


class TestGroupInline(admin.TabularInline):
    model = TestGroup
    extra = 1


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 0
    fields = ('order', 'text', 'question_type', 'points')
    show_change_link = True


class AnswerOptionInline(admin.TabularInline):
    model = AnswerOption
    extra = 2


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ('title', 'teacher', 'question_count', 'duration', 'max_attempts',
                    'passing_score', 'is_published', 'require_kiosk', 'created_at')
    list_filter = ('is_published', 'require_kiosk', 'teacher')
    search_fields = ('title', 'teacher__last_name')
    inlines = [TestGroupInline, QuestionInline]

    @admin.display(description='вопросов')
    def question_count(self, test):
        return test.questions.count()


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'test', 'question_type', 'points', 'order')
    list_filter = ('test', 'question_type')
    inlines = [AnswerOptionInline]
