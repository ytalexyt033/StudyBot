from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from models.user import User
from services.database import Database

class UserMiddleware(BaseMiddleware):
    def __init__(self, db: Database):
        self.db = db
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        from_user = None
        
        if hasattr(event, 'message') and event.message:
            from_user = event.message.from_user
        elif hasattr(event, 'callback_query') and event.callback_query:
            from_user = event.callback_query.from_user
        elif hasattr(event, 'from_user'):
            from_user = event.from_user
        
        if from_user:
            user = User(
                user_id=from_user.id,
                username=from_user.username,
                first_name=from_user.first_name,
                last_name=from_user.last_name
            )
            self.db.add_user(user)
            data['user'] = user
        
        data['db'] = self.db
        return await handler(event, data)