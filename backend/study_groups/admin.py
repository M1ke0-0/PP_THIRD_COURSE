from django.contrib import admin

from .models import Group, GroupStudent


class GroupStudentInline(admin.TabularInline):
    model = GroupStudent
    extra = 1
    autocomplete_fields = ['student']


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'student_count')
    search_fields = ('name',)
    inlines = [GroupStudentInline]

    @admin.display(description='студентов')
    def student_count(self, group):
        return group.students.count()
