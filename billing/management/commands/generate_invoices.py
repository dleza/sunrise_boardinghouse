from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

from tenants.models import Occupancy
from billing.models import RentInvoice, BreakMonthSetting

def add_one_month(d: date) -> date:
    # safe month increment (keeps day where possible)
    year = d.year + (d.month // 12)
    month = (d.month % 12) + 1
    day = d.day

    # clamp day to last day of new month
    import calendar
    last_day = calendar.monthrange(year, month)[1]
    day = min(day, last_day)
    return date(year, month, day)

def money(x: Decimal) -> Decimal:
    return x.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

class Command(BaseCommand):
    help = "Generate monthly rent invoices for active occupancies (entry-date billing)."

    def add_arguments(self, parser):
        parser.add_argument("--date", type=str, help="Run as if today is YYYY-MM-DD")

    @transaction.atomic
    def handle(self, *args, **options):
        if options.get("--date"):
            today = date.fromisoformat(options["--date"])
        else:
            today = timezone.localdate()

        # Break month multipliers (default 1.00)
        bm = {s.month: s.rent_multiplier for s in BreakMonthSetting.objects.all()}
        multiplier = bm.get(today.month, Decimal("1.00"))

        active_occs = Occupancy.objects.filter(active=True)

        created = 0
        skipped = 0

        for occ in active_occs:
            # only generate on the student's billing day (entry day)
            if occ.entry_date.day != today.day:
                continue

            # Determine room total price for this due date
            price_obj = occ.room.price_for_date(today)
            if not price_obj:
                self.stdout.write(self.style.WARNING(
                    f"Skipping {occ.student} ({occ.room}): no room price found for {today}"
                ))
                skipped += 1
                continue

            room_total = Decimal(price_obj.price)
            per_student = room_total / Decimal(occ.room.capacity)
            per_student = money(per_student * multiplier)

            # Determine billing period: from previous due date to this due date - 1 day
            period_start = add_one_month(today.replace(day=occ.entry_date.day))  # not used; better compute below

            # Better: period is [today - 1 month, today - 1 day]
            prev_due = add_one_month(today)  # placeholder
            # compute previous due correctly:
            # previous due date is one month before today, same billing day clamped
            import calendar
            y, m = today.year, today.month
            if m == 1:
                py, pm = y - 1, 12
            else:
                py, pm = y, m - 1
            last_day_prev = calendar.monthrange(py, pm)[1]
            prev_day = min(occ.entry_date.day, last_day_prev)
            prev_due = date(py, pm, prev_day)

            period_start = prev_due
            period_end = today - timedelta(days=1)

            inv, was_created = RentInvoice.objects.get_or_create(
                occupancy=occ,
                due_date=today,
                defaults={
                    "student": occ.student,
                    "period_start": period_start,
                    "period_end": period_end,
                    "amount_due": per_student,
                }
            )
            if was_created:
                created += 1
            else:
                skipped += 1

        self.stdout.write(self.style.SUCCESS(
            f"Invoice generation complete for {today}: created={created}, skipped={skipped}"
        ))
