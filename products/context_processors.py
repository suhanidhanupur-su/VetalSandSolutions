from django.db import DatabaseError, OperationalError, ProgrammingError
from .models import Wishlist


def wishlist_count(request):
    if not request.user.is_authenticated:
        return {'wishlist_count': 0}

    try:
        return {'wishlist_count': Wishlist.objects.filter(user=request.user).count()}
    except (DatabaseError, OperationalError, ProgrammingError):
        return {'wishlist_count': 0}
