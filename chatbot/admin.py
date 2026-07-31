from django.contrib import admin
from .models import ChatMessage

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "question_preview", "answer_preview", "created_at")
    search_fields = ("question", "answer")
    list_filter = ("created_at",)
    readonly_fields = ("created_at",)

    def question_preview(self, obj):
        return obj.question[:50] + "..." if len(obj.question) > 50 else obj.question
    question_preview.short_description = "Question"

    def answer_preview(self, obj):
        return obj.answer[:60] + "..." if len(obj.answer) > 60 else obj.answer
    answer_preview.short_description = "AI Answer"
