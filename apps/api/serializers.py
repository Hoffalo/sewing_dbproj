"""DRF serializers — JSON shape for the React SPA."""

from __future__ import annotations

from decimal import Decimal

from rest_framework import serializers

from apps.customers.models import Customer
from apps.orders.models import (
    Material,
    Measurement,
    Order,
    OrderItem,
    OrderItemMaterial,
)
from apps.production.models import Employee, ProductionStage, Ticket


class CustomerSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    order_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Customer
        fields = [
            "id",
            "first_name",
            "last_name",
            "full_name",
            "phone",
            "email",
            "address",
            "notes",
            "created_at",
            "updated_at",
            "order_count",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def get_full_name(self, obj: Customer) -> str:
        return f"{obj.first_name} {obj.last_name}".strip()


class MeasurementSerializer(serializers.ModelSerializer):
    label = serializers.CharField(source="get_name_display", read_only=True)

    class Meta:
        model = Measurement
        fields = ["id", "name", "label", "value_cm", "notes"]


class MaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Material
        fields = ["id", "name", "unit", "stock_quantity", "cost_per_unit", "currency"]


class OrderItemMaterialSerializer(serializers.ModelSerializer):
    material = MaterialSerializer(read_only=True)

    class Meta:
        model = OrderItemMaterial
        fields = ["id", "material", "quantity_used"]


class OrderItemSerializer(serializers.ModelSerializer):
    measurements = MeasurementSerializer(many=True, read_only=True)
    material_links = OrderItemMaterialSerializer(many=True, read_only=True)
    garment_label = serializers.CharField(source="get_garment_type_display", read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "garment_type",
            "garment_label",
            "description",
            "fabric",
            "color",
            "quantity",
            "unit_price",
            "design_notes",
            "position",
            "measurements",
            "material_links",
        ]


class OrderItemWriteSerializer(serializers.Serializer):
    """Slim shape used when creating an order with nested items."""

    garment_type = serializers.ChoiceField(choices=OrderItem.GarmentType.choices)
    description = serializers.CharField()
    fabric = serializers.CharField(required=False, allow_blank=True, default="")
    color = serializers.CharField(required=False, allow_blank=True, default="")
    quantity = serializers.IntegerField(min_value=1, default=1)
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    design_notes = serializers.CharField(required=False, allow_blank=True, default="")


class CustomerSlimSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = ["id", "full_name", "phone"]

    def get_full_name(self, obj: Customer) -> str:
        return f"{obj.first_name} {obj.last_name}".strip()


class OrderSerializer(serializers.ModelSerializer):
    customer = CustomerSlimSerializer(read_only=True)
    customer_id = serializers.PrimaryKeyRelatedField(
        queryset=Customer.objects.all(), source="customer", write_only=True
    )
    items = OrderItemSerializer(many=True, read_only=True)
    items_input = OrderItemWriteSerializer(many=True, write_only=True, required=False)
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "customer",
            "customer_id",
            "order_date",
            "due_date",
            "status",
            "status_label",
            "currency",
            "total_price",
            "notes",
            "items",
            "items_input",
            "item_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["status", "total_price", "created_at", "updated_at"]

    def get_item_count(self, obj: Order) -> int:
        return obj.items.count()

    def create(self, validated_data):
        items = validated_data.pop("items_input", [])
        order = Order.objects.create(**validated_data)
        for idx, item in enumerate(items, start=1):
            OrderItem.objects.create(
                order=order,
                position=idx,
                garment_type=item["garment_type"],
                description=item["description"],
                fabric=item.get("fabric", ""),
                color=item.get("color", ""),
                quantity=item["quantity"],
                unit_price=item["unit_price"],
                design_notes=item.get("design_notes", ""),
            )
        order.refresh_from_db()
        return order


class OrderListSerializer(serializers.ModelSerializer):
    """Slim payload for board cards & dashboard lists."""

    customer_name = serializers.SerializerMethodField()
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    item_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "customer_name",
            "order_date",
            "due_date",
            "status",
            "status_label",
            "currency",
            "total_price",
            "item_count",
            "notes",
        ]

    def get_customer_name(self, obj: Order) -> str:
        return f"{obj.customer.first_name} {obj.customer.last_name}".strip()


class ProductionStageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductionStage
        fields = ["id", "name", "sequence", "is_terminal"]


class TicketSerializer(serializers.ModelSerializer):
    current_stage = ProductionStageSerializer(read_only=True)
    assigned_to_name = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = [
            "id",
            "code",
            "current_stage",
            "assigned_to",
            "assigned_to_name",
            "priority",
            "deadline",
            "created_at",
        ]

    def get_assigned_to_name(self, obj: Ticket) -> str | None:
        if not obj.assigned_to:
            return None
        u = obj.assigned_to.user
        return u.get_full_name() or u.get_username()


class UserSerializer(serializers.Serializer):
    """Shape returned by /api/auth/me/ and /api/auth/login/."""

    id = serializers.IntegerField()
    username = serializers.CharField()
    full_name = serializers.CharField()
    role = serializers.CharField(allow_null=True)
    is_owner_or_manager = serializers.BooleanField()


def serialize_user(user) -> dict:
    from sewing_shop.roles import is_owner_or_manager

    role = None
    if hasattr(user, "employee_profile"):
        role = user.employee_profile.role
    elif user.is_superuser:
        role = Employee.Role.OWNER
    return {
        "id": user.id,
        "username": user.get_username(),
        "full_name": user.get_full_name() or user.get_username(),
        "role": role,
        "is_owner_or_manager": is_owner_or_manager(user),
    }


# Decimal helper — DRF returns DecimalFields as strings; the SPA expects numbers
# in a few computed places (totals, weekly_revenue). Keep this conversion local.
def to_float(d: Decimal | None) -> float:
    return float(d) if d is not None else 0.0
