"""
Forms for API key management.
"""

from django import forms
from django.core.exceptions import ValidationError

from .api_keys import APIKey


class APIKeyForm(forms.ModelForm):
    """Form for creating/editing API keys"""
    
    # Override to show as password input
    key_value = forms.CharField(
        label="API Key",
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Enter API key (will be encrypted)",
            "autocomplete": "new-password",
        }),
        required=False,
        help_text="Enter the API key value. It will be encrypted before storage.",
    )
    
    class Meta:
        model = APIKey
        fields = [
            "name",
            "provider",
            "description",
            "is_global",
            "is_active",
            "expires_at",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "provider": forms.Select(attrs={"class": "form-select"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "is_global": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "expires_at": forms.DateTimeInput(attrs={
                "class": "form-control",
                "type": "datetime-local",
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set initial key value if editing (but don't show actual key)
        if self.instance and self.instance.pk:
            self.fields["key_value"].help_text = "Leave blank to keep existing key. Enter new value to update."
            self.fields["key_value"].required = False
        else:
            self.fields["key_value"].required = True
        
        # Add provider choices
        self.fields["provider"].widget = forms.Select(
            attrs={"class": "form-select"},
            choices=self._get_provider_choices()
        )
    
    def _get_provider_choices(self):
        """Get provider choices"""
        return [
            ("", "Select provider..."),
            ("openai", "OpenAI"),
            ("gemini", "Google Gemini (Google AI)"),
            ("binance", "Binance"),
            ("binance_secret", "Binance Secret"),
            ("discord", "Discord Webhook"),
            ("polygon", "Polygon"),
            ("coinmarketcap", "CoinMarketCap"),
            ("alpha_vantage", "Alpha Vantage"),
            ("other", "Other"),
        ]
    
    def clean_name(self):
        """Validate name is unique"""
        name = self.cleaned_data.get("name")
        if name:
            # Check if name already exists (excluding current instance)
            qs = APIKey.objects.filter(name=name)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(f"An API key with name '{name}' already exists.")
        return name
    
    def clean(self):
        """Validate form data"""
        cleaned_data = super().clean()
        
        # If creating new key, key_value is required
        if not self.instance.pk and not cleaned_data.get("key_value"):
            raise ValidationError({"key_value": "API key value is required for new keys."})
        
        return cleaned_data
    
    def save(self, commit=True, user=None):
        """Save the API key with encryption"""
        instance = super().save(commit=False)
        
        # Set created_by if provided
        if user and not instance.created_by:
            instance.created_by = user
        
        # Encrypt and store the key if provided
        key_value = self.cleaned_data.get("key_value")
        if key_value:
            instance.key = key_value
        
        if commit:
            instance.save()
        
        return instance


class APIKeyDeleteForm(forms.Form):
    """Form for confirming API key deletion"""
    confirm = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        label="I confirm I want to delete this API key",
    )

