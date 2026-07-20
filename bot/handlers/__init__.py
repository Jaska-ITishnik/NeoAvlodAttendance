from bot.handlers import cart, catalog, contact, help, orders, profile, settings, start, subscription

routers = (
    start.router,
    help.router,
    subscription.router,
    catalog.router,
    cart.router,
    orders.router,
    profile.router,
    contact.router,
    settings.router,
)

__all__ = ("routers",)
