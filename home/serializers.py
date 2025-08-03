from rest_framework import serializers
from .models import *
from .models import Product, Category


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'phone', 'address']
        read_only_fields = ['email']


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password']

    def validate(self, data):
        data['username'] = data['username'].lower()
        data['email'] = data['email'].lower()

        if CustomUser.objects.filter(username=data['username']).exists():
            raise serializers.ValidationError({'username': 'Username already exists. Please choose another.'})

        if CustomUser.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError({'email': 'Email already exists. Please use a different email.'})

        return data

    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user
    

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        data['username'] = data['username'].lower()
        if not data['username']:
            raise serializers.ValidationError("please enter the usename")
        
        if not data['password']:
            raise serializers.ValidationError("please enter the password")

        return data
    

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'phone', 'address']
        read_only_fields = ['username', 'email']


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

    def validate_name(self, value):
    # For create
        if self.instance is None and Category.objects.filter(name=value).exists():
            raise serializers.ValidationError("Category with this name already exists.")
        # For update (exclude self)
        if self.instance and Category.objects.exclude(id=self.instance.id).filter(name=value).exists():
            raise serializers.ValidationError("Another category with this name already exists.")
        return value



class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(write_only=True)
    category = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'stock', 'category', 'category_name']

    def validate_name(self, value):
        # Only apply uniqueness check on create or if name is changed
        product_id = self.instance.id if self.instance else None
        qs = Product.objects.filter(name__iexact=value)
        if product_id:
            qs = qs.exclude(id=product_id)
        if qs.exists():
            raise serializers.ValidationError("Product with this name already exists.")
        return value

    def validate_category_name(self, value):
        if not Category.objects.filter(name__iexact=value).exists():
            raise serializers.ValidationError("Category with this name does not exist.")
        return value

    def create(self, validated_data):
        category_name = validated_data.pop('category_name')
        category = Category.objects.get(name__iexact=category_name)
        return Product.objects.create(category=category, **validated_data)

    def update(self, instance, validated_data):
        category_name = validated_data.pop('category_name', None)
        if category_name:
            category = Category.objects.get(name__iexact=category_name)
            instance.category = category

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance
    
# serializers.py



class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    class Meta:
        model = CartItem
        fields = ['id', 'product', 'price', 'quantity', 'total_price', 'product_name']
        read_only_fields = ['user']





class OrderItemSerializer(serializers.ModelSerializer):
    product = serializers.SerializerMethodField()
    class Meta:
        model = OrderItem
        fields = ['product', 'quantity', 'price']

    def get_product(self, obj):
        return {
            'name': obj.product.name,
        
        }

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True,read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'user', 'created_at', 'total_amount', 'items','status']
        read_only_fields = ['user', 'created_at', 'total_amount']

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        user = self.context['request'].user
        order = Order.objects.create(user=user)

        total = 0

        for item_data in items_data:
            product = item_data['product']
            quantity = item_data['quantity']

            # Decrease stock
            if product.stock < quantity:
                raise serializers.ValidationError(f"Not enough stock for {product.name}")

            product.stock -= quantity
            product.save()

            price = product.price * quantity
            OrderItem.objects.create(order=order, product=product, quantity=quantity, price=price)

            total += price

        order.total_amount = total
        order.save()

        return order
