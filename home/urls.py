from django.urls import path,include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import *
from rest_framework.routers import DefaultRouter
from django.views.generic import TemplateView

router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'cart', CartItemViewSet, basename='cart')


urlpatterns = [
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', RegisterView.as_view(), name='register'),
    path('register-page/', TemplateView.as_view(template_name="registration/register.html"), name='register_page'),
    path('login/', LoginView.as_view(), name='login'),
    path('login-page/', TemplateView.as_view(template_name="registration/login.html"), name='login_page'),
    path('', TemplateView.as_view(template_name="products/product_list.html"), name='products_page'),
    path('product/<int:id>/', TemplateView.as_view(template_name='products/product_detail.html')),
    path('categories-page/', TemplateView.as_view(template_name="admin_categories.html"), name='categories_page'),
    path('admin-products-page/', TemplateView.as_view(template_name="admin_products.html"), name='products_page'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('place-order/', PlaceOrderView.as_view(), name='place-order'),
  # Your urls.py
    path('user-profile/', UserProfileView.as_view(), name='user-profile'), 
    path('profile-page/', TemplateView.as_view(template_name='profile.html'), name='profile-page'),  # HTML page

    path("cart-page/", TemplateView.as_view(template_name="cart-page.html")),
    path('my-orders/', MyOrdersAPIView.as_view(), name='my-orders-api'),  # 👈 API (returns JSON)
    path('my-orders-page/', TemplateView.as_view(template_name='my-orders-page.html'), name='my-orders-page'),  # 👈 HTML Page

    path('', include(router.urls)),
]
