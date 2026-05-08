from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CustomerViewSet,
    DashboardView,
    MaterialViewSet,
    OrderViewSet,
    ProductionStageViewSet,
    TicketPDFView,
    TicketViewSet,
)

router = DefaultRouter()
router.register(r"customers", CustomerViewSet, basename="customer")
router.register(r"orders", OrderViewSet, basename="order")
router.register(r"materials", MaterialViewSet, basename="material")
router.register(r"production-stages", ProductionStageViewSet, basename="stage")
router.register(r"tickets", TicketViewSet, basename="ticket")

urlpatterns = [
    path("", include(router.urls)),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("tickets/<int:ticket_id>/pdf/", TicketPDFView.as_view(), name="ticket-pdf"),
]
