import datetime
import logging
from typing import Dict, Any
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from models.enums import OrderStatus, DisputeStatus, UserRole, order_types
from config import ADMIN_CHAT_ID, MAX_ORDERS_PER_USER

logger = logging.getLogger(__name__)

class OrderManager:
    def __init__(self, application, db):
        self.application = application
        self.db = db

    async def add_order(self, order_data: Dict[str, Any]) -> str:
        user_orders = self.db.get_user_orders(order_data['client_id'], OrderStatus.ACTIVE.value)
        if len(user_orders) >= MAX_ORDERS_PER_USER:
            raise ValueError(f"Превышен лимит активных заказов ({MAX_ORDERS_PER_USER})")

        order_id = self.db.add_order(order_data)
        await self._notify_admins_about_new_order(order_id)
        return order_id

    async def _update_order_message(self, order_id: str):
        order = self.db.get_order(order_id)
        if not order:
            return

        emoji, type_display = order_types.get(order['type'], ("✏️", "ДРУГОЕ ЗАДАНИЕ"))

        status_text = {
            OrderStatus.ACTIVE.value: "🎯 АКТИВНЫЙ ЗАКАЗ",
            OrderStatus.TAKEN.value: "✅ ПРИНЯТ ИСПОЛНИТЕЛЕМ",
            OrderStatus.IN_PROGRESS.value: "🔄 В РАБОТЕ",
            OrderStatus.UNDER_REVIEW.value: "🔍 НА ПРОВЕРКЕ",
            OrderStatus.COMPLETED.value: "🏁 ЗАВЕРШЕН",
            OrderStatus.CANCELED.value: "❌ ОТМЕНЕН",
            OrderStatus.DISPUTE.value: "⚖️ СПОР"
        }.get(order['status'], "🎯 АКТИВНЫЙ ЗАКАЗ")
        
        client = self.db.get_user(order['client_id'])
        executor_info = ""
        
        if order['executor_id']:
            executor = self.db.get_user(order['executor_id'])
            executor_info = f"\n👨‍💻 *Исполнитель:* @{executor['username']}" if executor else ""
        
        text = (
            f"{status_text}\n\n"
            f"{emoji} *Тип:* {type_display}\n"
            f"📚 *Предмет:* {order.get('subject', 'не указано')}\n"
            f"📝 *Описание:*\n{order.get('description', 'не указано')}\n"
            f"⏰ *Срок:* {order.get('deadline', 'не указано')}\n"
            f"💰 *Бюджет:* {order.get('budget', 'не указано')} руб"
            f"{executor_info}\n\n"
            f"👤 *Клиент:* @{client['username']}\n"
            f"🆔 *ID:* `{order_id}`"
        )
        
        reply_markup = None
        if order['status'] == OrderStatus.ACTIVE.value:
            reply_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Взять заказ", callback_data=f"accept_{order_id}")],
                [InlineKeyboardButton("❌ Отменить", callback_data=f"cancel_{order_id}")]
            ])
        elif order['status'] == OrderStatus.DISPUTE.value:
            dispute = self.db.get_order_dispute(order_id)
            if dispute:
                reply_markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton("⚖️ Принять спор", callback_data=f"take_dispute_{dispute['dispute_id']}")]
                ])
        
        try:
            if order.get('message_id'):
                await self.application.bot.edit_message_text(
                    chat_id=ADMIN_CHAT_ID,
                    message_id=order['message_id'],
                    text=text,
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )
            else:
                sent_message = await self.application.bot.send_message(
                    chat_id=ADMIN_CHAT_ID,
                    text=text,
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )
                self.db.update_order(order_id, {"message_id": sent_message.message_id})
            
        except Exception as e:
            logger.error(f"Ошибка обновления сообщения: {e}")
    
    async def _notify_admins_about_new_order(self, order_id: str):
        order = self.db.get_order(order_id)
        if not order:
            return
        
        emoji, type_display = order_types.get(order['type'], ("✏️", "ДРУГОЕ ЗАДАНИЕ"))
        client = self.db.get_user(order['client_id'])
        
        text = (
            f"🔔 *Новый заказ!*\n\n"
            f"{emoji} *Тип:* {type_display}\n"
            f"📚 *Предмет:* {order.get('subject', 'не указано')}\n"
            f"💰 *Бюджет:* {order.get('budget', 'не указано')} руб\n\n"
            f"👤 *Клиент:* @{client['username']}\n"
            f"🆔 *ID:* `{order_id}`"
        )
        
        try:
            sent_message = await self.application.bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=text,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ Взять заказ", callback_data=f"accept_{order_id}")]
                ]),
                parse_mode="Markdown"
            )
            
            self.db.update_order(order_id, {"message_id": sent_message.message_id})
            
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления в чат Study-Offers: {e}")
    
    async def accept_order(self, order_id: str, executor_id: int) -> bool:
        order = self.db.get_order(order_id)
        if not order or order['status'] != OrderStatus.ACTIVE.value:
            return False
        
        self.db.update_order(order_id, {
            "status": OrderStatus.TAKEN.value,
            "executor_id": executor_id
        })
        
        executor = self.db.get_user(executor_id)
        client = self.db.get_user(order['client_id'])
        
        if client:
            try:
                await self.application.bot.send_message(
                    chat_id=client['user_id'],
                    text=(
                        f"🎉 Ваш заказ *{order_id}* принят исполнителем!\n\n"
                        f"👨‍💻 *Исполнитель:* @{executor['username']}\n"
                        f"📞 Свяжитесь с исполнителем для уточнения деталей."
                    ),
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(f"Ошибка отправки уведомления клиенту: {e}")
        
        await self._update_order_message(order_id)
        return True
    
    async def cancel_order(self, order_id: str, canceled_by: int) -> bool:
        order = self.db.get_order(order_id)
        if not order:
            return False
        
        self.db.update_order(order_id, {
            "status": OrderStatus.CANCELED.value
        })
        
        client = self.db.get_user(order['client_id'])
        executor = self.db.get_user(order['executor_id']) if order['executor_id'] else None
        canceled_by_user = self.db.get_user(canceled_by)
        
        notification_text = (
            f"⚠️ Заказ *{order_id}* отменен пользователем @{canceled_by_user['username']}\n\n"
            f"📚 *Предмет:* {order.get('subject', 'не указано')}\n"
            f"💰 *Бюджет:* {order.get('budget', 'не указано')} руб"
        )
        
        if canceled_by != client['user_id'] and client:
            try:
                await self.application.bot.send_message(
                    chat_id=client['user_id'],
                    text=notification_text,
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(f"Ошибка отправки уведомления клиенту: {e}")
        
        if executor and canceled_by != executor['user_id']:
            try:
                await self.application.bot.send_message(
                    chat_id=executor['user_id'],
                    text=notification_text,
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(f"Ошибка отправки уведомления исполнителю: {e}")
        
        await self._update_order_message(order_id)
        return True
    
    async def complete_order(self, order_id: str) -> bool:
        order = self.db.get_order(order_id)
        if not order or order['status'] not in [OrderStatus.TAKEN.value, OrderStatus.IN_PROGRESS.value, OrderStatus.UNDER_REVIEW.value]:
            return False
        
        self.db.update_order(order_id, {
            "status": OrderStatus.COMPLETED.value,
            "completed_at": datetime.datetime.now().isoformat()
        })
        
        client = self.db.get_user(order['client_id'])
        executor = self.db.get_user(order['executor_id']) if order['executor_id'] else None
        
        notification_text = (
            f"🏁 Заказ *{order_id}* завершен!\n\n"
            f"📚 *Предмет:* {order.get('subject', 'не указано')}\n"
            f"💰 *Бюджет:* {order.get('budget', 'не указано')} руб\n\n"
            f"Пожалуйста, оцените работу исполнителя."
        )
        
        if client:
            try:
                await self.application.bot.send_message(
                    chat_id=client['user_id'],
                    text=notification_text,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("⭐ Оценить исполнителя", callback_data=f"rate_{order_id}")]
                    ]),
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(f"Ошибка отправки уведомления клиенту: {e}")
        
        if executor:
            try:
                await self.application.bot.send_message(
                    chat_id=executor['user_id'],
                    text=notification_text,
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(f"Ошибка отправки уведомления исполнителю: {e}")
        
        await self._update_order_message(order_id)
        return True
    
    async def open_dispute(self, order_id: str, opened_by: int, reason: str) -> bool:
        order = self.db.get_order(order_id)
        if not order or order['status'] == OrderStatus.CANCELED.value or order['status'] == OrderStatus.COMPLETED.value:
            return False
        
        dispute_id = self.db.add_dispute(order_id, opened_by, reason)
        
        client = self.db.get_user(order['client_id'])
        executor = self.db.get_user(order['executor_id']) if order['executor_id'] else None
        opened_by_user = self.db.get_user(opened_by)
        
        notification_text = (
            f"⚖️ По заказу *{order_id}* открыт спор!\n\n"
            f"👤 *Инициатор:* @{opened_by_user['username']}\n"
            f"📝 *Причина:* {reason}\n\n"
            f"Администратор скоро свяжется с вами для разрешения ситуации."
        )
        
        if opened_by != client['user_id'] and client:
            try:
                await self.application.bot.send_message(
                    chat_id=client['user_id'],
                    text=notification_text,
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(f"Ошибка отправки уведомления клиенту: {e}")
        
        if executor and opened_by != executor['user_id']:
            try:
                await self.application.bot.send_message(
                    chat_id=executor['user_id'],
                    text=notification_text,
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(f"Ошибка отправки уведомления исполнителю: {e}")
        
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE role = ?", (UserRole.ADMIN.value,))
        admins = cursor.fetchall()
        
        for admin in admins:
            try:
                await self.application.bot.send_message(
                    chat_id=admin[0],
                    text=(
                        f"⚖️ *Новый спор!*\n\n"
                        f"🆔 *ID спора:* `{dispute_id}`\n"
                        f"🆔 *ID заказа:* `{order_id}`\n"
                        f"👤 *Инициатор:* @{opened_by_user['username']}\n"
                        f"📝 *Причина:* {reason}\n\n"
                        f"Для принятия спора нажмите кнопку ниже."
                    ),
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("⚖️ Принять спор", callback_data=f"take_dispute_{dispute_id}")]
                    ]),
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(f"Ошибка отправки уведомления админу {admin[0]}: {e}")
        
        await self._update_order_message(order_id)
        return True
    
    async def resolve_dispute(self, dispute_id: str, admin_id: int, resolution: str, accept: bool) -> bool:
        dispute = self.db.get_dispute(dispute_id)
        if not dispute or dispute['status'] != DisputeStatus.OPENED.value:
            return False
        
        order = self.db.get_order(dispute['order_id'])
        if not order:
            return False
        
        new_status = DisputeStatus.RESOLVED.value if accept else DisputeStatus.REJECTED.value
        self.db.update_dispute(dispute_id, {
            "status": new_status,
            "admin_id": admin_id,
            "resolution": resolution,
            "resolved_at": datetime.datetime.now().isoformat()
        })
        
        if accept:
            self.db.update_order(order['order_id'], {"status": OrderStatus.CANCELED.value})
        else:
            self.db.update_order(order['order_id'], {"status": OrderStatus.IN_PROGRESS.value})
        
        client = self.db.get_user(order['client_id'])
        executor = self.db.get_user(order['executor_id']) if order['executor_id'] else None
        admin = self.db.get_user(admin_id)
        
        resolution_text = (
            f"⚖️ *Спор по заказу {order['order_id']} разрешен!*\n\n"
            f"👤 *Администратор:* @{admin['username']}\n"
            f"📝 *Решение:* {resolution}\n"
            f"🔹 *Результат:* {'Принято' if accept else 'Отклонено'}\n\n"
        )
        
        if accept:
            resolution_text += "Заказ отменен, средства будут возвращены заказчику."
        else:
            resolution_text += "Заказ возвращен в работу."
        
        if client:
            try:
                await self.application.bot.send_message(
                    chat_id=client['user_id'],
                    text=resolution_text,
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(f"Ошибка отправки уведомления клиенту: {e}")
        
        if executor:
            try:
                await self.application.bot.send_message(
                    chat_id=executor['user_id'],
                    text=resolution_text,
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(f"Ошибка отправки уведомления исполнителю: {e}")
        
        await self._update_order_message(order['order_id'])
        return True