import logging

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def _send_email(subject, message, recipient):
    if not recipient:
        logger.warning('Email notification skipped because no recipient was configured.')
        return False

    email_backend = getattr(settings, 'EMAIL_BACKEND', '')
    smtp_configured = all(
        getattr(settings, setting_name, '')
        for setting_name in ('EMAIL_HOST', 'EMAIL_HOST_USER', 'EMAIL_HOST_PASSWORD', 'DEFAULT_FROM_EMAIL')
    )
    test_backend = email_backend == 'django.core.mail.backends.locmem.EmailBackend'
    if not test_backend and (
        email_backend != 'django.core.mail.backends.smtp.EmailBackend' or not smtp_configured
    ):
        logger.warning('Email notification skipped because SMTP is not fully configured.')
        return False

    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [recipient],
            fail_silently=False,
        )
    except Exception:
        logger.exception('Email notification failed for recipient %s.', recipient)
        return False
    return True


def send_order_request_email(order):
    products = '\n'.join(
        f'- {item.product.name} (Quantity: {item.quantity})'
        for item in order.items.select_related('product').all()
    )
    message = (
        f'Order Number: #{order.id}\n'
        f'Customer Name: {order.full_name}\n'
        f'Payment Method: {order.get_payment_method_display()}\n'
        f'Products:\n{products}\n'
        f'Status: {order.get_status_display()}\n'
    )
    _send_email(
        'Vetal Sand Solutions - Order Request Received',
        message,
        order.email,
    )


def send_payment_confirmation_email(order):
    message = (
        f'Order Number: #{order.id}\n'
        f'Customer Name: {order.full_name}\n'
        f'Payment Method: {order.get_payment_method_display()}\n'
        f'Payment Status: Payment received\n'
        f'Total Amount: {order.total_amount or "-"}\n'
    )
    return _send_email(
        'Vetal Sand Solutions - Payment Confirmation',
        message,
        order.email,
    )


def send_contact_enquiry_emails(enquiry):
    details = (
        f'Name: {enquiry.name}\n'
        f'Company: {enquiry.company or "-"}\n'
        f'Email: {enquiry.email}\n'
        f'Phone: {enquiry.phone or "-"}\n'
        f'Message:\n{enquiry.message}\n'
    )
    _send_email(
        'Vetal Sand Solutions - Enquiry Received',
        f'Thank you for contacting Vetal Sand Solutions.\n\n{details}',
        enquiry.email,
    )
    _send_email(
        'Vetal Sand Solutions - New Contact Enquiry',
        details,
        settings.COMPANY_NOTIFICATION_EMAIL,
    )


def send_quote_request_emails(quote_request):
    details = (
        f'Name: {quote_request.name}\n'
        f'Company: {quote_request.company or "-"}\n'
        f'Email: {quote_request.email}\n'
        f'Phone: {quote_request.phone or "-"}\n'
        f'Product: {quote_request.product.name if quote_request.product else "-"}\n'
        f'Grade: {quote_request.grade}\n'
        f'Quantity: {quote_request.quantity}\n'
        f'Application: {quote_request.application}\n'
        f'Location: {quote_request.location}\n'
        f'Message:\n{quote_request.message}\n'
    )
    _send_email(
        'Vetal Sand Solutions - Quote Request Received',
        f'Thank you for your quote request. Our team will review it shortly.\n\n{details}',
        quote_request.email,
    )
    _send_email(
        'Vetal Sand Solutions - New Quote Request',
        details,
        settings.COMPANY_NOTIFICATION_EMAIL,
    )
