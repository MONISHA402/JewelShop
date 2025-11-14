from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),

    # CATEGORY & PRODUCT ROUTES
    path('category/<slug:slug>/', views.category_view, name='category_view'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),

    # CART
    path('cart/', views.view_cart, name='view_cart'),
    path("add-to-cart/<int:product_id>/", views.add_to_cart, name="add_to_cart"),
    path("remove-from-cart/<int:product_id>/", views.remove_from_cart, name="remove_from_cart"),
    path('update-cart/', views.update_cart, name='update_cart'),
    path('cart/remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),

    # CHECKOUT / ORDERS / PAYMENT
    path('checkout/', views.checkout, name='checkout'),
    path('place_order/', views.place_order, name='place_order'),
    path('payment/', views.payment, name='payment'),
    path('paymenthandler/', views.paymenthandler, name='paymenthandler'),
    path('order-success/<int:order_id>/', views.order_success, name='order_success'),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),
    path('my-orders/', views.my_orders, name='my_orders'),

    # AUTH
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('signup/', views.signup, name='signup'),

    # STATIC PAGES
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('help/', views.help, name='help'),
]
