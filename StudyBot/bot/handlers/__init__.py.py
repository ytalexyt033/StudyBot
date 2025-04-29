from .common import register_common_handlers
from .order_handlers import register_order_handlers
from .admin_handlers import register_admin_handlers

def register_handlers(application):
    register_common_handlers(application)
    register_order_handlers(application)
    register_admin_handlers(application)