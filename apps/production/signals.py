from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.orders.models import Order
from apps.production.models import Delivery, StatusHistory, Ticket


@receiver(post_save, sender=StatusHistory)
def status_history_created(sender, instance, created, **kwargs):
    if not created:
        return
    Ticket.objects.filter(pk=instance.ticket_id).update(current_stage_id=instance.stage_id)
    order_id = (
        Ticket.objects.filter(pk=instance.ticket_id)
        .values_list("order_item__order_id", flat=True)
        .first()
    )
    if order_id is None:
        return
    tickets = Ticket.objects.filter(order_item__order_id=order_id).select_related("current_stage")
    if tickets.exists() and all(t.current_stage.is_terminal for t in tickets):
        Order.objects.filter(pk=order_id).exclude(status=Order.Status.DELIVERED).update(
            status=Order.Status.READY
        )


@receiver(post_save, sender=Delivery)
def delivery_created(sender, instance, created, **kwargs):
    if created:
        Order.objects.filter(pk=instance.order_id).update(status=Order.Status.DELIVERED)
