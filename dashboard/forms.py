from django import forms
from django.core.exceptions import ValidationError
from rooms.models import Room, RoomPrice
from rooms.models import Room
from tenants.models import Student
from tenants.models import Occupancy
from billing.models import RentInvoice, RentPayment
from expenses.models import Expense
from maintenance.models import MaintenanceRequest
from django.utils import timezone
from maintenance.models import MaintenanceRequest, Area

""" class PaymentForm(forms.ModelForm):
    invoice = forms.ModelChoiceField(
        queryset=RentInvoice.objects.exclude(status="PAID").order_by("-due_date"),
        empty_label="Select invoice...",
        widget=forms.Select(attrs={"class": "form-select"})
    )

    class Meta:
        model = RentPayment
        fields = ["invoice", "amount", "method", "reference"]
        widgets = {
            "amount": forms.NumberInput(attrs={"class": "form-control", "placeholder": "e.g. 750"}),
            "method": forms.Select(attrs={"class": "form-select"}),
            "reference": forms.TextInput(attrs={"class": "form-control", "placeholder": "Transaction reference (optional)"}),
        } """
class PaymentForm(forms.ModelForm):
    class Meta:
        model = RentPayment
        fields = ["invoice", "amount", "method", "reference"]
        widgets = {
            "invoice": forms.Select(attrs={"class": "form-select"}),
            "amount": forms.NumberInput(attrs={"class": "form-control"}),
            "method": forms.Select(attrs={"class": "form-select"}),
            "reference": forms.TextInput(attrs={"class": "form-control"}),
        }


from django import forms
from tenants.models import Student


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            "full_name",
            "phone",
            "guardian_name",
            "guardian_phone",
            "school",
        ]

        widgets = {
            "full_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Student full name"
            }),

            "phone": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. 0977xxxxxx"
            }),

            "guardian_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Guardian full name"
            }),

            "guardian_phone": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Guardian phone number"
            }),

            "school": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "School / University"
            }),
        }



class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ["category", "amount", "expense_date", "notes"]
        widgets = {
            "category": forms.Select(attrs={"class": "form-select"}),
            "amount": forms.NumberInput(attrs={"class": "form-control", "placeholder": "e.g. 1200"}),
            "expense_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Optional notes..."}),
        }

class OccupancyForm(forms.ModelForm):
    room = forms.ModelChoiceField(
        queryset=Room.objects.all(),
        widget=forms.Select(attrs={"class": "form-select"})
    )

    class Meta:
        model = Occupancy
        fields = ["student", "room", "entry_date"]
        widgets = {
            "student": forms.Select(attrs={"class": "form-select"}),
            "entry_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        }

    def clean(self):
        cleaned = super().clean()
        room = cleaned.get("room")

        if room:
            occupied = room.occupancies.filter(active=True).count()
            if occupied >= room.capacity:
                raise ValidationError(f"{room.name} is already full.")

        return cleaned
from django.utils import timezone

class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ["name", "capacity", "description"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Master Bedroom (Self Contained)"}),
            "capacity": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 2, "placeholder": "Optional description..."}),
        }


class RoomPriceForm(forms.ModelForm):
    class Meta:
        model = RoomPrice
        fields = ["price", "start_date"]
        widgets = {
            "price": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Total room price per month"}),
            "start_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # default start_date = today (nice UX)
        if not self.initial.get("start_date"):
            self.initial["start_date"] = timezone.localdate()

from django import forms
from django.utils import timezone

class InvoiceGenerationForm(forms.Form):
    month = forms.DateField(
        widget=forms.DateInput(attrs={"class": "form-control", "type": "month"}),
        help_text="Select the month to generate invoices for."
    )

    def clean_month(self):
        # HTML month input returns YYYY-MM-01 in many browsers; that's okay.
        m = self.cleaned_data["month"]
        return m.replace(day=1)

class TransferForm(forms.Form):
    new_room = forms.ModelChoiceField(
        queryset=Room.objects.order_by("name"),
        widget=forms.Select(attrs={"class": "form-select"})
    )
    transfer_date = forms.DateField(
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"})
    )

    def __init__(self, *args, current_occ=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_occ = current_occ

        # default date = today
        from django.utils import timezone
        if not self.initial.get("transfer_date"):
            self.initial["transfer_date"] = timezone.localdate()

        # exclude current room
        if current_occ:
            self.fields["new_room"].queryset = Room.objects.exclude(id=current_occ.room_id).order_by("name")

    def clean(self):
        cleaned = super().clean()
        new_room = cleaned.get("new_room")
        transfer_date = cleaned.get("transfer_date")

        if self.current_occ and transfer_date:
            if transfer_date < self.current_occ.entry_date:
                raise ValidationError("Transfer date cannot be before entry date.")

        if new_room:
            occupied = new_room.occupancies.filter(active=True).count()
            if occupied >= new_room.capacity:
                raise ValidationError(f"{new_room.name} is already full.")

        return cleaned
class TransferForm(forms.Form):
    new_room = forms.ModelChoiceField(
        queryset=Room.objects.order_by("name"),
        widget=forms.Select(attrs={"class": "form-select"})
    )
    transfer_date = forms.DateField(
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"})
    )

    def __init__(self, *args, current_occ=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_occ = current_occ
        from django.utils import timezone
        if not self.initial.get("transfer_date"):
            self.initial["transfer_date"] = timezone.localdate()

        if current_occ:
            self.fields["new_room"].queryset = Room.objects.exclude(id=current_occ.room_id).order_by("name")

    def clean(self):
        cleaned = super().clean()
        new_room = cleaned.get("new_room")
        transfer_date = cleaned.get("transfer_date")

        if self.current_occ and transfer_date and transfer_date < self.current_occ.entry_date:
            raise ValidationError("Transfer date cannot be before entry date.")

        if new_room:
            occupied = new_room.occupancies.filter(active=True).count()
            if occupied >= new_room.capacity:
                raise ValidationError(f"{new_room.name} is already full.")

        return cleaned
class MaintenanceForm(forms.ModelForm):
    class Meta:
        model = MaintenanceRequest
        fields = ["room", "title", "description", "reported_date", "estimated_cost"]
        widgets = {
            "room": forms.Select(attrs={"class": "form-select"}),
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Replace broken shower head"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Details..."}),
            "reported_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "estimated_cost": forms.NumberInput(attrs={"class": "form-control", "placeholder": "0.00"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if not self.initial.get("reported_date"):
            self.initial["reported_date"] = timezone.localdate()
            

class MaintenanceUpdateForm(forms.ModelForm):
    class Meta:
        model = MaintenanceRequest
        fields = ["status", "resolved_date", "actual_cost"]
        widgets = {
            "status": forms.Select(attrs={"class": "form-select form-select-sm"}),
            "resolved_date": forms.DateInput(attrs={"class": "form-control form-control-sm", "type": "date"}),
            "actual_cost": forms.NumberInput(attrs={"class": "form-control form-control-sm", "placeholder": "0.00"}),
        }
    
class MaintenanceForm(forms.ModelForm):
    class Meta:
        model = MaintenanceRequest
        fields = ["room", "area", "title", "description", "reported_date", "estimated_cost"]
        widgets = {
            "room": forms.Select(attrs={"class": "form-select"}),
            "area": forms.Select(attrs={"class": "form-select"}),
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Fix leaking shower tap"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "reported_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "estimated_cost": forms.NumberInput(attrs={"class": "form-control"}),
        }

def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.fields["area"].queryset = Area.objects.order_by("name")
    self.fields["room"].queryset = Room.objects.order_by("name")

