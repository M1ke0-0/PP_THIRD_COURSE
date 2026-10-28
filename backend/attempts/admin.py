from django.contrib import admin

from .models import Attempt, ExamEvent, StudentAnswer


class StudentAnswerInline(admin.TabularInline):
    model = StudentAnswer
    extra = 0
    fields = ('question', 'selected', 'is_correct', 'points', 'answered_at')
    readonly_fields = fields
    can_delete = False

    @admin.display(description='выбрано')
    def selected(self, answer):
        return ', '.join(option.text for option in answer.selected_answers.all())

    def has_add_permission(self, request, obj=None):
        return False


class ExamEventInline(admin.TabularInline):
    model = ExamEvent
    extra = 0
    readonly_fields = ('created_at', 'event_type', 'details')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Attempt)
class AttemptAdmin(admin.ModelAdmin):
    list_display = ('student', 'test', 'status', 'started_at', 'score', 'max_score',
                    'percent', 'violations')
    list_filter = ('status', 'test')
    search_fields = ('student__username', 'student__last_name')
    readonly_fields = ('test', 'student', 'started_at', 'finished_at', 'score', 'max_score',
                       'correct_answers', 'total_questions', 'status')
    inlines = [StudentAnswerInline, ExamEventInline]

    @admin.display(description='%')
    def percent(self, attempt):
        return attempt.percent

    @admin.display(description='событий в журнале')
    def violations(self, attempt):
        return attempt.events.count()


@admin.register(ExamEvent)
class ExamEventAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'event_type', 'attempt')
    list_filter = ('event_type',)
    readonly_fields = ('attempt', 'event_type', 'created_at', 'details')
