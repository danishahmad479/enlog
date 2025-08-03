# home/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)

    def __str__(self):
        return self.username



class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField()
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)

    def __str__(self):
        return self.name



class CartItem(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()
    total_price = models.DecimalField(max_digits=12, decimal_places=2,null=True, blank=True)


    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    products = models.ManyToManyField(Product, through='OrderItem')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order {self.id} by {self.user.username}"

    def save(self, *args, **kwargs):
        is_status_changed = False
        previous_status = None

        if self.pk:
            try:
                previous = Order.objects.get(pk=self.pk)
                previous_status = previous.status
                allowed_transitions = {
                    'pending': ['shipped', 'delivered'],
                    'shipped': ['delivered'],
                    'delivered': [],
                }

                if self.status != previous_status:
                    is_status_changed = True
                    if self.status not in allowed_transitions[previous_status]:
                        raise ValueError(f"Invalid status transition from {previous_status} to {self.status}")
            except Order.DoesNotExist:
                pass

        super().save(*args, **kwargs)

        # Send notification if status changed
        if is_status_changed and previous_status:
            try:
                channel_layer = get_channel_layer()
                if channel_layer:
                    async_to_sync(channel_layer.group_send)(
                        f"user_{self.user.id}",
                        {
                            "type": "send_notification",
                            "message": f"Your order #{self.id} status changed from {previous_status.capitalize()} to {self.status.capitalize()}."
                        }
                    )
                    print(f"Notification sent to user {self.user.id} for order {self.id}")
            except Exception as e:
                print(f"Failed to send notification: {e}")

    class Meta:
        ordering = ['-created_at']

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE,related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} x {self.quantity} in Order {self.order.id}"

