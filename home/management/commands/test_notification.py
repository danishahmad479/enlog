from django.core.management.base import BaseCommand
from home.models import Order
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

class Command(BaseCommand):
    help = 'Test the notification system by changing order status'

    def add_arguments(self, parser):
        parser.add_argument('order_id', type=int, help='Order ID to update')
        parser.add_argument('status', type=str, choices=['pending', 'shipped', 'delivered'], help='New status')

    def handle(self, *args, **options):
        order_id = options['order_id']
        new_status = options['status']
        
        try:
            order = Order.objects.get(id=order_id)
            old_status = order.status
            order.status = new_status
            order.save()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully updated order {order_id} from {old_status} to {new_status}'
                )
            )
            
            # Test direct notification
            channel_layer = get_channel_layer()
            if channel_layer:
                async_to_sync(channel_layer.group_send)(
                    f"user_{order.user.id}",
                    {
                        "type": "send_notification",
                        "message": f"Test notification: Order #{order.id} status changed from {old_status.capitalize()} to {new_status.capitalize()}."
                    }
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Notification sent to user {order.user.id}'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        'Channel layer not available'
                    )
                )
                
        except Order.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    f'Order with ID {order_id} does not exist'
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f'Error updating order: {e}'
                )
            ) 