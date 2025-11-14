from django.shortcuts import render, get_object_or_404, redirect
from .models import Category, Product, Cart, CartItem
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import Order, OrderItem
import razorpay
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from .forms import SignUpForm  
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.http import HttpResponseBadRequest
from django.db.models import Q
from django.contrib.auth.decorators import login_required


def home(request):
    category = request.GET.get("category")
    sort_by = request.GET.get("sort")

    products = Product.objects.all()

    if category:
       products = products.filter(category__slug=category)

    if sort_by == "low-to-high":
        products = products.order_by("price")
    elif sort_by == "high-to-low":
        products = products.order_by("-price")

    return render(request, 'shop/home.html', {"products": products})


# Category detail view (e.g., Bangles)
def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products = category.products.all()
    return render(request, 'shop/category_detail.html', {
        'category': category,
        'products': products
    })

# Product detail view
def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    return render(request, 'shop/product_detail.html', {'product': product})

# User login
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            return render(request, 'shop/login.html', {'error': 'Invalid credentials'})
    return render(request, 'shop/login.html')

# User logout
def logout_view(request):
    logout(request)
    return redirect('home')

# Checkout page
@login_required
def checkout(request):
    cart = Cart.objects.get(user=request.user)
    items = cart.items.select_related('product').all()
    total = sum(item.get_subtotal() for item in items)

    if request.method == "POST":
        print("Checkout POST received ✅")  # Debug in console
        return redirect('payment')

    return render(request, 'shop/checkout.html', {
        'items': items,
        'total': total,
    })


# Add to cart
@login_required
def add_to_cart(request, product_id):
    cart, created = Cart.objects.get_or_create(user=request.user)
    product = get_object_or_404(Product, id=product_id)

    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)

    if not created:
        cart_item.quantity += 1

    cart_item.save()
    return redirect('view_cart')

# Remove from cart
@login_required
def remove_from_cart(request, product_id):
    cart = get_object_or_404(Cart, user=request.user)
    product = get_object_or_404(Product, id=product_id)

    CartItem.objects.filter(cart=cart, product=product).delete()
    return redirect('view_cart')

@login_required
def update_cart(request):
    cart = get_object_or_404(Cart, user=request.user)

    if request.method == "POST":
        for key, value in request.POST.items():

            if key.startswith("quantity_"):
                try:
                    cart_item_id = int(key.split("_")[1])
                    quantity = int(value)

                    cart_item = CartItem.objects.get(id=cart_item_id, cart=cart)

                    if quantity > 0:
                        cart_item.quantity = quantity
                        cart_item.save()
                    else:
                        cart_item.delete()

                except CartItem.DoesNotExist:
                    print(f"CartItem not found: {cart_item_id}")
                except ValueError:
                    print(f"Invalid quantity value: {value}")

    return redirect("view_cart")


# View cart
@login_required
def view_cart(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    items = CartItem.objects.filter(cart=cart)

    total = sum(item.product.price * item.quantity for item in items)

    return render(request, 'shop/cart.html', {
        "items": items,
        "total": total
    })


# oreder,orderItem
@login_required
def place_order(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    items = cart.items.select_related('product').all()

    if not items:
        return redirect('view_cart')  # No items to order

    total = sum(item.get_subtotal() for item in items)

    # Create Order
    order = Order.objects.create(user=request.user, total_amount=total)

    # Create OrderItems
    for item in items:
        OrderItem.objects.create(
            order=order,
            product=item.product,
            quantity=item.quantity,
            price=item.product.price,
        )

    # Clear the cart
    cart.items.all().delete()

    return render(request, 'shop/order_success.html', {'order': order})

# payment
@login_required
def payment(request):
    cart = Cart.objects.get(user=request.user)
    items = cart.items.select_related('product').all()

    total_rupees = sum(item.get_subtotal() for item in items)  # keep total in rupees
    total_paise = int(total_rupees * 100)  # convert only once to paise

    # Razorpay max allowed = ₹500000; prevent exceeding it
    if total_rupees > 500000:
        messages.error(request, "Order amount exceeds Razorpay maximum limit (₹5 Lakhs).")
        return redirect("checkout")

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    razorpay_order = client.order.create({
        "amount": total_paise,
        "currency": "INR",
        "payment_capture": "1"
    })

    context = {
        'items': items,
        'total': total_rupees,    # show rupees in UI
        'razorpay_order_id': razorpay_order['id'],
        'razorpay_merchant_key': settings.RAZORPAY_KEY_ID,
        'callback_url': '/paymenthandler/',
    }
    return render(request, 'shop/payment.html', context)

# paymenthandler
@csrf_exempt
def paymenthandler(request):
    if request.method == "POST":
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

        try:
            payment_id = request.POST.get('razorpay_payment_id', '')
            order_id = request.POST.get('razorpay_order_id', '')
            signature = request.POST.get('razorpay_signature', '')

            client.utility.verify_payment_signature({
                'razorpay_order_id': order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            })

            cart = Cart.objects.get(user=request.user)
            items = cart.items.select_related('product').all()
            total = sum(item.get_subtotal() for item in items)

            order = Order.objects.create(
                user=request.user,
                total_amount=total,
                is_paid=True,
                razorpay_order_id=order_id,
                razorpay_payment_id=payment_id,
                razorpay_signature=signature
            )

            for item in items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.product.price,
                )

            cart.items.all().delete()

            return redirect('order_success', order_id=order.id)

        except razorpay.errors.SignatureVerificationError:
            return HttpResponseBadRequest("Payment verification failed.")

# signup    
def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)  # log the user in after signup
            messages.success(request, 'Account created and logged in.')
            return redirect('home')
    else:
        form = SignUpForm()
    return render(request, 'shop/signup.html', {'form': form})

# order sucess
@login_required
def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'shop/order_success.html', {'order': order})


def about(request):
    return render(request, 'shop/about.html')

def contact(request):
    return render(request, 'shop/contact.html')

def help(request):
    return render(request, 'shop/help.html')

# category
def category_view(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products = Product.objects.filter(category=category, available=True)

    sort_option = request.GET.get('sort')
    if sort_option == 'low-to-high':
        products = products.order_by('price')
    elif sort_option == 'high-to-low':
        products = products.order_by('-price')

    context = {
        'category': category,
        'products': products,
    }
    return render(request, 'shop/category.html', context)
# my_order
@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'shop/my_orders.html', {'orders': orders})

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    items = order.items.select_related('product').all()

    context = {
        'order': order,
        'items': items,
    }
    return render(request, 'shop/order_detail.html', context)