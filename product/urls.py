from django.urls import path
from . import views

urlpatterns = [
    path('products/', views.getProduct, name='products'),
    path('product/latest/', views.getLatestProduct, name='latets_products'),
    path('product/<str:id>/', views.getProductDetail, name='product_detail'),
    path('login/', views.MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('product/<str:id>/review/', views.createProductReview, name='product-review'),
    path('user/profile/', views.getUserProfile, name='user_profile'),
    path('user/profile/update/', views.updateUserProfile,
         name='user_profile_update'),
    path('users/', views.getUsers, name='users'),
    path('register/', views.registerUser, name='register'),
    path('order/add/', views.orderView, name='order-add'),
    path('order/detail/<str:id>/', views.orderDetailView, name='order-detail'),
    path('order/payment/<str:id>/', views.payIntent, name='pay-intent'),
    path('order/list/', views.getOrders,name='orders-list')
]
