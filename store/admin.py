from django.contrib import admin
from django.utils.html import format_html
from .models import Look

@admin.register(Look)
class LookAdmin(admin.ModelAdmin):
    list_display = (
        "look_number",
        "thumbnail",
        "title",
        "season",
        "model_name",
        "is_published",
    )
    list_display_links = ("thumbnail", "title")
    list_editable = ("look_number", "is_published")
    list_filter = ("is_published", "season")
    search_fields = ("title", "model_name", "photographer_credit")
    prepopulated_fields = {"slug": ("title",)}
    ordering = ("look_number",)
 
    fieldsets = (
        (None, {"fields": ("look_number", "title", "slug", "image", "caption")}),
        ("Credits", {"fields": ("season", "model_name", "photographer_credit")}),
        ("Visibility", {"fields": ("is_published",)}),
    )
 
    @admin.display(description="Preview")
    def thumbnail(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="height:48px;width:38px;object-fit:cover;border:1px solid #333;">',
                obj.image.url,
            )
        return "—"