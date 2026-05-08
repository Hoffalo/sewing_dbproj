from decimal import Decimal

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.orders.models import Order, OrderItem


def recalc_order_total(order: Order) -> None:
    total = Decimal("0.00")
    for item in order.items.all():
        total += Decimal(item.quantity) * Decimal(item.unit_price)
    Order.objects.filter(pk=order.pk).update(total_price=total)


@receiver(post_save, sender=OrderItem)
def order_item_saved(sender, instance, **kwargs):
    recalc_order_total(instance.order)


@receiver(post_delete, sender=OrderItem)
def order_item_deleted(sender, instance, **kwargs):
    recalc_order_total(instance.order)
