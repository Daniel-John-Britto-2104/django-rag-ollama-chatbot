from django.contrib import admin
from .models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "title",
        "uploaded_at",
    )

    search_fields = (
        "title",
        "content",
    )

    list_filter = (
        "uploaded_at",
    )

    readonly_fields = (
        "uploaded_at",
    )