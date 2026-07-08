from django.db import models
from django.urls import reverse

class Look(models.Model):
    """A single spread in the lookbook. Ordered by look_number, which is a real
    sequence (the order the collection was shot/dropped in) — not decoration."""
 
    title = models.CharField(max_length=120, help_text="e.g. 'Midnight Run'")
    slug = models.SlugField(unique=True)
    look_number = models.PositiveIntegerField(unique=True, help_text="Position in the lookbook, e.g. 1 for LOOK 01")
    season = models.CharField(max_length=60, blank=True, help_text="e.g. 'FW25' — shown as a small tag")
    image = models.ImageField(upload_to="lookbook/")
    caption = models.CharField(max_length=200, blank=True, help_text="Short editorial line under the title")
    model_name = models.CharField(max_length=120, blank=True)
    photographer_credit = models.CharField(max_length=120, blank=True)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
 
    class Meta:
        ordering = ["look_number"]
        verbose_name = "Look"
        verbose_name_plural = "Lookbook"
 
    def __str__(self):
        return f"Look {self.look_number:02d} — {self.title}"
 
    def get_absolute_url(self):
        return reverse("store:lookbook_detail", args=[self.slug])