from typing import Optional
from uuid import uuid4
from datetime import datetime

from aiogram import Bot
from models.order import Order
from models.user import User
from config.constants import OrderStatus, ORDER_TYPES
from config.settings import ADMIN_CHAT_ID, MAX_ORDERS_PER_USER

class OrderService:
    def __init__(self, bot: Bot, db):
        self.bot = bot
        self.db = db
        self.max_orders = MAX_ORDERS_PER_USER
    
    async def create_order(self, order_data: dict, client_id: int) -> Optional[Order]:
        if len(self.db.get_user_orders(client_id, OrderStatus.ACTIVE.value)) >= self.max_orders:
            return None
        
        order_id = str(uuid4())
        order = Order(
            order_id=order_id,
            type=order_data['type'],
            subject=order_data['subject'],
            description=order_data['description'],
            deadline=order_data['deadline'],
            budget=order_data['budget'],
            client_id=client_id,
            file_path=order_data.get('file_path')
        )
        
        self.db.add_order(order)
        await self._notify_admins(order)
        return order
    
    async def _notify_admins(self, order: Order):
        emoji, type_display = ORDER_TYPES.get(order.type, ("✏️", "ДРУГОЕ ЗАДАНИЕ"))
        client = self.db.get_user(order.client_id)
        
        text = (
            f"🔔 *Новый заказ!*\n\n"
            f"{emoji} *Тип:* {type_display}\n"
            f"📚 *Предмет:* {order.subject}\n"
            f"💰 *Бюджет:* {order.budget} руб\n\n"
            f"👤 *Клиент:* {client.mention}\n"
            f"🆔 *ID:* `{order.order_id}`"
        )
        
        try:
            from keyboards.order_kb import get_order_accept_kb
            sent_message = await self.bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=text,
                reply_markup=get_order_accept_kb(order.order_id),
                parse_mode="Markdown"
            )
            
            self.db.update_order(order.order_id, {"message_id": sent_message.message_id})
        except Exception as e:
            print(f"Ошибка отправки уведомления: {e}")
    
    async def accept_order(self, order_id: str, executor_id: int) -> bool:
        order = self.db.get_order(order_id)
        if not order or order.status != OrderStatus.ACTIVE.value:
            return False
        
        self.db.update_order(order_id, {
            "status": OrderStatus.TAKEN.value,
            "executor_id": executor_id
        })
        
        executor = self.db.get_user(executor_id)
        client = self.db.get_user(order.client_id)
        
        if client:
            try:
                await self.bot.send_message(
                    chat_id=client.user_id,
                    text=(
                        f"🎉 Ваш заказ *{order_id}* принят исполнителем!\n\n"
                        f"👨‍💻 *Исполнитель:* {executor.mention}\n"
                        f"📞 Свяжитесь с исполнителем для уточнения деталей."
                    ),
                    parse_mode="Markdown"
                )
            except Exception as e:
                print(f"Ошибка отправки уведомления клиенту: {e}")
        
        await self._update_order_message(order_id)
        return True
    
    async def _update_order_message(self, order_id: str):
        order = self.db.get_order(order_id)
        if not order:
            return
        
        emoji, type_display = ORDER_TYPES.get(order.type, ("✏️", "ДРУГОЕ ЗАДАНИЕ"))
        status_text = order.status_display
        
        client = self.db.get_user(order.client_id)
        executor_info = ""
        
        if order.executor_id:
            executor = self.db.get_user(order.executor_id)
            executor_info = f"\n👨‍💻 *Исполнитель:* {executor.mention}" if executor else ""
        
        text = (
            f"{status_text}\n\n"
            f"{emoji} *Тип:* {type_display}\n"
            f"📚 *Предмет:* {order.subject}\n"
            f"📝 *Описание:*\n{order.description}\n"
            f"⏰ *Срок:* {order.deadline}\n"
            f"💰 *Бюджет:* {order.budget} руб"
            f"{executor_info}\n\n"
            f"👤 *Клиент:* {client.mention}\n"
            f"🆔 *ID:* `{order.order_id}`"
        )
        
        try:
            from keyboards.order_kb import get_order_actions_kb
            await self.bot.edit_message_text(
                chat_id=ADMIN_CHAT_ID,
                message_id=order.message_id,
                text=text,
                reply_markup=get_order_actions_kb(order),
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"Ошибка обновления сообщения: {e}")
    
    async def complete_order(self, order_id: str) -> bool:
        order = self.db.get_order(order_id)
        if not order or order.status not in [
            OrderStatus.TAKEN.value, 
            OrderStatus.IN_PROGRESS.value, 
            OrderStatus.UNDER_REVIEW.value
        ]:
            return False
        
        self.db.update_order(order_id, {
            "status": OrderStatus.COMPLETED.value,
            "completed_at": datetime.now().isoformat()
        })
        
        client = self.db.get_user(order.client_id)
        executor = self.db.get_user(order.executor_id) if order.executor_id else None
        
        notification_text = (
            f"🏁 Заказ *{order_id}* завершен!\n\n"
            f"📚 *Предмет:* {order.subject}\n"
            f"💰 *Бюджет:* {order.budget} руб\n\n"
            f"Пожалуйста, оцените работу исполнителя."
        )
        
        if client:
            try:
                from keyboards.order_kb import get_rating_kb
                await self.bot.send_message(
                    chat_id=client.user_id,
                    text=notification_text,
                    reply_markup=get_rating_kb(order_id),
                    parse_mode="Markdown"
                )
            except Exception as e:
                print(f"Ошибка отправки уведомления клиенту: {e}")
        
        if executor:
            try:
                await self.bot.send_message(
                    chat_id=executor.user_id,
                    text=notification_text,
                    parse_mode="Markdown"
                )
            except Exception as e:
                print(f"Ошибка отправки уведомления исполнителю: {e}")
        
        await self._update_order_message(order_id)
        return True
    
    async def cancel_order(self, order_id: str, canceled_by: int) -> bool:
        order = self.db.get_order(order_id)
        if not order:
            return False
        
        self.db.update_order(order_id, {"status": OrderStatus.CANCELED.value})
        
        client = self.db.get_user(order.client_id)
        executor = self.db.get_user(order.executor_id) if order.executor_id else None
        canceled_by_user = self.db.get_user(canceled_by)
        
        notification_text = (
            f"⚠️ Заказ *{order_id}* отменен пользователем {canceled_by_user.mention}\n\n"
            f"📚 *Предмет:* {order.subject}\n"
            f"💰 *Бюджет:* {order.budget} руб"
        )
        
        if canceled_by != client.user_id and client:
            try:
                await self.bot.send_message(
                    chat_id=client.user_id,
                    text=notification_text,
                    parse_mode="Markdown"
                )
            except Exception as e:
                print(f"Ошибка отправки уведомления клиенту: {e}")
        
        if executor and canceled_by != executor.user_id:
            try:
                await self.bot.send_message(
                    chat_id=executor.user_id,
                    text=notification_text,
                    parse_mode="Markdown"
                )
            except Exception as e:
                print(f"Ошибка отправки уведомления исполнителю: {e}")
        
        await self._update_order_message(order_id)
        return True