from rest_framework import serializers
from .models import Product, Order, Order_Item, Shipping_Address, Review
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken


class Review_Serializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = "__all__"

class Product_Serializer(serializers.ModelSerializer):
    reviews = serializers.SerializerMethodField (read_only=True)
    class Meta:
        model = Product
        fields = '__all__'

    def get_reviews(self,obj):
        reviews = obj.review_set.all()
        serializer = Review_Serializer(reviews, many=True)
        return serializer.data


class User_Serializer(serializers.ModelSerializer):
    is_admin = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email',
                  'last_name', 'first_name', "is_admin"]

    def get_is_admin(self, obj):
        is_admin = obj.is_staff
        return is_admin


class User_Serializer_With_Token(User_Serializer):
    token = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'last_name',
                  'first_name', "is_admin", "token"]

    def get_token(self, obj):
        token = RefreshToken.for_user(obj)
        return str(token.access_token)


class Shipping_Address_Serializer(serializers.ModelSerializer):
    class Meta:
        model = Shipping_Address
        fields = '__all__'


class Order_Item_Serializer(serializers.ModelSerializer):
    class Meta:
        model = Order_Item
        fields = '__all__'


class Order_Serializer(serializers.ModelSerializer):
    shipping_address = serializers.SerializerMethodField(read_only=True)
    order_items = serializers.SerializerMethodField(read_only=True)
    user = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Order
        fields = '__all__'

    def get_shipping_address(self, obj):
        try:
            address = Shipping_Address_Serializer(
                obj.shipping_address, many=False).data
        except:
            address = False
        return address

    def get_order_items(self, obj):
        items = obj.order_item_set.all()
        serializer = Order_Item_Serializer(items, many=True)
        return serializer.data

    def get_user(self, obj):
        user = obj.user
        serializer = User_Serializer(user, many=False)
        return serializer.data
