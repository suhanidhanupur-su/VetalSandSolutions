from django import forms
from django.core.exceptions import ValidationError

from products.models import Product


GRADE_CHOICES = [
    ('16/30', '16/30'),
    ('24/40', '24/40'),
    ('45/50', '45/50'),
    ('50/60', '50/60'),
    ('60/70', '60/70'),
]


class ContactEnquiryForm(forms.Form):
    name = forms.CharField(max_length=150, required=True)
    company = forms.CharField(max_length=150, required=False)
    email = forms.EmailField(max_length=150, required=True)
    phone = forms.CharField(max_length=50, required=False)
    message = forms.CharField(widget=forms.Textarea, required=True)


class QuoteRequestForm(forms.Form):
    name = forms.CharField(max_length=150, required=True)
    company = forms.CharField(max_length=150, required=False)
    email = forms.EmailField(max_length=150, required=True)
    phone = forms.CharField(max_length=50, required=False)
    product = forms.ModelChoiceField(
        queryset=Product.objects.none(),
        required=True,
        empty_label='Select a product',
    )
    grade = forms.ChoiceField(choices=GRADE_CHOICES, required=True)
    quantity = forms.CharField(max_length=100, required=True)
    application = forms.CharField(max_length=150, required=True)
    location = forms.CharField(max_length=150, required=True)
    message = forms.CharField(widget=forms.Textarea, required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product'].queryset = Product.objects.filter(is_active=True).order_by('name')

    def clean_grade(self):
        grade = self.cleaned_data.get('grade')
        allowed = {value for value, label in GRADE_CHOICES}
        if grade not in allowed:
            raise ValidationError('Please choose a valid grade.')
        return grade
