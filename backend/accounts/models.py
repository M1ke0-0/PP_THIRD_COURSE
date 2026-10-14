from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Администратор'
        TEACHER = 'TEACHER', 'Преподаватель'
        STUDENT = 'STUDENT', 'Студент'

    role = models.CharField(max_length=16, choices=Role.choices, default=Role.STUDENT)

    @property
    def is_admin_role(self):
        return self.role == self.Role.ADMIN or self.is_superuser

    @property
    def is_teacher(self):
        return self.role == self.Role.TEACHER

    @property
    def is_student(self):
        return self.role == self.Role.STUDENT
