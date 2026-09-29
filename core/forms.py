from django import forms

from .models import ContactMessage


class ContactForm(forms.ModelForm):
    """
    Contact form. "website" is a honeypot: it's hidden from people, so only
    bots fill it in, and a filled-in form is quietly dropped.
    """

    website = forms.CharField(
        required=False,
        label="Leave this field empty",
        widget=forms.TextInput(
            attrs={"autocomplete": "off", "tabindex": "-1"}
        ),
    )

    class Meta:
        model = ContactMessage
        fields = ["name", "email", "subject", "message"]
        labels = {"name": "Your name", "email": "Your email"}
        widgets = {
            "name": forms.TextInput(attrs={"autocomplete": "name"}),
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
            "message": forms.Textarea(attrs={"rows": 6}),
        }
        error_messages = {
            "name": {"required": "Please tell us your name."},
            "email": {
                "required": "Please enter your email so we can reply.",
                "invalid": "Please enter a valid email address.",
            },
            "subject": {"required": "Please choose what your message is about."},
            "message": {"required": "Please write your message."},
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["subject"].choices = [
            ("", "Choose a topic"),
        ] + ContactMessage.SUBJECT_CHOICES

    def clean_message(self):
        message = self.cleaned_data["message"].strip()
        if len(message) < 10:
            raise forms.ValidationError(
                "Please write a little more so we can help (10+ characters)."
            )
        return message

    @property
    def is_spam(self):
        """True when the hidden honeypot field was filled in."""
        return bool(self.cleaned_data.get("website"))
