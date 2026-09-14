from django.shortcuts import render


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