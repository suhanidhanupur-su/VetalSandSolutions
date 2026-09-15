from django import forms

from .models import Order


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ('full_name', 'email', 'phone', 'address', 'city', 'state', 'pincode', 'notes', 'payment_method')
        widgets = {
            'full_name': forms.TextInput(attrs={'placeholder': 'Full name'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Email address'}),
            'phone': forms.TextInput(attrs={'placeholder': 'Phone number'}),
            'address': forms.Textarea(attrs={'placeholder': 'Street address', 'rows': 3}),
            'city': forms.TextInput(attrs={'placeholder': 'City'}),
            'state': forms.TextInput(attrs={'placeholder': 'State'}),
            'pincode': forms.TextInput(attrs={'placeholder': 'Pincode'}),
            'notes': forms.Textarea(attrs={'placeholder': 'Additional notes (optional)', 'rows': 3}),
            'payment_method': forms.RadioSelect,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['payment_method'].required = False
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'order-form-control')

    def clean_payment_method(self):
        return self.cleaned_data.get('payment_method') or Order.PaymentMethod.COD