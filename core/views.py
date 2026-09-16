from django.contrib import messages
from django.shortcuts import redirect, render

from enquiries.forms import ContactEnquiryForm, QuoteRequestForm
from enquiries.models import ContactEnquiry, QuoteRequest

from .email_notifications import send_contact_enquiry_emails, send_quote_request_emails


def home(request):
    return render(request, 'core/home.html')


def about(request):
    return render(request, 'core/about.html')


def industries(request):
    return render(request, 'core/industries.html')


def applications(request):
    return render(request, 'core/applications.html')


def portfolio(request):
    return render(request, 'core/portfolio.html')


def gallery(request):
    return render(request, 'core/gallery.html')


def contact(request):
    if request.method == 'POST':
        form = ContactEnquiryForm(request.POST)
        if form.is_valid():
            enquiry = ContactEnquiry.objects.create(
                name=form.cleaned_data['name'],
                company=form.cleaned_data.get('company', ''),
                email=form.cleaned_data['email'],
                phone=form.cleaned_data.get('phone', ''),
                message=form.cleaned_data['message'],
            )
            send_contact_enquiry_emails(enquiry)
            messages.success(request, 'Thank you. Your enquiry has been recorded and our team will review it.')
            return redirect('contact')
    else:
        form = ContactEnquiryForm()

    return render(request, 'core/contact.html', {'form': form})


def request_quote(request):
    if request.method == 'POST':
        form = QuoteRequestForm(request.POST)
        if form.is_valid():
            quote_request = QuoteRequest.objects.create(
                name=form.cleaned_data['name'],
                company=form.cleaned_data.get('company', ''),
                email=form.cleaned_data['email'],
                phone=form.cleaned_data.get('phone', ''),
                product=form.cleaned_data['product'],
                grade=form.cleaned_data['grade'],
                quantity=form.cleaned_data['quantity'],
                application=form.cleaned_data['application'],
                location=form.cleaned_data['location'],
                message=form.cleaned_data.get('message', ''),
            )
            send_quote_request_emails(quote_request)
            messages.success(request, 'Thank you. Your quote request has been recorded and our team will review it.')
            return redirect('quote')
    else:
        form = QuoteRequestForm()

    return render(request, 'core/request_quote.html', {'form': form})