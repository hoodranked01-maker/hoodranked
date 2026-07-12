from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "phone", "address", "city", "state"]
        widgets = {
            "address": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # No CSS classes needed here — profile.html styles inputs by type/tag
        # selector (same pattern as the auth pages), so this just adds the
        # placeholder/autocomplete hints that make the form usable.
        placeholders = {
            "first_name": "David",
            "last_name": "Adeyemi",
            "email": "you@example.com",
            "phone": "+234 800 000 0000",
            "address": "Street address, apartment, etc.",
            "city": "Lagos",
            "state": "Lagos State",
        }
        autocomplete = {
            "first_name": "given-name",
            "last_name": "family-name",
            "email": "email",
            "phone": "tel",
            "address": "street-address",
            "city": "address-level2",
            "state": "address-level1",
        }
        for name, field in self.fields.items():
            if name in placeholders:
                field.widget.attrs.setdefault("placeholder", placeholders[name])
            if name in autocomplete:
                field.widget.attrs.setdefault("autocomplete", autocomplete[name])