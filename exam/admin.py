from django.contrib import admin
from .models import Student, Subject, Question, Result

admin.site.register(Student)
admin.site.register(Subject)
admin.site.register(Question)
admin.site.register(Result)
