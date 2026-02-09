from django.db.models import Count, Q, Sum
from django.utils import timezone
from decimal import Decimal
from django.shortcuts import get_object_or_404, redirect
from tenants.models import Occupancy
from datetime import date
from .forms import TransferForm
from .forms import StudentForm
from rooms.models import Room
from billing.models import RentInvoice, RentPayment
from expenses.models import Expense
from .forms import RoomForm, RoomPriceForm
from rooms.models import RoomPrice
from django.db import transaction
from tenants.models import Student, Occupancy
from django.shortcuts import render
from django.contrib import messages
from decimal import Decimal, ROUND_HALF_UP
from django.db import transaction
from django.db.models import OuterRef, Subquery
from billing.models import RentPayment
from .forms import ExpenseForm
from expenses.models import Expense
from billing.models import RentInvoice
from .forms import OccupancyForm
from maintenance.models import MaintenanceRequest
from .forms import MaintenanceForm, MaintenanceUpdateForm
from maintenance.models import MaintenanceRequest, Area
from rooms.models import Room
from django.db.models.functions import TruncMonth
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from datetime import date
from decimal import Decimal
from billing.models import RentPayment
from expenses.models import Expense
from maintenance.models import MaintenanceRequest
from .forms import ExpenseForm, PaymentForm
from datetime import date
from calendar import monthrange
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from django.contrib import messages
from django.shortcuts import render, redirect

from tenants.models import Occupancy
from billing.models import RentInvoice
from .forms import InvoiceGenerationForm
from rooms.models import Room
from django.contrib.auth.decorators import login_required



# ------------------------
# Helpers
# ------------------------
def _month_start(d: date) -> date:
    return d.replace(day=1)

def _add_months(d: date, months: int) -> date:
    y = d.year + (d.month - 1 + months) // 12
    m = (d.month - 1 + months) % 12 + 1
    return d.replace(year=y, month=m, day=1)


# ------------------------
# Dashboard (KPI page)
# ------------------------
@login_required
def index(request):
    today = timezone.localdate()
    month_start = _month_start(today)
    next_month_start = _add_months(month_start, 1)

    # Occupancy
    rooms_qs = Room.objects.annotate(
        occupied=Count("occupancies", filter=Q(occupancies__active=True))
    )

    total_capacity = rooms_qs.aggregate(s=Sum("capacity"))["s"] or 0
    total_occupied = sum(r.occupied for r in rooms_qs)
    total_available = max(total_capacity - total_occupied, 0)

    # Rent collected (this month)
    rent_collected = RentPayment.objects.filter(
        payment_date__gte=month_start,
        payment_date__lt=next_month_start,
    ).aggregate(s=Sum("amount"))["s"] or Decimal("0.00")

    # Overdue rent (dynamic, always correct)
    overdue_invoices = RentInvoice.objects.filter(
        due_date__lt=today
    )
    overdue_rent = sum(
        (inv.amount_due - inv.amount_paid)
        for inv in overdue_invoices
        if inv.amount_due > inv.amount_paid
    ) or Decimal("0.00")

    # Expenses (this month)
    expenses_total = Expense.objects.filter(
        expense_date__gte=month_start,
        expense_date__lt=next_month_start,
    ).aggregate(s=Sum("amount"))["s"] or Decimal("0.00")

    profit = rent_collected - expenses_total

    # Charts: last 6 months
    labels, rent_series, exp_series = [], [], []

    for i in range(-5, 1):
        m_start = _add_months(month_start, i)
        m_end = _add_months(month_start, i + 1)

        labels.append(m_start.strftime("%b"))

        r_sum = RentPayment.objects.filter(
            payment_date__gte=m_start, payment_date__lt=m_end
        ).aggregate(s=Sum("amount"))["s"] or Decimal("0.00")
        rent_series.append(float(r_sum))

        e_sum = Expense.objects.filter(
            expense_date__gte=m_start, expense_date__lt=m_end
        ).aggregate(s=Sum("amount"))["s"] or Decimal("0.00")
        exp_series.append(float(e_sum))

    context = {
        "occupied_beds": total_occupied,
        "available_beds": total_available,
        "rent_collected": rent_collected,
        "overdue_rent": overdue_rent,
        "expenses": expenses_total,
        "profit": profit,

        # chart data
        "chart_labels": labels,
        "chart_rent": rent_series,
        "chart_expenses": exp_series,
        "chart_occ": [total_occupied, total_available],
    }
    return render(request, "dashboard/index.html", context)

from django.contrib import messages
from django.shortcuts import render, redirect
from django.db.models import OuterRef, Subquery
from tenants.models import Student, Occupancy
from .forms import StudentForm
@login_required
def students_list(request):
    if request.method == "POST":
        form = StudentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Student added successfully.")
            return redirect("dash_students")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = StudentForm()

    latest_occ = Occupancy.objects.filter(student=OuterRef("pk")).order_by("-entry_date")

    students = (
        Student.objects
        .annotate(
            room_name=Subquery(latest_occ.values("room__name")[:1]),
            entry_date=Subquery(latest_occ.values("entry_date")[:1]),
            active=Subquery(latest_occ.values("active")[:1]),
        )
        .order_by("full_name")
    )

    return render(request, "dashboard/students_list.html", {
        "students": students,
        "form": form,   # <-- THIS is what your template needs
    })

""" from django.shortcuts import render, redirect
from dashboard.forms import StudentForm


def add_student(request):
    if request.method == "POST":
        form = StudentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("students_list")
    else:
        form = StudentForm()

    return render(request, "students/add_student.html", {"form": form}) """

# ------------------------
# Placeholder pages (needed by urls.py)
# ------------------------

from django.db.models.functions import TruncMonth
@login_required
def maintenance_reports(request):
    # Optional month filter: YYYY-MM
    month = request.GET.get("month", "").strip()

    qs = MaintenanceRequest.objects.select_related("room", "area").all()

    if month:
        try:
            y, m = month.split("-")
            y = int(y); m = int(m)
            qs = qs.filter(reported_date__year=y, reported_date__month=m)
        except Exception:
            month = ""

    total_count = qs.count()
    open_count = qs.filter(status="OPEN").count()
    inprog_count = qs.filter(status="IN_PROGRESS").count()
    done_count = qs.filter(status="DONE").count()

    est_total = qs.aggregate(s=Sum("estimated_cost"))["s"] or 0
    act_total = qs.aggregate(s=Sum("actual_cost"))["s"] or 0

    # Breakdown by ROOM
    by_room = (
        qs.filter(room__isnull=False)
        .values("room__name")
        .annotate(
            count=Count("id"),
            actual=Sum("actual_cost"),
            estimated=Sum("estimated_cost"),
        )
        .order_by("-count")
    )

    # Breakdown by AREA
    by_area = (
        qs.filter(area__isnull=False)
        .values("area__name")
        .annotate(
            count=Count("id"),
            actual=Sum("actual_cost"),
            estimated=Sum("estimated_cost"),
        )
        .order_by("-count")
    )

    # Monthly trend (last 6 months, actual cost + count)
    trend_qs = (
        MaintenanceRequest.objects
        .annotate(m=TruncMonth("reported_date"))
        .values("m")
        .annotate(count=Count("id"), actual=Sum("actual_cost"))
        .order_by("m")
    )

    labels = []
    series_count = []
    series_actual = []
    for row in trend_qs:
        if row["m"]:
            labels.append(row["m"].strftime("%b %Y"))
            series_count.append(int(row["count"] or 0))
            series_actual.append(float(row["actual"] or 0))

    return render(request, "dashboard/maintenance_reports.html", {
        "month": month,

        "total_count": total_count,
        "open_count": open_count,
        "inprog_count": inprog_count,
        "done_count": done_count,
        "est_total": est_total,
        "act_total": act_total,

        "by_room": by_room,
        "by_area": by_area,

        "trend_labels": labels,
        "trend_count": series_count,
        "trend_actual": series_actual,
    })
@login_required
def students_list(request):
    # Show each student's latest occupancy (if any)
    latest_occ = Occupancy.objects.filter(student=OuterRef("pk")).order_by("-entry_date")

    students = (
        Student.objects
        .annotate(
            room_name=Subquery(latest_occ.values("room__name")[:1]),
            entry_date=Subquery(latest_occ.values("entry_date")[:1]),
            active=Subquery(latest_occ.values("active")[:1]),
        )
        .order_by("full_name")
    )
    return render(request, "dashboard/students_list.html", {"students": students})

@login_required
def invoices_list(request):
    invoices = (
        RentInvoice.objects
        .select_related("student", "occupancy__room")
        .order_by("-due_date")[:200]
    )
    return render(request, "dashboard/invoices_list.html", {"invoices": invoices})

def payments_list(request):
    if request.method == "POST":
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save()
            # Invoice totals/status auto-update via signals ✅
            messages.success(request, "Payment saved successfully.")
            return redirect("dash_payments")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = PaymentForm()

    payments = (
        RentPayment.objects
        .select_related("invoice__student", "invoice__occupancy__room")
        .order_by("-payment_date")[:200]
    )
    return render(request, "dashboard/payments_list.html", {"payments": payments, "form": form})
@login_required
def expenses_list(request):
    if request.method == "POST":
        form = ExpenseForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Expense saved successfully.")
            return redirect("dash_expenses")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ExpenseForm()

    expenses = Expense.objects.order_by("-expense_date", "-created_at")[:200]
    return render(request, "dashboard/expenses_list.html", {"expenses": expenses, "form": form})



def _money(x: Decimal) -> Decimal:
    return x.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

@transaction.atomic
@login_required
def rooms_list(request):
    today = timezone.localdate()

    # --- Handle room creation ---
    if request.method == "POST":
        room_form = RoomForm(request.POST)
        price_form = RoomPriceForm(request.POST)

        if room_form.is_valid():
            room = room_form.save()

            # If a price was provided, create the active price entry
            # (price_form is optional: only save if user entered a price)
            price = request.POST.get("price", "").strip()
            start_date = request.POST.get("start_date", "").strip()

            if price and start_date:
                pf = RoomPriceForm({"price": price, "start_date": start_date})
                if pf.is_valid():
                    rp = pf.save(commit=False)
                    rp.room = room
                    rp.save()
                else:
                    # roll back room creation if price invalid (optional)
                    messages.warning(request, "Room added, but price was not saved (invalid).")

            messages.success(request, "Room added successfully.")
            return redirect("dash_rooms")
        else:
            messages.error(request, "Please correct the room form errors.")
    else:
        room_form = RoomForm()
        price_form = RoomPriceForm()

    # --- Display table ---
    rooms_qs = (
        Room.objects
        .annotate(occupied=Count("occupancies", filter=Q(occupancies__active=True)))
        .order_by("name")
    )

    rooms_data = []
    for r in rooms_qs:
        price_obj = r.price_for_date(today)
        room_total = Decimal(price_obj.price) if price_obj else Decimal("0.00")

        per_student = (room_total / Decimal(r.capacity)) if r.capacity else Decimal("0.00")
        per_student = _money(per_student)

        available = max(r.capacity - r.occupied, 0)

        rooms_data.append({
            "name": r.name,
            "capacity": r.capacity,
            "occupied": r.occupied,
            "available": available,
            "room_total": room_total,
            "per_student": per_student,
        })

    return render(request, "dashboard/rooms_list.html", {
        "rooms": rooms_data,
        "room_form": room_form,
        "price_form": price_form,
    })
@login_required
def finance_reports(request):
    month = request.GET.get("month", "").strip()

    if month:
        try:
            y, m = month.split("-")
            y, m = int(y), int(m)
            start = date(y, m, 1)
            end = date(y + (m // 12), (m % 12) + 1, 1)
        except Exception:
            month = ""
            start = None
            end = None
    else:
        start = None
        end = None

    rent_qs = RentPayment.objects.all()
    exp_qs = Expense.objects.all()
    maint_qs = MaintenanceRequest.objects.filter(status="DONE")

    if start and end:
        rent_qs = rent_qs.filter(payment_date__gte=start, payment_date__lt=end)
        exp_qs = exp_qs.filter(expense_date__gte=start, expense_date__lt=end)
        maint_qs = maint_qs.filter(resolved_date__gte=start, resolved_date__lt=end)

    rent_total = rent_qs.aggregate(s=Sum("amount"))["s"] or Decimal("0.00")
    exp_total = exp_qs.aggregate(s=Sum("amount"))["s"] or Decimal("0.00")
    maint_total = maint_qs.aggregate(s=Sum("actual_cost"))["s"] or Decimal("0.00")

    profit_total = rent_total - (exp_total + maint_total)

    rent_monthly = (
        RentPayment.objects
        .annotate(m=TruncMonth("payment_date"))
        .values("m")
        .annotate(total=Sum("amount"))
        .order_by("m")
    )

    exp_monthly = (
        Expense.objects
        .annotate(m=TruncMonth("expense_date"))
        .values("m")
        .annotate(total=Sum("amount"))
        .order_by("m")
    )

    maint_monthly = (
        MaintenanceRequest.objects
        .filter(status="DONE", resolved_date__isnull=False)
        .annotate(m=TruncMonth("resolved_date"))
        .values("m")
        .annotate(total=Sum("actual_cost"))
        .order_by("m")
    )

    month_map = {}

    def add(rows, key):
        for r in rows:
            if r["m"]:
                month_map.setdefault(r["m"], {"rent": 0, "exp": 0, "maint": 0})
                month_map[r["m"]][key] = float(r["total"] or 0)

    add(rent_monthly, "rent")
    add(exp_monthly, "exp")
    add(maint_monthly, "maint")

    months = sorted(month_map.keys())

    labels = [m.strftime("%b %Y") for m in months]
    rent_series = [month_map[m]["rent"] for m in months]
    exp_series = [month_map[m]["exp"] for m in months]
    maint_series = [month_map[m]["maint"] for m in months]
    profit_series = [
        month_map[m]["rent"] - (month_map[m]["exp"] + month_map[m]["maint"])
        for m in months
    ]

    rows = [
        {
            "month": m.strftime("%Y-%m"),
            "rent": Decimal(str(month_map[m]["rent"])),
            "expenses": Decimal(str(month_map[m]["exp"])),
            "maintenance": Decimal(str(month_map[m]["maint"])),
            "profit": Decimal(str(
                month_map[m]["rent"] -
                (month_map[m]["exp"] + month_map[m]["maint"])
            )),
        }
        for m in reversed(months)
    ]

    return render(request, "dashboard/finance_reports.html", {
        "month": month,
        "rent_total": rent_total,
        "exp_total": exp_total,
        "maint_total": maint_total,
        "profit_total": profit_total,
        "labels": labels,
        "rent_series": rent_series,
        "exp_series": exp_series,
        "maint_series": maint_series,
        "profit_series": profit_series,
        "rows": rows[:24],
    })
def maintenance_list(request):
    return render(request, "dashboard/maintenance_list.html")

def reports(request):
    return render(request, "dashboard/reports.html")

def gallery_manager(request):
    return render(request, "dashboard/gallery_manager.html")

def blog_manager(request):
    return render(request, "dashboard/blog_manager.html")

def _month_start_end(d: date):
    start = d.replace(day=1)
    last_day = monthrange(start.year, start.month)[1]
    end = start.replace(day=last_day)
    return start, end

def _due_date_for_month(entry_day: int, month_start: date) -> date:
    # due date = min(entry_day, last day of month)
    last_day = monthrange(month_start.year, month_start.month)[1]
    day = min(int(entry_day), last_day)
    return date(month_start.year, month_start.month, day)

from django.utils import timezone

@transaction.atomic
@login_required
def generate_invoices(request):
    # --- QUICK ACTION: this month ---
    if request.method == "POST" and request.POST.get("action") == "this_month":
        today = timezone.localdate()
        month_start = today.replace(day=1)
        form = InvoiceGenerationForm(initial={"month": today.strftime("%Y-%m")})

    elif request.method == "POST":
        form = InvoiceGenerationForm(request.POST)
        if not form.is_valid():
            messages.error(request, "Please correct the form errors.")
            return render(request, "dashboard/generate_invoices.html", {"form": form})
        month_start = form.cleaned_data["month"]

    else:
        today = timezone.localdate()
        form = InvoiceGenerationForm(initial={"month": today.strftime("%Y-%m")})
        return render(request, "dashboard/generate_invoices.html", {"form": form})

    # ---------- INVOICE GENERATION LOGIC ----------
    period_start, period_end = _month_start_end(month_start)

    created = 0
    skipped = 0

    active_occs = (
        Occupancy.objects
        .select_related("student", "room")
        .filter(active=True)
    )

    for occ in active_occs:
        entry_day = occ.entry_date.day
        due_date = _due_date_for_month(entry_day, month_start)

        price_obj = occ.room.price_for_date(due_date) if hasattr(occ.room, "price_for_date") else None
        amount = Decimal(price_obj.price) if price_obj else Decimal("0.00")

        inv, was_created = RentInvoice.objects.get_or_create(
            student=occ.student,
            period_start=period_start,
            period_end=period_end,
            defaults={
                "due_date": due_date,
                "amount": amount,
                "status": "UNPAID",
            }
        )

        if was_created:
            created += 1
        else:
            skipped += 1

    messages.success(
        request,
        f"Invoices generated for {month_start.strftime('%B %Y')}: "
        f"{created} created, {skipped} already existed."
    )

    return redirect("dash_generate_invoices")


def new_func(request):
    form = InvoiceGenerationForm(request.POST)
    return form


def contact_manager(request):
    return render(request, "dashboard/contact_manager.html")
@login_required
def occupancy_exit(request, occ_id):
    occ = get_object_or_404(Occupancy, id=occ_id)

    if request.method == "POST":
        exit_date_str = request.POST.get("exit_date", "").strip()
        exit_date = timezone.localdate()
        if exit_date_str:
            exit_date = date.fromisoformat(exit_date_str)

        occ.active = False
        occ.exit_date = exit_date
        occ.save(update_fields=["active", "exit_date"])

        messages.success(request, f"{occ.student.full_name} exited from {occ.room.name}.")
        return redirect("dash_occupancy")

    return redirect("dash_occupancy")

@login_required
def occupancy_transfer(request, occ_id):
    occ = get_object_or_404(Occupancy, id=occ_id)

    if request.method == "POST":
        form = TransferForm(request.POST, current_occ=occ)
        if form.is_valid():
            new_room = form.cleaned_data["new_room"]
            transfer_date = form.cleaned_data["transfer_date"]

            # 1) exit current occupancy
            occ.active = False
            occ.exit_date = transfer_date
            occ.save(update_fields=["active", "exit_date"])

            # 2) create new occupancy in new room
            Occupancy.objects.create(
                student=occ.student,
                room=new_room,
                entry_date=transfer_date,
                active=True
            )

            messages.success(request, f"{occ.student.full_name} transferred to {new_room.name}.")
            return redirect("dash_occupancy")
        else:
            messages.error(request, "Transfer failed. Room may be full or date invalid.")

    return redirect("dash_occupancy")
@login_required
def occupancy_assign(request):
    if request.method == "POST":
        form = OccupancyForm(request.POST)
        if form.is_valid():
            occ = form.save(commit=False)
            occ.active = True
            occ.save()
            messages.success(request, "Student assigned to room successfully.")
            return redirect("dash_occupancy")
        else:
            messages.error(request, "Room may be full or form has errors.")
    else:
        form = OccupancyForm()

    occupancies = (
        Occupancy.objects
        .select_related("student", "room")
        .order_by("-entry_date")
    )

    all_rooms = Room.objects.order_by("name")

    return render(
        request,
        "dashboard/occupancy.html",
        {
            "form": form,
            "occupancies": occupancies,
            "all_rooms": all_rooms,
        },
    )
@login_required
def occupancy_exit(request, occ_id):
    occ = get_object_or_404(Occupancy, id=occ_id)

    if request.method == "POST":
        exit_date_str = request.POST.get("exit_date", "").strip()
        exit_date = timezone.localdate()
        if exit_date_str:
            exit_date = date.fromisoformat(exit_date_str)

        occ.active = False
        occ.exit_date = exit_date
        occ.save(update_fields=["active", "exit_date"])

        messages.success(request, f"{occ.student.full_name} exited from {occ.room.name}.")
    return redirect("dash_occupancy")

@login_required
def occupancy_transfer(request, occ_id):
    occ = get_object_or_404(Occupancy, id=occ_id)

    if request.method == "POST":
        form = TransferForm(request.POST, current_occ=occ)
        if form.is_valid():
            new_room = form.cleaned_data["new_room"]
            transfer_date = form.cleaned_data["transfer_date"]

            # Exit current occupancy
            occ.active = False
            occ.exit_date = transfer_date
            occ.save(update_fields=["active", "exit_date"])

            # Create new occupancy
            Occupancy.objects.create(
                student=occ.student,
                room=new_room,
                entry_date=transfer_date,
                active=True,
            )

            messages.success(request, f"{occ.student.full_name} transferred to {new_room.name}.")
        else:
            messages.error(request, "Transfer failed. Room may be full or date invalid.")
    return redirect("dash_occupancy")
@login_required
def maintenance_list(request):
    # Create new request
    if request.method == "POST" and request.POST.get("action") == "create":
        form = MaintenanceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Maintenance request logged.")
            return redirect("dash_maintenance")
        messages.error(request, "Please correct the maintenance form errors.")
    else:
        form = MaintenanceForm()

    # Filters
    status = request.GET.get("status", "").strip()
    room_id = request.GET.get("room", "").strip()
    area_id = request.GET.get("area", "").strip()
    q = request.GET.get("q", "").strip()
    start = request.GET.get("start", "").strip()
    end = request.GET.get("end", "").strip()

    qs = MaintenanceRequest.objects.select_related("room", "area").all()

    if status in ["OPEN", "IN_PROGRESS", "DONE"]:
        qs = qs.filter(status=status)

    if room_id.isdigit():
        qs = qs.filter(room_id=int(room_id))

    if area_id.isdigit():
        qs = qs.filter(area_id=int(area_id))

    if q:
        qs = qs.filter(
            Q(title__icontains=q) |
            Q(description__icontains=q)
        )

    # date range
    if start:
        try:
            qs = qs.filter(reported_date__gte=start)
        except Exception:
            pass
    if end:
        try:
            qs = qs.filter(reported_date__lte=end)
        except Exception:
            pass

    requests = qs.order_by("-reported_date", "-created_at")[:500]

    rooms = Room.objects.order_by("name")
    areas = Area.objects.order_by("name")

    return render(request, "dashboard/maintenance_list.html", {
        "form": form,
        "requests": requests,

        # filter dropdown data
        "rooms": rooms,
        "areas": areas,

        # keep selected values in UI
        "f_status": status,
        "f_room": room_id,
        "f_area": area_id,
        "f_q": q,
        "f_start": start,
        "f_end": end,
    })
@login_required
def maintenance_update(request, req_id):
    mr = get_object_or_404(MaintenanceRequest, id=req_id)

    if request.method == "POST":
        form = MaintenanceUpdateForm(request.POST, instance=mr)
        if form.is_valid():
            updated = form.save(commit=False)

            # If marked DONE and no resolved_date set, default to today
            if updated.status == "DONE" and not updated.resolved_date:
                updated.resolved_date = timezone.localdate()

            updated.save()
            messages.success(request, "Maintenance updated.")
        else:
            messages.error(request, "Update failed. Check values.")
    return redirect("dash_maintenance")

from django.db.models import Sum
from django.db.models.functions import TruncMonth
from datetime import date
from decimal import Decimal

from billing.models import RentPayment
from expenses.models import Expense
from maintenance.models import MaintenanceRequest

@login_required
def finance_reports(request):
    month = request.GET.get("month", "").strip()

    if month:
        try:
            y, m = month.split("-")
            y, m = int(y), int(m)
            start = date(y, m, 1)
            end = date(y + (m // 12), (m % 12) + 1, 1)
        except Exception:
            month = ""
            start = None
            end = None
    else:
        start = None
        end = None

    rent_qs = RentPayment.objects.all()
    exp_qs = Expense.objects.all()
    maint_qs = MaintenanceRequest.objects.filter(status="DONE")

    if start and end:
        rent_qs = rent_qs.filter(payment_date__gte=start, payment_date__lt=end)
        exp_qs = exp_qs.filter(expense_date__gte=start, expense_date__lt=end)
        maint_qs = maint_qs.filter(resolved_date__gte=start, resolved_date__lt=end)

    rent_total = rent_qs.aggregate(s=Sum("amount"))["s"] or Decimal("0.00")
    exp_total = exp_qs.aggregate(s=Sum("amount"))["s"] or Decimal("0.00")
    maint_total = maint_qs.aggregate(s=Sum("actual_cost"))["s"] or Decimal("0.00")

    profit_total = rent_total - (exp_total + maint_total)

    rent_monthly = (
        RentPayment.objects
        .annotate(m=TruncMonth("payment_date"))
        .values("m")
        .annotate(total=Sum("amount"))
        .order_by("m")
    )

    exp_monthly = (
        Expense.objects
        .annotate(m=TruncMonth("expense_date"))
        .values("m")
        .annotate(total=Sum("amount"))
        .order_by("m")
    )

    maint_monthly = (
        MaintenanceRequest.objects
        .filter(status="DONE", resolved_date__isnull=False)
        .annotate(m=TruncMonth("resolved_date"))
        .values("m")
        .annotate(total=Sum("actual_cost"))
        .order_by("m")
    )

    month_map = {}

    def add(rows, key):
        for r in rows:
            if r["m"]:
                month_map.setdefault(r["m"], {"rent": 0, "exp": 0, "maint": 0})
                month_map[r["m"]][key] = float(r["total"] or 0)

    add(rent_monthly, "rent")
    add(exp_monthly, "exp")
    add(maint_monthly, "maint")

    months = sorted(month_map.keys())

    labels = [m.strftime("%b %Y") for m in months]
    rent_series = [month_map[m]["rent"] for m in months]
    exp_series = [month_map[m]["exp"] for m in months]
    maint_series = [month_map[m]["maint"] for m in months]
    profit_series = [
        month_map[m]["rent"] - (month_map[m]["exp"] + month_map[m]["maint"])
        for m in months
    ]

    rows = [
        {
            "month": m.strftime("%Y-%m"),
            "rent": Decimal(str(month_map[m]["rent"])),
            "expenses": Decimal(str(month_map[m]["exp"])),
            "maintenance": Decimal(str(month_map[m]["maint"])),
            "profit": Decimal(str(
                month_map[m]["rent"] -
                (month_map[m]["exp"] + month_map[m]["maint"])
            )),
        }
        for m in reversed(months)
    ]

    return render(request, "dashboard/finance_reports.html", {
        "month": month,
        "rent_total": rent_total,
        "exp_total": exp_total,
        "maint_total": maint_total,
        "profit_total": profit_total,
        "labels": labels,
        "rent_series": rent_series,
        "exp_series": exp_series,
        "maint_series": maint_series,
        "profit_series": profit_series,
        "rows": rows[:24],
    })

from django.db.models import Sum
from django.utils import timezone
from datetime import date
from decimal import Decimal

from billing.models import RentInvoice, RentPayment
from expenses.models import Expense


def _month_range(d: date):
    start = d.replace(day=1)
    if start.month == 12:
        end = start.replace(year=start.year + 1, month=1, day=1)
    else:
        end = start.replace(month=start.month + 1, day=1)
    return start, end


def reports_home(request):
    return render(request, "dashboard/reports_home.html")


def rent_report(request):
    today = timezone.localdate()
    start, end = _month_range(today)

    expected = (
        RentInvoice.objects.filter(issue_date__gte=start, issue_date__lt=end)
        .aggregate(x=Sum("amount"))["x"] or Decimal("0.00")
    )

    collected = (
        RentPayment.objects.filter(paid_on__gte=start, paid_on__lt=end)
        .aggregate(x=Sum("amount"))["x"] or Decimal("0.00")
    )

    return render(request, "dashboard/reports_rent.html", {
        "start": start, "end": end,
        "expected": expected, "collected": collected,
    })


def expenses_report(request):
    today = timezone.localdate()
    start, end = _month_range(today)

    total_expenses = (
        Expense.objects.filter(date__gte=start, date__lt=end)
        .aggregate(x=Sum("amount"))["x"] or Decimal("0.00")
    )

    items = Expense.objects.filter(date__gte=start, date__lt=end).order_by("-date")

    return render(request, "dashboard/reports_expenses.html", {
        "start": start, "end": end,
        "total_expenses": total_expenses,
        "items": items,
    })


def profit_report(request):
    today = timezone.localdate()
    start, end = _month_range(today)

    collected = (
        RentPayment.objects.filter(paid_on__gte=start, paid_on__lt=end)
        .aggregate(x=Sum("amount"))["x"] or Decimal("0.00")
    )

    expenses = (
        Expense.objects.filter(date__gte=start, date__lt=end)
        .aggregate(x=Sum("amount"))["x"] or Decimal("0.00")
    )

    profit = collected - expenses

    return render(request, "dashboard/reports_profit.html", {
        "start": start, "end": end,
        "collected": collected,
        "expenses": expenses,
        "profit": profit,
    })
