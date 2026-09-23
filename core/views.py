from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect, render

from enquiries.forms import ContactEnquiryForm, QuoteRequestForm
from enquiries.models import ContactEnquiry, QuoteRequest
from products.models import Product

from .email_notifications import send_contact_enquiry_emails, send_quote_request_emails
from .models import GalleryImage


def home(request):
    products = list(Product.objects.filter(is_active=True).select_related('category')[:5])
    focus_gallery_image = GalleryImage.objects.filter(
        is_active=True,
        category__iexact='Work in Focus',
    ).first()

    return render(request, 'core/home.html', {
        'home_products': products,
        'focus_gallery_image': focus_gallery_image,
    })


def about(request):
    return render(request, 'core/about.html')


def industries(request):
    return render(request, 'core/industries.html')


def applications(request):
    return render(request, 'core/applications.html')


def portfolio(request):
    return render(request, 'core/portfolio.html')


def gallery(request):
    gallery_images = list(GalleryImage.objects.filter(is_active=True))
    return render(request, 'core/gallery.html', {'gallery_images': gallery_images})



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


def system_status(request):
    import traceback
    from django.http import JsonResponse
    from django.db import connection
    from django.db.migrations.recorder import MigrationRecorder
    from products.models import Category, Product
    from django.contrib.auth import get_user_model

    data = {
        'status': 'ok',
        'database': {},
    }
    try:
        connection.ensure_connection()
        engine = connection.settings_dict.get('ENGINE', '')
        raw_host = connection.settings_dict.get('HOST', '')
        if raw_host:
            masked_host = raw_host.split('@')[-1]
        else:
            masked_host = 'local-or-sqlite'

        recorder = MigrationRecorder(connection)
        applied_migrations = len(recorder.applied_migrations())

        user_count = get_user_model().objects.count()
        product_count = Product.objects.count()
        active_product_count = Product.objects.filter(is_active=True).count()
        category_count = Category.objects.count()

        data['database'] = {
            'connected': True,
            'engine': engine.split('.')[-1],
            'host': masked_host,
            'applied_migrations_count': applied_migrations,
            'users_count': user_count,
            'products_total': product_count,
            'products_active': active_product_count,
            'categories_count': category_count,
        }
        data['razorpay'] = {
            'configured': getattr(settings, 'RAZORPAY_CONFIGURED', False),
            'test_mode': getattr(settings, 'RAZORPAY_TEST_MODE', True),
            'currency': getattr(settings, 'RAZORPAY_CURRENCY', 'INR'),
            'key_id_set': bool(getattr(settings, 'RAZORPAY_KEY_ID', '')),
            'key_prefix': settings.RAZORPAY_KEY_ID[:8] if getattr(settings, 'RAZORPAY_KEY_ID', '') else '',
            'secret_set': bool(getattr(settings, 'RAZORPAY_KEY_SECRET', '')),
            'matching_env_keys': [
                k for k in sorted(os.environ.keys())
                if any(t in k.upper() for t in ('RAZOR', 'RZP', 'PAYMENT'))
            ],
            'vercel_env': os.environ.get('VERCEL_ENV', 'unknown'),
        }
    except Exception as exc:
        data['status'] = 'error'
        data['error_type'] = exc.__class__.__name__
        data['error_message'] = str(exc)
        data['traceback'] = traceback.format_exc()

    return JsonResponse(data)