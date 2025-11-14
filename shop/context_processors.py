from .models import Category, Cart
from django.conf import settings

def common_data(request):
    categories = Category.objects.all()
    cart_count = 0
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            cart_count = cart.items.count()
        except Cart.DoesNotExist:
            cart_count = 0
    return {'categories': categories, 'cart_count': cart_count}
