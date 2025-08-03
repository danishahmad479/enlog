from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import *
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from .models import *
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAdminUser
from django.shortcuts import render
from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from decimal import Decimal
from django.db import transaction
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.viewsets import ModelViewSet



class RegisterView(APIView):
    def post(self,request):
        try:
            data = request.data
            serializer = RegisterSerializer(data = data)
            if serializer.is_valid():
                serializer.save()
                user = CustomUser.objects.get(username = serializer.data['username'])
                refresh = RefreshToken.for_user(user) 
                return Response({'status' : status.HTTP_200_OK,
                                "payload" : serializer.data,
                                'refresh': str(refresh),
                                'access': str(refresh.access_token),
                                'message' : "your data is saved"
                                },status = status.HTTP_200_OK)  
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'status': status.HTTP_500_INTERNAL_SERVER_ERROR, 'message': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LoginView(APIView):
    def post(self,request):
        try:
            data = request.data
            serializer = LoginSerializer(data = data)
            if serializer.is_valid():
                user = authenticate(username = serializer.data['username'] , password = serializer.data['password'])
                print(user)
                if user:            
                    refresh = RefreshToken.for_user(user)
                    return Response({
                        'status': status.HTTP_200_OK,
                        'refresh': str(refresh),
                        'access': str(refresh.access_token),
                        'message': 'Login successful',
                        "is_staff": user.is_staff,
                        'user_id': user.id,
                    },status= status.HTTP_200_OK)
                else:
                    return Response({'status':status.HTTP_401_UNAUTHORIZED,'message':'Invalid Credentials'},status=status.HTTP_401_UNAUTHORIZED)
            else:
                return Response({'status':status.HTTP_401_UNAUTHORIZED,'message':"Invalid Credentials!.Please Register"})
        except Exception as e:
                return Response({'status': status.HTTP_500_INTERNAL_SERVER_ERROR, 'message': str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "Logged out successfully"}, status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)




class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            serializer = ProfileSerializer(request.user)
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=500)

    def put(self, request):
        try:
            serializer = ProfileSerializer(request.user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({'message': 'Profile updated successfully'})
            return Response(serializer.errors, status=400)
        except Exception as e:
            return Response({'error': str(e)}, status=500)
        

class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user and request.user.is_staff

class CategoryViewSet(ModelViewSet):
    queryset = Category.objects.all().order_by('id')
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]



class ReadOnlyOrAdmin(BasePermission):
    def has_permission(self, request, view):
        # Allow safe methods (GET, HEAD, OPTIONS) for everyone
        if request.method in SAFE_METHODS:
            return True
        # Only allow other methods for admin
        return request.user and request.user.is_staff



class ProductViewSet(ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [ReadOnlyOrAdmin, IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['category', 'price']  # category ID and price filter

    def get_queryset(self):
        queryset = Product.objects.select_related('category').order_by('id')

        # Optional custom range filter
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        category_id = self.request.query_params.get('category')

        if category_id:
            queryset = queryset.filter(category_id=category_id)
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        return queryset
    


class CartItemViewSet(ModelViewSet):
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]

        
    def get_queryset(self):
        return CartItem.objects.filter(user=self.request.user)\
        .select_related('product')\
        .order_by('-id')


    def perform_create(self, serializer):
        serializer.save(user=self.request.user)




class PlaceOrderView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        user = request.user
        cart_items = CartItem.objects.filter(user=user)

        if not cart_items.exists():
            return Response({"detail": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)

        total_amount = Decimal(0)
        order = Order.objects.create(user=user, total_amount=0)

        for item in cart_items:
            product = item.product

            if product.stock < item.quantity:
                transaction.set_rollback(True)
                return Response({
                    "detail": f"Not enough stock for {product.name}"
                }, status=status.HTTP_400_BAD_REQUEST)

            # Decrease stock
            product.stock -= item.quantity
            product.save()

            # Create OrderItem
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=item.quantity,
                price=item.price
            )

            total_amount += item.total_price

        order.total_amount = total_amount
        order.save()

        # Clear cart
        cart_items.delete()

        return Response({"message": "✅ Order has been placed!"}, status=status.HTTP_201_CREATED)


from rest_framework import generics


class MyOrdersAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # orders = Order.objects.filter(user=request.user).order_by('-created_at')

        orders = Order.objects.filter(user=request.user)\
            .prefetch_related(
                'items',                      # Order -> OrderItem (reverse FK)
                'items__product'              # OrderItem -> Product
            )\
            .select_related()\
            .order_by('-created_at')
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)
