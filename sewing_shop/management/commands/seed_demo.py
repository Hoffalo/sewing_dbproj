"""
Load a rich demo dataset for Costuras Lucía (course demo / manual QA).

The project also ships JSON fixtures under ``apps/*/fixtures/demo.json`` with the
same reference rows (customers, materials) for ``loaddata``-based workflows.
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.customers.models import Customer
from apps.orders.models import (
    Material,
    Measurement,
    Order,
    OrderItem,
    OrderItemMaterial,
)
from apps.production.models import Delivery, Employee, ProductionStage, StatusHistory, Ticket
from sewing_shop.roles import GROUP_MANAGER, GROUP_OWNER, GROUP_STAFF, GROUP_TAILOR


class Command(BaseCommand):
    help = "Seed the database with demo users, garments, tickets, and history."

    @transaction.atomic
    def handle(self, *args, **options):
        User = get_user_model()
        if not User.objects.filter(is_superuser=True).exists():
            User.objects.create_superuser("admin", email="admin@example.com", password="admin")
            self.stdout.write(self.style.SUCCESS("Created superuser admin / admin"))

        if Customer.objects.exists():
            self.stdout.write(self.style.WARNING("Demo data already exists — skipping dataset import."))
            return

        def make_user(username: str, first: str, last: str, group_name: str) -> tuple:
            user, _ = User.objects.get_or_create(
                username=username,
                defaults={"first_name": first, "last_name": last, "is_staff": True},
            )
            if not user.has_usable_password():
                user.set_password("demo1234")
            user.first_name = first
            user.last_name = last
            user.is_staff = True
            user.save()
            grp = Group.objects.filter(name=group_name).first()
            if grp:
                user.groups.add(grp)
            employee, _created = Employee.objects.update_or_create(
                user=user,
                defaults={
                    "role": {
                        GROUP_OWNER: Employee.Role.OWNER,
                        GROUP_MANAGER: Employee.Role.MANAGER,
                        GROUP_TAILOR: Employee.Role.TAILOR,
                        GROUP_STAFF: Employee.Role.STAFF,
                    }[group_name],
                    "hired_on": date(2020, 1, 1),
                    "active": True,
                },
            )
            return user, employee

        owner_user, owner_emp = make_user("lucia", "Lucía", "Restrepo", GROUP_OWNER)
        mgr_user, mgr_emp = make_user("carlos", "Carlos", "Mendoza", GROUP_MANAGER)
        tailor_user, tailor_emp = make_user("ana", "Ana", "Torres", GROUP_TAILOR)
        staff1_user, staff1_emp = make_user("pedro", "Pedro", "Salas", GROUP_STAFF)
        staff2_user, staff2_emp = make_user("sofia", "Sofía", "Gómez", GROUP_STAFF)

        customers = [
            Customer.objects.create(
                first_name=n[0],
                last_name=n[1],
                phone=p,
                email=e,
                address="Bogotá, Colombia",
            )
            for n, p, e in [
                (("María", "Rodríguez"), "+57-300-111-2233", "maria.r@example.com"),
                (("José", "Martínez"), "+57-310-222-3344", "jose.m@example.com"),
                (("Carmen", "López"), "+57-320-333-4455", "carmen.l@example.com"),
                (("Andrés", "García"), "+57-300-444-5566", "andres.g@example.com"),
                (("Laura", "Hernández"), "+57-301-555-6677", "laura.h@example.com"),
                (("Diego", "Vargas"), "+57-302-666-7788", "diego.v@example.com"),
                (("Valentina", "Morales"), "+57-303-777-8899", "valentina.m@example.com"),
                (("Camila", "Navarro"), "+57-304-888-9900", "camila.n@example.com"),
            ]
        ]

        materials = [
            Material.objects.create(
                name=name,
                unit=unit,
                stock_quantity=Decimal("120.00"),
                cost_per_unit=Decimal(price),
            )
            for name, unit, price in [
                ("Seda italiana azul", Material.Unit.METER, "18.50"),
                ("Lino gris", Material.Unit.METER, "12.00"),
                ("Hilo poliéster blanco", Material.Unit.SPOOL, "2.40"),
                ("Cierre invisible 20cm", Material.Unit.UNIT, "0.90"),
                ("Tela drill negra", Material.Unit.METER, "9.40"),
                ("Entretela fusible", Material.Unit.METER, "4.10"),
            ]
        ]

        today = timezone.localdate()

        def mk_order(idx: int, customer: Customer, status: str, od: date, due: date, note: str) -> Order:
            o = Order.objects.create(
                customer=customer,
                order_date=od,
                due_date=due,
                status=status,
                notes=note,
            )
            return o

        orders: list[Order] = []
        orders.append(
            mk_order(
                1,
                customers[0],
                Order.Status.PENDING,
                today - timedelta(days=2),
                today + timedelta(days=7),
                "Vestido de fiesta",
            )
        )
        orders.append(
            mk_order(
                2,
                customers[1],
                Order.Status.IN_PRODUCTION,
                today - timedelta(days=10),
                today + timedelta(days=3),
                "Traje formal",
            )
        )
        orders.append(
            mk_order(
                3,
                customers[2],
                Order.Status.IN_PRODUCTION,
                today - timedelta(days=20),
                today - timedelta(days=1),
                "Conjunto clásico — atrasado",
            )
        )
        orders.append(
            mk_order(
                4,
                customers[3],
                Order.Status.READY,
                today - timedelta(days=25),
                today + timedelta(days=2),
                "Listo para retiro",
            )
        )
        orders.append(
            mk_order(
                5,
                customers[4],
                Order.Status.DELIVERED,
                today - timedelta(days=45),
                today - timedelta(days=10),
                "Entregado reciente",
            )
        )
        orders.append(
            mk_order(
                6,
                customers[5],
                Order.Status.CANCELLED,
                today - timedelta(days=60),
                today - timedelta(days=30),
                "Cliente canceló",
            )
        )
        orders.append(
            mk_order(
                7,
                customers[6],
                Order.Status.PENDING,
                today - timedelta(days=1),
                today + timedelta(days=5),
                "Prueba rápida",
            )
        )
        orders.append(
            mk_order(
                8,
                customers[7],
                Order.Status.IN_PRODUCTION,
                today - timedelta(days=12),
                today + timedelta(days=8),
                "Falda lápiz",
            )
        )
        orders.append(
            mk_order(
                9,
                customers[0],
                Order.Status.IN_PRODUCTION,
                today - timedelta(days=15),
                today + timedelta(days=1),
                "Camisa a medida",
            )
        )
        orders.append(
            mk_order(
                10,
                customers[2],
                Order.Status.PENDING,
                today - timedelta(days=3),
                today + timedelta(days=10),
                "Ajustes livianos",
            )
        )
        orders.append(
            mk_order(
                11,
                customers[4],
                Order.Status.READY,
                today - timedelta(days=18),
                today,
                "Abrigo — terminado",
            )
        )
        orders.append(
            mk_order(
                12,
                customers[3],
                Order.Status.DELIVERED,
                today - timedelta(days=50),
                today - timedelta(days=5),
                "Entrega histórica",
            )
        )

        stages = {s.name: s for s in ProductionStage.objects.all()}
        assert stages, "Run migrations — production stages missing."

        def make_item(
            order: Order,
            pos: int,
            gtype: str,
            desc: str,
            price: str,
            measures: dict[str, str],
        ) -> OrderItem:
            item = OrderItem.objects.create(
                order=order,
                garment_type=gtype,
                description=desc,
                fabric="mixed",
                color="n/a",
                quantity=1,
                unit_price=Decimal(price),
                position=pos,
            )
            for name, val in measures.items():
                Measurement.objects.create(
                    order_item=item,
                    name=name,
                    value_cm=Decimal(val),
                )
            return item

        # ~25 line items distributed among orders
        items: list[OrderItem] = []
        items.append(
            make_item(
                orders[0],
                1,
                OrderItem.GarmentType.DRESS,
                "Vestido largo",
                "180.00",
                {
                    Measurement.Name.BUST: "92.00",
                    Measurement.Name.WAIST: "74.00",
                    Measurement.Name.HIPS: "98.00",
                    Measurement.Name.LENGTH: "118.00",
                },
            )
        )
        items.append(
            make_item(
                orders[1],
                1,
                OrderItem.GarmentType.SUIT,
                "Saco + pantalón",
                "420.00",
                {
                    Measurement.Name.BUST: "102.00",
                    Measurement.Name.SLEEVE: "63.00",
                    Measurement.Name.INSEAM: "78.00",
                },
            )
        )
        items.append(
            make_item(
                orders[2],
                1,
                OrderItem.GarmentType.SKIRT,
                "Falda tubo",
                "95.00",
                {Measurement.Name.WAIST: "70.00", Measurement.Name.HIPS: "96.00"},
            )
        )
        items.append(
            make_item(
                orders[3],
                1,
                OrderItem.GarmentType.PANTS,
                "Pantalón pinzas",
                "140.00",
                {Measurement.Name.WAIST: "82.00", Measurement.Name.INSEAM: "76.00"},
            )
        )
        items.append(
            make_item(
                orders[4],
                1,
                OrderItem.GarmentType.SHIRT,
                "Camisa vestir",
                "85.00",
                {Measurement.Name.NECK: "39.00", Measurement.Name.SLEEVE: "65.00"},
            )
        )
        items.append(
            make_item(
                orders[5],
                1,
                OrderItem.GarmentType.ALTERATION,
                "Ajuste básico",
                "25.00",
                {Measurement.Name.LENGTH: "3.00"},
            )
        )
        items.append(
            make_item(
                orders[6],
                1,
                OrderItem.GarmentType.DRESS,
                "Vestido cóctel",
                "210.00",
                {
                    Measurement.Name.BUST: "88.00",
                    Measurement.Name.WAIST: "70.00",
                    Measurement.Name.LENGTH: "102.00",
                },
            )
        )
        items.append(
            make_item(
                orders[7],
                1,
                OrderItem.GarmentType.SKIRT,
                "Falda midi",
                "75.00",
                {Measurement.Name.WAIST: "72.00", Measurement.Name.HIPS: "100.00"},
            )
        )
        items.append(
            make_item(
                orders[8],
                1,
                OrderItem.GarmentType.SHIRT,
                "Camisa lino",
                "95.00",
                {Measurement.Name.NECK: "40.00", Measurement.Name.SHOULDER: "46.00"},
            )
        )
        items.append(
            make_item(
                orders[9],
                1,
                OrderItem.GarmentType.ALTERATION,
                "Cortar basta",
                "18.00",
                {Measurement.Name.LENGTH: "2.00"},
            )
        )
        items.append(
            make_item(
                orders[10],
                1,
                OrderItem.GarmentType.OTHER,
                "Chaleco",
                "110.00",
                {Measurement.Name.BUST: "96.00"},
            )
        )
        items.append(
            make_item(
                orders[11],
                1,
                OrderItem.GarmentType.SUIT,
                "Traje 3 piezas",
                "510.00",
                {
                    Measurement.Name.BUST: "104.00",
                    Measurement.Name.SLEEVE: "64.00",
                    Measurement.Name.INSEAM: "80.00",
                },
            )
        )
        # extra lines on busy orders
        items.append(
            make_item(
                orders[1],
                2,
                OrderItem.GarmentType.SHIRT,
                "Camisa extra",
                "70.00",
                {Measurement.Name.NECK: "41.00"},
            )
        )
        items.append(
            make_item(
                orders[2],
                2,
                OrderItem.GarmentType.ALTERATION,
                "Cerrar cierre",
                "12.00",
                {Measurement.Name.LENGTH: "1.00"},
            )
        )
        items.append(
            make_item(
                orders[3],
                2,
                OrderItem.GarmentType.SKIRT,
                "Falda corta",
                "60.00",
                {Measurement.Name.WAIST: "74.00"},
            )
        )

        # Link a few materials
        for it in items[:6]:
            OrderItemMaterial.objects.create(
                order_item=it,
                material=materials[0],
                quantity_used=Decimal("1.5"),
            )

        def add_history(ticket: Ticket, actor: Employee, chain: list[str]):
            for name in chain:
                StatusHistory.objects.create(
                    ticket=ticket,
                    stage=stages[name],
                    changed_by=actor,
                    comment="demo",
                )

        # Tickets for production orders: pick items tied to in-production / ready / delivered samples
        ticket_targets: list[tuple[OrderItem, Employee, list[str], str]] = [
            (items[1], tailor_emp, ["RECEIVED", "DESIGN_CONFIRMED", "CUTTING"], Order.Status.IN_PRODUCTION),
            (items[2], tailor_emp, ["RECEIVED", "CUTTING", "SEWING"], Order.Status.IN_PRODUCTION),
            (items[3], tailor_emp, ["RECEIVED", "DESIGN_CONFIRMED", "CUTTING", "SEWING", "FINISHING", "QUALITY_CHECK", "READY"], Order.Status.READY),
            (items[4], owner_emp, ["RECEIVED", "DESIGN_CONFIRMED", "CUTTING", "SEWING", "FINISHING", "QUALITY_CHECK", "READY", "DELIVERED"], Order.Status.DELIVERED),
            (items[7], tailor_emp, ["RECEIVED", "CUTTING"], Order.Status.IN_PRODUCTION),
            (items[8], tailor_emp, ["RECEIVED", "SEWING"], Order.Status.IN_PRODUCTION),
            (items[11], mgr_emp, ["RECEIVED", "DELIVERED"], Order.Status.DELIVERED),
        ]

        for item, actor, chain, _ in ticket_targets:
            ticket = Ticket.objects.create(
                order_item=item,
                assigned_to=tailor_emp,
                current_stage=stages["RECEIVED"],
                priority=Ticket.Priority.NORMAL,
                deadline=item.order.due_date,
                code="",
            )
            add_history(ticket, actor, chain)

        # Deliveries (two delivered orders)
        for ord_obj in [orders[4], orders[11]]:
            if not hasattr(ord_obj, "delivery"):
                Delivery.objects.create(
                    order=ord_obj,
                    delivered_at=timezone.now() - timedelta(days=3),
                    received_by=ord_obj.customer.first_name,
                    delivered_by=mgr_emp,
                    final_observations="Todo en buen estado.",
                )

        # Recalculate order totals via ORM aggregates
        for order in Order.objects.all():
            total = sum(
                (it.quantity * it.unit_price for it in order.items.all()),
                Decimal("0.00"),
            )
            Order.objects.filter(pk=order.pk).update(total_price=total)

        self.stdout.write(self.style.SUCCESS("Demo data ready."))
