from django.shortcuts import render
from django.db.models import Count, Q
from decimal import Decimal, ROUND_HALF_UP
from datetime import date

from rooms.models import Room

WHATSAPP_LINK = "https://wa.me/260977316161?text=Hello%20Sunrise%20Student%20Boarding%20House,%20I%20would%20like%20to%20book%20a%20bedspace."

BLOG_POSTS = [
    {"title": "How to Choose a Good Boarding House in Lusaka", "slug": "choose-boarding-house", "summary": "Key things students should check before renting.", "date": "Jan 2026"},
    {"title": "How Sunrise Ensures Safety & Cleanliness", "slug": "safety-cleanliness", "summary": "Our standards for student comfort and security.", "date": "Jan 2026"},
]

def _money_round(x: Decimal) -> Decimal:
    return x.quantize(Decimal("1"), rounding=ROUND_HALF_UP)

def home(request):
    today = date.today()

    rooms_qs = (
        Room.objects
        .annotate(occupied=Count("occupancies", filter=Q(occupancies__active=True)))
        .order_by("name")
    )

    rooms = []
    total_available = 0

    for room in rooms_qs:
        price_obj = room.price_for_date(today)
        room_price = price_obj.price if price_obj else Decimal("0")

        per_student = (room_price / Decimal(room.capacity)) if room.capacity else Decimal("0")
        per_student = _money_round(per_student)

        available = max(room.capacity - room.occupied, 0)
        total_available += available

        rooms.append({
            "id": room.id,
            "name": room.name,
            "capacity": room.capacity,
            "occupied": room.occupied,
            "available": available,
            "price_per_student": per_student,
            "img": "img/placeholder_room.jpg",
        })

    return render(request, "public/home.html", {
        "available_beds": total_available,
        "rooms": rooms[:3],
        "whatsapp_link": WHATSAPP_LINK,
    })

def rooms(request):
    today = date.today()
    rooms_qs = (
        Room.objects
        .annotate(occupied=Count("occupancies", filter=Q(occupancies__active=True)))
        .order_by("name")
    )

    rooms_data = []
    for room in rooms_qs:
        price_obj = room.price_for_date(today)
        room_price = price_obj.price if price_obj else Decimal("0")

        per_student = (room_price / Decimal(room.capacity)) if room.capacity else Decimal("0")
        per_student = _money_round(per_student)

        available = max(room.capacity - room.occupied, 0)

        rooms_data.append({
            "id": room.id,
            "name": room.name,
            "capacity": room.capacity,
            "occupied": room.occupied,
            "available": available,
            "price_per_student": per_student,
            "img": "img/placeholder_room.jpg",
        })

    return render(request, "public/rooms.html", {"rooms": rooms_data, "whatsapp_link": WHATSAPP_LINK})

def gallery(request):
    return render(request, "public/gallery.html", {"whatsapp_link": WHATSAPP_LINK})

def features(request):
    return render(request, "public/features.html", {"whatsapp_link": WHATSAPP_LINK})

def tips_list(request):
    return render(request, "public/tips_list.html", {"posts": BLOG_POSTS, "whatsapp_link": WHATSAPP_LINK})

def tips_detail(request, slug):
    post = next((p for p in BLOG_POSTS if p["slug"] == slug), None)
    return render(request, "public/tips_detail.html", {"post": post, "whatsapp_link": WHATSAPP_LINK})

def contact(request):
    return render(request, "public/contact.html", {"whatsapp_link": WHATSAPP_LINK})

