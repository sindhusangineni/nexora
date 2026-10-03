from django.contrib import admin

from apps.question_bank.models import (
    AssertionReasonContent,
    DescriptiveContent,
    MatchFollowingContent,
    MatchFollowingItem,
    MatchFollowingPair,
    Question,
    QuestionTopic,
    QuestionVersion,
    QuestionVersionChoice,
    TrueFalseContent,
)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("id", "created_at", "updated_at")
    readonly_fields = ("id", "created_at", "updated_at")


class QuestionVersionChoiceInline(admin.TabularInline):
    model = QuestionVersionChoice
    extra = 0


@admin.register(QuestionVersion)
class QuestionVersionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "question",
        "version_number",
        "question_type",
        "difficulty",
        "status",
        "source_type",
    )
    list_filter = ("question_type", "difficulty", "status", "source_type")
    search_fields = ("text", "question__id")
    readonly_fields = ("id", "created_at", "updated_at")
    inlines = [QuestionVersionChoiceInline]


@admin.register(QuestionTopic)
class QuestionTopicAdmin(admin.ModelAdmin):
    list_display = ("id", "question", "topic", "created_at")
    search_fields = ("question__id", "topic__name")


admin.site.register(TrueFalseContent)
admin.site.register(AssertionReasonContent)
admin.site.register(MatchFollowingContent)
admin.site.register(MatchFollowingItem)
admin.site.register(MatchFollowingPair)
admin.site.register(DescriptiveContent)
