from decimal import Decimal
from html import escape

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import select

from bot.buttons import MainMenu, main_menu_keyboard
from bot.user_preferences import language_for_event_user
from db import database
from db.models import Order, Student

router = Router(name="orders")

STATUS_LABELS = {
    "uz": {
        "pending": "Kutilmoqda",
        "paid": "To'langan",
        "shipped": "Yetkazilmoqda",
        "delivered": "Yetkazildi",
        "cancelled": "Bekor qilingan",
    },
    "ru": {
        "pending": "Ожидает",
        "paid": "Оплачен",
        "shipped": "Доставляется",
        "delivered": "Доставлен",
        "cancelled": "Отменен",
    },
}

PAYMENT_STATUS_LABELS = {
    "uz": {
        "pending": "Kutilmoqda",
        "paid": "To'langan",
        "failed": "Muvaffaqiyatsiz",
        "refunded": "Qaytarilgan",
    },
    "ru": {
        "pending": "Ожидает",
        "paid": "Оплачен",
        "failed": "Не удалось",
        "refunded": "Возвращен",
    },
}


def _format_money(value: Decimal) -> str:
    return f"{value:,.0f}".replace(",", " ")


def _fetch_orders(telegram_id: int) -> list[Order]:
    query = (
        select(Order)
        .join(Student)
        .where(Student.telegram_id == telegram_id)
        .order_by(Order.created_at.desc())
        .limit(10)
    )
    return list(database.execute(query).scalars().all())


def _order_items_text(order: Order, language_code: str) -> str:
    lines = []
    for item in order.items[:3]:
        product_name = item.product.name if item.product else "Mahsulot"
        lines.append(f"{escape(product_name)} x {item.quantity}")

    remaining_count = len(order.items) - len(lines)
    if remaining_count > 0:
        remaining_text = {
            "uz": f"yana {remaining_count} ta mahsulot",
            "ru": f"еще {remaining_count} товар(ов)",
        }[language_code]
        lines.append(remaining_text)

    if lines:
        return ", ".join(lines)
    return {"uz": "Mahsulotlar topilmadi", "ru": "Товары не найдены"}[language_code]


@router.message(Command(commands=["orders"]))
@router.message(F.text.in_(MainMenu.texts("orders")))
async def orders_handler(message: Message) -> None:
    language_code = language_for_event_user(message.from_user)
    if message.from_user is None:
        await message.answer(
            {
                "uz": "Foydalanuvchi aniqlanmadi.",
                "ru": "Пользователь не определен.",
            }[language_code],
            reply_markup=main_menu_keyboard(language_code),
        )
        return

    orders = _fetch_orders(message.from_user.id)
    if not orders:
        await message.answer(
            {
                "uz": "📦 Sizning buyurtmalaringiz hali yo'q.",
                "ru": "📦 У вас пока нет заказов.",
            }[language_code],
            reply_markup=main_menu_keyboard(language_code),
        )
        return

    lines = [{"uz": "📦 <b>Buyurtmalarim</b>\n", "ru": "📦 <b>Мои заказы</b>\n"}[language_code]]
    order_status_labels = STATUS_LABELS[language_code]
    payment_status_labels = PAYMENT_STATUS_LABELS[language_code]
    for order in orders:
        payment_status = order.payment.status if order.payment else "pending"
        created_at = order.created_at.strftime("%d.%m.%Y %H:%M")
        if language_code == "ru":
            lines.append(
                f"🧾 <b>#{order.id}</b> - {created_at}\n"
                f"📌 <b>Статус:</b> {order_status_labels.get(order.status, order.status)}\n"
                f"💳 <b>Оплата:</b> {payment_status_labels.get(payment_status, payment_status)}\n"
                f"💰 <b>Итого:</b> {_format_money(order.total_amount)} сум\n"
                f"📦 <b>Товары:</b> {_order_items_text(order, language_code)}"
            )
        else:
            lines.append(
                f"🧾 <b>#{order.id}</b> - {created_at}\n"
                f"📌 <b>Status:</b> {order_status_labels.get(order.status, order.status)}\n"
                f"💳 <b>To'lov:</b> {payment_status_labels.get(payment_status, payment_status)}\n"
                f"💰 <b>Jami:</b> {_format_money(order.total_amount)} so'm\n"
                f"📦 <b>Mahsulotlar:</b> {_order_items_text(order, language_code)}"
            )

    await message.answer(
        "\n\n".join(lines),
        reply_markup=main_menu_keyboard(language_code),
        parse_mode="HTML",
    )
