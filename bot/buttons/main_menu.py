from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


DEFAULT_LANGUAGE = "uz"
SUPPORTED_LANGUAGES = ("uz", "ru")


def normalize_language(language_code: str | None) -> str:
    if language_code in SUPPORTED_LANGUAGES:
        return language_code
    return DEFAULT_LANGUAGE


class MainMenu:
    CATALOG = "🛍 Katalog"
    CART = "🛒 Savat"
    ORDERS = "📦 Buyurtmalarim"
    SEARCH = "🔎 Qidirish"
    PROFILE = "👤 Profil"
    CONTACT = "📞 Aloqa"
    SETTINGS = "⚙️ Sozlamalar"

    LABELS = {
        "uz": {
            "catalog": CATALOG,
            "cart": CART,
            "orders": ORDERS,
            "search": SEARCH,
            "profile": PROFILE,
            "contact": CONTACT,
            "settings": SETTINGS,
        },
        "ru": {
            "catalog": "🛍 Каталог",
            "cart": "🛒 Корзина",
            "orders": "📦 Мои заказы",
            "search": "🔎 Поиск",
            "profile": "👤 Профиль",
            "contact": "📞 Связь",
            "settings": "⚙️ Настройки",
        },
    }

    @classmethod
    def text(cls, key: str, language_code: str | None = None) -> str:
        language_code = normalize_language(language_code)
        return cls.LABELS[language_code][key]

    @classmethod
    def texts(cls, key: str) -> set[str]:
        return {labels[key] for labels in cls.LABELS.values()}

    @classmethod
    def all_texts(cls) -> set[str]:
        return {text for labels in cls.LABELS.values() for text in labels.values()}


def main_menu_keyboard(language_code: str | None = None) -> ReplyKeyboardMarkup:
    language_code = normalize_language(language_code)
    labels = MainMenu.LABELS[language_code]
    placeholder = {
        "uz": "👇 Kerakli bo'limni tanlang",
        "ru": "👇 Выберите нужный раздел",
    }[language_code]

    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=labels["catalog"]),
                KeyboardButton(text=labels["cart"]),
            ],
            [
                KeyboardButton(text=labels["orders"]),
                KeyboardButton(text=labels["search"]),
            ],
            [
                KeyboardButton(text=labels["profile"]),
                KeyboardButton(text=labels["contact"]),
            ],
            [
                KeyboardButton(text=labels["settings"]),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder=placeholder,
    )
