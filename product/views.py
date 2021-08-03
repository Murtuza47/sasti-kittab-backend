import re
from rest_framework.response import Response
from django.conf import settings
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from stripe.api_resources import source
from .models import Product, Order, Order_Item, Review, Shipping_Address
from .serialize import Product_Serializer, Review_Serializer, User_Serializer, User_Serializer_With_Token, Order_Serializer
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.core.paginator import Paginator, EmptyPage,PageNotAnInteger

from product import serialize
from datetime import date, datetime
import stripe


stripe.api_key = settings.STRIPE_SECRET_KEY


# Create your views here.

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attr):
        data = super().validate(attr)
        serialize = User_Serializer_With_Token(self.user).data
        for key, value in serialize.items():
            data[key] = value
        return data


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


@api_view(['GET'])
def getProduct(request):
    query = request.query_params.get('keyword')
    if query == None:
        query = ''

    product = Product.objects.filter(name__icontains=query)

    page = request.query_params.get('page')
    paginator = Paginator(product, 8 )

    try:
        product = paginator.page(page)
    except PageNotAnInteger:
        product = paginator.page(1)
    except EmptyPage:
        product = paginator.page(paginator.num_pages)

    if page == None:
        page = 1
    
    page = int(page)
    serialize = Product_Serializer(product, many=True)
    return Response({"products": serialize.data, "page":page, "pages":paginator.num_pages})

@api_view(['GET'])
def getLatestProduct(request):
    product = Product.objects.filter(rating__gte=4).order_by('-rating')[0:5]
    serialize = Product_Serializer(product, many=True)
    return Response(serialize.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getUserProfile(request):
    user = request.user
    serialize = User_Serializer(user, many=False)
    return Response(serialize.data)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def getUsers(request):
    users = User.objects.all()
    serialize = User_Serializer(users, many=True)
    return Response(serialize.data)


@api_view(['GET'])
def getProductDetail(request, id):
    product = Product.objects.get(id=id)
    serialize = Product_Serializer(product, many=False)
    return Response(serialize.data)


@api_view(['POST'])
def registerUser(request):
    data = request.data
    try:
        user = User.objects.create(
            username=data['username'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            email=data['email'],
            password=make_password(data['password'])

        )
        serialize = User_Serializer_With_Token(user, many=False)
        return Response(serialize.data)

    except:
        message = {'detail': 'User with this email already exist'}
        return Response(message, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def updateUserProfile(request):
    user = request.user
    serialize = User_Serializer_With_Token(user, many=False)
    data = request.data
    user.first_name = data['first_name']
    user.last_name = data['last_name']
    user.email = data['email']
    user.username = data['username']
    if data['password']:
        user.password = make_password(data['password'])
    user.save()

    return Response(serialize.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def orderView(request):
    user = request.user
    data = request.data

    orderItems = data['orderItems']

    if orderItems and len(orderItems) == 0:
        return Response({"detail": "No Order Item"}, status=status.HTTP_400_BAD_REQUEST)
    else:
        # Create Order
        order = Order.objects.create(
            user=user,
            payment_method=data['paymentMethod'],
            tax_price=data['taxPrice'],
            shipping_price=data['shippingPrice'],
            total_price=data['totalPrice']
        )
        # Create Shipping Address
        Shipping_Address.objects.create(
            order=order,
            address=data['address'],
            city=data['city'],
            postal_code=data['postalCode'],
            country=data['country']
        )

        # Create OrderItems and set order to orderItem relatrion
        for product in orderItems:
            productObject = Product.objects.get(id=product["id"])
            orderItem = Order_Item.objects.create(
                product=productObject,
                order=order,
                name=productObject.name,
                quantity=product['qty'],
                price=product['price'],
                image=productObject.image.url
            )
            # Update  Stock
            productObject.in_stock -= orderItem.quantity
            productObject.save()

        serializer = Order_Serializer(order, many=False)
        return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def orderDetailView(request, id):
    user = request.user
    try:
        order = Order.objects.get(id=id)
        if user.is_staff or order.user == user:
            serializer = Order_Serializer(order, many=False)
            return Response(serializer.data)
        else:
            return Response({"detail": "User is not Authorized"}, status=status.HTTP_400_BAD_REQUEST)
    except:
        return Response({"detail": "Order doesnot exist"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def payIntent(request,id):
    try:
        order = Order.objects.get(id=id)
        token = request.data.get('token')
        print("request",request.data)
        print("token",token)
        intent = stripe.Charge.create(
            amount=order.total_price * 100,
            currency='usd',
            source=token
        )
        # order.is_paid = True
        # order.paid_at = datetime.now()
        # order.save()
        # print(intent)
        return Response('Order is paid')
        
    except Exception as e:
        return Response({"detail": e}, status=status.HTTP_400_BAD_REQUEST)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def createProductReview(request,id):
    user = request.user
    data = request.data
    product = Product.objects.get(id=id)
    total = 0

    # Review already exist
    already_exist = product.review_set.filter(user=user).exists()
    if already_exist:
        return Response({"detail": "Product already reviewed"}, status=status.HTTP_400_BAD_REQUEST)
     
    # No rating or 0
    elif data.get('rating') == 0:
        return Response({"detail": "Please add a rating to the product"}, status=status.HTTP_400_BAD_REQUEST)
    # Create Review 
    else:
        review = Review.objects.create(
            user = user,
            product = product,
            name = data.get("name"),
            rating = data.get("rating"),
            comment = data.get("comment")
        )
        
        reviews = product.review_set.all()
        product.num_reviews = len(reviews)

        for i in reviews:
            total += i.rating
        
        product.rating = total / len(reviews)
        product.save()

        serialize = Review_Serializer(review,many=False)
        return Response(serialize.data)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getOrders(request):
    user = request.user
    orders = user.order_set.all()
    serialize = Order_Serializer(orders, many=True)
    return Response(serialize.data)
