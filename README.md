# Costuras Lucía — Sewing Shop Management System

University databases course project: a **normalized PostgreSQL schema** behind a **Django 5 REST API** with a separate **React single-page app** as the only UI. The story follows **Costuras Lucía**, a tailoring atelier whose owner splits her time between **Madrid** (EUR pricing day-to-day) and Colombian clients who occasionally settle in **COP**, plus rare **USD** walk-ins — all **without fictitious FX conversion** (see §5.4).

---

## 1. Problem description

**Costuras Lucía** is a family-run sewing and alterations workshop. The owner is not technical, so the UI is a deliberately simple three-page React app:

- **Home** — operational dashboard (status counts, weekly revenue per currency, upcoming orders).
- **CRM** — drag-and-drop Kanban board across order stages, plus order creation.
- **Clients** — searchable directory with new-client intake.

Behind the SPA, Django serves a JSON API. Staff register walk-in customers, capture garment lines with metric measurements, open **work tickets**, advance **production stages** with an audit trail, and close orders through a **delivery** handshake.

**Intended users**

- **Owner / Manager** — full office operations, pricing oversight, closing deliveries, can move orders backward in the pipeline.
- **Tailor** — executes assigned tickets, advances the line forward only.
- **Front-desk staff** — intake customers/orders, no production edits.

---

## 2. Requirements & feature mapping

- **Client registry** → `Customer` model + `/clients` page (create, search, delete).
- **Orders & garments** → `Order`, `OrderItem`, `Measurement`, `Material`, `OrderItemMaterial`.
- **Inventory reference** → `Material` (catalog with stock and currency).
- **Production** → `ProductionStage` (reference table, seed data), `Ticket`, append-only `StatusHistory`, `Delivery`.
- **CRM pipeline UI** → drag-drop board on `/crm` writes `Order.status` via `POST /api/orders/<id>/move/`, validated server-side by [apps/orders/status_flow.py](apps/orders/status_flow.py).
- **RBAC** → Django **groups** `Owner`, `Manager`, `Tailor`, `Staff` (data migration); status-flow validators read group membership to allow/refuse transitions.
- **Multi-currency orders** → `Order.currency` + `Material.currency` (EUR / COP / USD); line items inherit the order currency; `OrderItemMaterial.clean()` blocks catalog/order mismatches.
- **PDF tickets** → `GET /api/tickets/<id>/pdf/` (ReportLab, locale-aware money) — same renderer the old admin had, just exposed via DRF.
- **Dashboard** → `GET /api/dashboard/` returns status counts, 8-week per-currency revenue, this-week revenue, upcoming orders and overdue counts. The Home page consumes it.
- **ERD** → `make erd` uses `django-extensions graph_models` (+ Graphviz in Docker).

---

## 3. Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│  Browser                                                           │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  React SPA (Vite, port 5173)                                 │  │
│  │  - Sidebar  · Home · CRM · Clients                           │  │
│  │  - TanStack Query, dnd-kit, Recharts, Tailwind               │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                            │  fetch('/api/...', { credentials })   │
│                            ▼                                       │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Django (port 8000)                                          │  │
│  │   /api/               DRF router (customers, orders, …)      │  │
│  │   /api/auth/          login / logout / me / csrf             │  │
│  │   /api/dashboard/     aggregate KPIs                         │  │
│  │   /api/tickets/<>/pdf ReportLab PDF                          │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                            │                                       │
│                            ▼                                       │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  PostgreSQL 16                                               │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
```

The Django admin (and the `django-unfold` theme) was removed entirely; `apps/api/` is the only public surface. Models, signals, and the role-aware status-flow rules in [apps/orders/status_flow.py](apps/orders/status_flow.py) are reused unchanged.

---

## 4. Technology stack

| Layer / concern        | Choice                                              |
|------------------------|-----------------------------------------------------|
| Database               | PostgreSQL 16                                       |
| Backend runtime        | Python 3.12, Django 5.2.x                           |
| API                    | Django REST Framework 3.15                          |
| CORS / cookies         | django-cors-headers                                 |
| Auth                   | Django session auth + CSRF (no JWT)                 |
| PDF                    | ReportLab                                           |
| Money formatting       | Babel (`format_currency`, locale-aware)             |
| Diagrams               | django-extensions + pydot + Graphviz (system)       |
| Frontend build         | Vite 5 + TypeScript 5                               |
| UI                     | React 18 + Tailwind CSS 3                           |
| Data fetching          | TanStack Query v5                                   |
| Drag & drop            | @dnd-kit/core + @dnd-kit/sortable                   |
| Charts                 | Recharts                                            |
| Icons                  | lucide-react                                        |
| Forms                  | react-hook-form                                     |
| Toasts                 | react-hot-toast                                     |

---

## 5. Setup

### Prerequisites
- Docker + Docker Compose (recommended), **or** Python 3.12 + Node 20 locally
- A copy of `.env.example` saved as `.env`

### One-shot run (Docker)

```bash
cp .env.example .env       # first time only
make up                    # builds db + web + frontend; runs all three
```

In another terminal, on the first run:

```bash
make migrate
make seed                  # creates demo users + demo orders
```

Then open **http://localhost:5173** and sign in with `admin` / `admin`.

### Local dev (without Docker)

Two terminals:

```bash
# 1. Backend
python -m venv .venv && source .venv/bin/activate    # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
docker compose up -d db                              # just Postgres
python manage.py migrate
python manage.py seed_demo
python manage.py runserver                           # :8000
```

```bash
# 2. Frontend
cd frontend
npm install
npm run dev                                          # :5173
```

The Vite dev server proxies `/api/*` to `localhost:8000`, so the SPA always talks through `/api`. The default seeded login is `admin` / `admin`.

### Notes on local vs Docker

- **PostgreSQL driver:** uses `psycopg` v3 (`psycopg[binary]`) so newer Python versions install without compiling client libs.
- **Hostname:** keep `POSTGRES_HOST=localhost` in `.env` for laptop runs. `docker-compose.yml` injects `POSTGRES_HOST=db` for the `web` container only — `db` only resolves inside the compose network.
- Start the database before migrating: `docker compose up -d db` (or `make up`).

---

## 6. Demo accounts (after `make seed`)

| Username | Password   | Role       |
|----------|------------|------------|
| `admin`  | `admin`    | Superuser  |
| `lucia`  | `demo1234` | Owner      |
| `carlos` | `demo1234` | Manager    |
| `ana`    | `demo1234` | Tailor     |
| `pedro`  | `demo1234` | Staff      |
| `sofia`  | `demo1234` | Staff      |

---

## 7. API surface

All endpoints are under `/api/` and require an authenticated session except `auth/csrf/` and `auth/login/`. Unsafe methods need an `X-CSRFToken` header (the SPA reads it from the `csrftoken` cookie).

| Method | Path                              | Purpose                                              |
|-------:|-----------------------------------|------------------------------------------------------|
| GET    | `/api/auth/csrf/`                 | Set the `csrftoken` cookie (called once on app boot) |
| POST   | `/api/auth/login/`                | `{username, password}` → session + user              |
| POST   | `/api/auth/logout/`               | End the session                                      |
| GET    | `/api/auth/me/`                   | Current user (`401` if signed out)                   |
| GET    | `/api/customers/?search=…`        | List + search by name/phone/email                    |
| POST   | `/api/customers/`                 | Create                                               |
| PATCH  | `/api/customers/<id>/`            | Update                                               |
| DELETE | `/api/customers/<id>/`            | Delete (`400` if they still have orders — `PROTECT`) |
| GET    | `/api/orders/?status=…`           | List with optional status filter                     |
| POST   | `/api/orders/`                    | Create with nested `items_input`                     |
| GET    | `/api/orders/<id>/`               | Full detail (items + measurements + materials)       |
| POST   | `/api/orders/<id>/move/`          | `{status}` — validated by `status_flow.py`           |
| DELETE | `/api/orders/<id>/`               | Delete (cascades line items, tickets, delivery)      |
| GET    | `/api/dashboard/`                 | Aggregates for Home page                             |
| GET    | `/api/tickets/<id>/pdf/`          | ReportLab work-order PDF                             |
| GET    | `/api/production-stages/`         | Reference table                                      |
| GET    | `/api/materials/`                 | Catalog                                              |

---

## 8. Database design

### 8.1 Entities

#### `Customer` (`apps.customers`)

| Attribute   | Notes                                              |
|-------------|----------------------------------------------------|
| PK `id`     | surrogate                                          |
| `phone`     | unique business key for walk-ins                   |
| `email`     | optional                                           |
| timestamps  | `created_at`, `updated_at`                         |

One customer has many orders (`Order.customer` FK with `on_delete=PROTECT`).

#### `Employee` (`apps.production`)

| Attribute | Notes                                          |
|-----------|------------------------------------------------|
| `user`    | `OneToOne` → `auth.User`                       |
| `role`    | `OWNER` / `MANAGER` / `TAILOR` / `STAFF`        |

#### `Order` (`apps.orders`)

| Attribute               | Notes                                                |
|-------------------------|------------------------------------------------------|
| `customer`              | FK `PROTECT`                                         |
| `order_date`/`due_date` | `CheckConstraint`: `due_date ≥ order_date`           |
| `status`                | `PENDING` → `IN_PRODUCTION` → `READY` → `DELIVERED` (or `CANCELLED`) |
| `currency`              | `EUR` / `COP` / `USD` — **no FX**, locked per order  |
| `total_price`           | denormalized aggregate (see §8.3), in `currency`     |

#### `OrderItem` (garment line)

| Attribute    | Notes                                            |
|--------------|--------------------------------------------------|
| `order`      | FK `CASCADE`                                     |
| `position`   | unique per order (`UniqueConstraint`)            |
| `unit_price` | `Decimal` in parent **order.currency**           |

`Measurement` stores `(order_item, name)` uniquely — **no repeating-group arrays of measurements**.

#### `Material` & `OrderItemMaterial`

`Material` is catalog/inventory; each row carries a `currency` for `cost_per_unit` and stock. When a garment line consumes materials (`OrderItemMaterial`), `clean()` requires matching material/order currency — the defensive seam where stray FX assumptions could otherwise hide.

#### `ProductionStage`

Reference table (`name`, `sequence`, `is_terminal`) seeded via migration. The owner can extend this table later without changing Python enums.

#### `Ticket`

| Attribute        | Notes                                       |
|------------------|---------------------------------------------|
| `order_item`     | FK `CASCADE`                                |
| `code`           | generated `TCK-YYYY-####`                   |
| `current_stage`  | denormalized pointer (see §8.3)             |
| `assigned_to`    | `SET_NULL`                                  |

#### `StatusHistory` (append-only)

`save()` rejects updates. `clean()` enforces **monotone stage sequences** unless `allow_backward` is checked for a supervised correction.

#### `Delivery`

`OneToOne` with `Order`. Creating a delivery sets order status to `DELIVERED` via signal.

### 8.2 Normalization (3NF argument)

1. **Atomic columns / no repeating groups** — measurements are rows, not CSV columns; order-line materials use `OrderItemMaterial`.
2. **Every non-key attribute depends on the whole key** — surrogate PKs (`BigAutoField`) on all transaction tables; composite uniqueness via `UniqueConstraint`, not artificial multi-column PKs.
3. **No transitive dependencies** — customer name/phone live only in `Customer`; orders store `customer_id`, not copies of name strings.

### 8.3 Deliberate denormalizations

| Column                  | Why keep it?                                | How kept consistent?                |
|-------------------------|---------------------------------------------|--------------------------------------|
| `Order.total_price`     | Fast list filtering/sorting, dashboard sums | Signals on `OrderItem` save/delete  |
| `Ticket.current_stage`  | Fast ticket queues / dashboards            | Signal on new `StatusHistory` rows  |

Both are **read-optimized projections**; the **normalized facts** remain line items and status history rows.

### 8.4 Currency model — denormalized but constrained

Each `Order` carries a single `currency` code; line items inherit it. We deliberately **do not** store an FX rate or convert between currencies — the shop's actual workflow is currency-locked per transaction, and storing fake FX would create false precision. `OrderItemMaterial.clean()` blocks currency-mixing across catalog and order, which is the only place a mismatch could silently occur. The `/api/dashboard/` endpoint reports revenue **per currency** — never as a cross-currency total.

> The same design paragraph is captured for course hand-ins in `docs/Costuras_Lucia_Architecture.docx` (section **3.4.3**).

---

## 9. ERD

Embedded diagram (`docs/erd_main.png`). Regenerate locally (requires Graphviz + DB migrated):

```bash
make erd
```

The committed PNG may be a placeholder if Graphviz was unavailable during export — replace via `make erd` in Docker (image installs `graphviz`).

---

## 10. Workflows

### W1 — Customer intake

1. **Clients page → "New client" panel** — capture name + phone (only required fields).
2. Submit → optimistic insert into the directory.
3. The new client is immediately searchable from the New Order drawer.

### W2 — Order creation

1. **CRM page → "New order"** opens a slide-in drawer.
2. Search and pick a customer; the panel collapses into a clear "selected client" chip.
3. Fill in due date, currency, and one or more garment lines (type, qty, unit price, fabric, color, design notes).
4. Save — order lands in the **Pending** column. The CRM board refreshes; the dashboard updates.

### W3 — Production tracking via CRM board

1. Drag an order across columns to update its status. The drop is sent to `POST /api/orders/<id>/move/` and validated by [apps/orders/status_flow.py](apps/orders/status_flow.py):
   - Only Owner/Manager may move an order **backward** in the pipeline.
   - `DELIVERED` is reachable only via a `Delivery` row, not direct drag (the API refuses the move with a friendly 400, surfaced as a toast).
   - Cancelled orders need Owner/Manager.
2. Drag within a column to **reorder cards**. Per-column ordering is persisted in the browser's `localStorage` (`crm-column-order-v1`) so it survives reloads.
3. New orders coming in from the server appear at the top of their column.

### W4 — Deletion

- **Order** — hover any card on the CRM board; trash icon appears. Confirm dialog → `DELETE /api/orders/<id>/`. Cascades line items, measurements, tickets, delivery.
- **Client** — hover any client card; trash icon appears. Confirm dialog → `DELETE /api/customers/<id>/`. The server returns 400 if the client still has orders (PROTECT FK); the toast surfaces the message.

### W5 — Ticket PDF

Open `/api/tickets/<id>/pdf/` directly (e.g. linked from order detail) — ReportLab streams a download.

---

## 11. Business rules implemented

- **`due_date ≥ order_date`** — `CheckConstraint` on `Order`.
- **Currency lock** — each `Order`/`Material` carries a currency code; `OrderItemMaterial.clean()` rejects lines that would join a COP order to a EUR-priced bolt; **no cross-currency aggregates** in the dashboard.
- **Monotone workflow** — `StatusHistory.clean` + `allow_backward` escape hatch.
- **Append-only audit** — `StatusHistory.save` rejects updates.
- **Order totals** — recalculated whenever a line item changes (signal).
- **Terminal synchronization** — signals promote order to `READY` / `DELIVERED` according to tickets + deliveries.
- **CRM transitions** — role checks centralized in `apps.orders.status_flow.validate_crm_transition`.

---

## 12. Roles & permissions

| Capability                              | Owner | Manager | Tailor | Staff |
|-----------------------------------------|:-----:|:-------:|:------:|:-----:|
| List / create / update customers        | ✅    | ✅      | view   | ✅    |
| Delete customer (no orders)             | ✅    | ✅      | ❌     | ❌    |
| Create order                            | ✅    | ✅      | ❌     | ✅    |
| Move order forward in pipeline          | ✅    | ✅      | ✅     | ✅    |
| Move order **backward**                 | ✅    | ✅      | ❌     | ❌    |
| Cancel order                            | ✅    | ✅      | ❌     | ❌    |
| Delete order                            | ✅    | ✅      | ❌     | ❌    |
| Mark delivered (Delivery row)           | ✅    | ✅      | ❌     | ❌    |

---

## 13. Frontend layout

```
frontend/
├── package.json
├── vite.config.ts        # /api → http://localhost:8000 proxy
├── tailwind.config.ts    # white + lavender palette, glow shadow tokens
└── src/
    ├── main.tsx          # router, query client, toaster
    ├── App.tsx           # AuthGate + routes
    ├── lib/
    │   ├── api.ts        # fetch wrapper, X-CSRFToken, ApiError
    │   ├── csrf.ts       # cookie reader
    │   ├── queries.ts    # TanStack Query hooks
    │   └── types.ts      # shared TS types & status helpers
    ├── components/
    │   ├── Sidebar.tsx
    │   ├── Layout.tsx
    │   ├── StatCard.tsx
    │   ├── OrderCard.tsx
    │   ├── KanbanColumn.tsx     # SortableContext + droppable column
    │   ├── NewOrderDrawer.tsx
    │   └── ConfirmDialog.tsx
    └── pages/
        ├── Home.tsx       # stat cards, charts, upcoming
        ├── CRM.tsx        # Kanban board + drop animation
        ├── Clients.tsx    # directory + new-client form
        └── Login.tsx
```

---

## 14. Maintenance commands

| Make target       | Meaning                                       |
|-------------------|-----------------------------------------------|
| `make up`         | Build & run Docker Compose (db + web + frontend) |
| `make down`       | Stop containers                                |
| `make migrate`    | `manage.py migrate`                            |
| `make seed`       | `manage.py seed_demo`                          |
| `make erd`        | Export `docs/erd.png` + `docs/erd_main.png`     |
| `make front`      | `cd frontend && npm run dev` (host)            |
| `make front-install` | `cd frontend && npm install`                |
| `make black`      | Format Python                                  |
| `make ruff`       | Lint Python                                    |

---

## 15. Developer hygiene

- **Pinned** dependencies in `requirements.txt` and `frontend/package.json`.
- **`pyproject.toml`** configures Black + Ruff (formatting + lint).
- TypeScript runs in strict mode; `npm run build` performs a full typecheck before bundling.
- Graphviz available in the Docker image for ERD generation.

---

### Academic integrity note

This README ties features to the **course learning goals** (normalization, constraints, audit, RBAC). When presenting, narrate why **`OrderItemMaterial`** breaks a repeating group, why **`ProductionStage`** is a table rather than `TextChoices`, and how the CRM drag-drop UI is just a thin client over a strictly-validated `apps.orders.status_flow` — the rules live with the data, not the UI.
