from django.contrib import admin

from .models import Chapter, Domain, Subject, Topic


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at", "updated_at")
    search_fields = ("name",)


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("name", "domain", "position", "created_at")
    list_filter = ("domain",)
    search_fields = ("name",)


@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ("name", "subject", "position", "created_at")
    list_filter = ("subject__domain", "subject")
    search_fields = ("name",)


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ("name", "chapter", "position", "created_at")
    list_filter = ("chapter__subject", "chapter")
    search_fields = ("name",)
