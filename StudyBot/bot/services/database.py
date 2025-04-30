import sqlite3
from typing import Dict, Any, List, Optional
from pathlib import Path
import uuid
from datetime import datetime

from models.user import User
from models.order import Order
from models.dispute import Dispute
from config.settings import DB_NAME
from config.constants import OrderStatus, UserRole, DisputeStatus

class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DB_NAME)
        self._create_tables()
    
    def _create_tables(self):
        """Создает все необходимые таблицы в базе данных"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            role TEXT DEFAULT 'customer',
            rating REAL DEFAULT 0,
            completed_orders INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id TEXT PRIMARY KEY,
            type TEXT,
            subject TEXT,
            description TEXT,
            deadline TEXT,
            budget INTEGER,
            client_id INTEGER,
            executor_id INTEGER,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            file_path TEXT,
            message_id INTEGER,
            FOREIGN KEY (client_id) REFERENCES users (user_id),
            FOREIGN KEY (executor_id) REFERENCES users (user_id)
        )""")
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_messages (
            message_id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT,
            user_id INTEGER,
            message TEXT,
            is_file INTEGER DEFAULT 0,
            file_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (order_id) REFERENCES orders (order_id),
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )""")
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS disputes (
            dispute_id TEXT PRIMARY KEY,
            order_id TEXT,
            opened_by INTEGER,
            admin_id INTEGER,
            reason TEXT,
            status TEXT DEFAULT 'opened',
            resolution TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resolved_at TIMESTAMP,
            FOREIGN KEY (order_id) REFERENCES orders (order_id),
            FOREIGN KEY (opened_by) REFERENCES users (user_id),
            FOREIGN KEY (admin_id) REFERENCES users (user_id)
        )""")
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS ratings (
            rating_id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT,
            executor_id INTEGER,
            customer_id INTEGER,
            rating INTEGER,
            comment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (order_id) REFERENCES orders (order_id),
            FOREIGN KEY (executor_id) REFERENCES users (user_id),
            FOREIGN KEY (customer_id) REFERENCES users (user_id)
        )""")
        
        self.conn.commit()

    def add_user(self, user: User) -> None:
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO users (user_id, username, first_name, last_name) VALUES (?, ?, ?, ?)",
            (user.user_id, user.username, user.first_name, user.last_name)
        )
        self.conn.commit()
    
    def get_user(self, user_id: int) -> Optional[User]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if row:
            return User(
                user_id=row[0],
                username=row[1],
                first_name=row[2],
                last_name=row[3],
                role=row[4],
                rating=row[5],
                completed_orders=row[6],
                created_at=row[7]
            )
        return None
    
    def set_user_role(self, user_id: int, role: UserRole) -> bool:
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE users SET role = ? WHERE user_id = ?",
            (role.value, user_id)
        )
        self.conn.commit()
        return cursor.rowcount > 0
    
    def add_order(self, order: Order) -> str:
        cursor = self.conn.cursor()
        cursor.execute(
            """INSERT INTO orders (
                order_id, type, subject, description, deadline, budget,
                client_id, executor_id, status, file_path, message_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                order.order_id, order.type, order.subject,
                order.description, order.deadline,
                order.budget, order.client_id, order.executor_id,
                order.status, order.file_path, order.message_id
            )
        )
        self.conn.commit()
        return order.order_id
    
    def get_order(self, order_id: str) -> Optional[Order]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,))
        row = cursor.fetchone()
        if row:
            return Order(
                order_id=row[0],
                type=row[1],
                subject=row[2],
                description=row[3],
                deadline=row[4],
                budget=row[5],
                client_id=row[6],
                executor_id=row[7],
                status=row[8],
                created_at=row[9],
                completed_at=row[10],
                file_path=row[11],
                message_id=row[12]
            )
        return None
    
    def update_order(self, order_id: str, updates: dict) -> bool:
        cursor = self.conn.cursor()
        set_clause = ", ".join(f"{key} = ?" for key in updates.keys())
        values = list(updates.values())
        values.append(order_id)
        cursor.execute(
            f"UPDATE orders SET {set_clause} WHERE order_id = ?",
            values
        )
        self.conn.commit()
        return cursor.rowcount > 0
    
    def get_user_orders(self, user_id: int, status: Optional[str] = None) -> List[Order]:
        cursor = self.conn.cursor()
        query = "SELECT * FROM orders WHERE client_id = ?"
        params = [user_id]
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        cursor.execute(query, params)
        return [
            Order(
                order_id=row[0],
                type=row[1],
                subject=row[2],
                description=row[3],
                deadline=row[4],
                budget=row[5],
                client_id=row[6],
                executor_id=row[7],
                status=row[8],
                created_at=row[9],
                completed_at=row[10],
                file_path=row[11],
                message_id=row[12]
            )
            for row in cursor.fetchall()
        ]
    
    def get_active_orders(self) -> List[Order]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM orders WHERE status = ?", (OrderStatus.ACTIVE.value,))
        return [
            Order(
                order_id=row[0],
                type=row[1],
                subject=row[2],
                description=row[3],
                deadline=row[4],
                budget=row[5],
                client_id=row[6],
                executor_id=row[7],
                status=row[8],
                created_at=row[9],
                completed_at=row[10],
                file_path=row[11],
                message_id=row[12]
            )
            for row in cursor.fetchall()
        ]
    
    def add_dispute(self, dispute: Dispute) -> str:
        cursor = self.conn.cursor()
        cursor.execute(
            """INSERT INTO disputes (
                dispute_id, order_id, opened_by, admin_id, reason, status, resolution
            ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                dispute.dispute_id, dispute.order_id, dispute.opened_by,
                dispute.admin_id, dispute.reason, dispute.status, dispute.resolution
            )
        )
        
        cursor.execute(
            "UPDATE orders SET status = ? WHERE order_id = ?",
            (OrderStatus.DISPUTE.value, dispute.order_id)
        )
        
        self.conn.commit()
        return dispute.dispute_id
    
    def get_dispute(self, dispute_id: str) -> Optional[Dispute]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM disputes WHERE dispute_id = ?", (dispute_id,))
        row = cursor.fetchone()
        if row:
            return Dispute(
                dispute_id=row[0],
                order_id=row[1],
                opened_by=row[2],
                admin_id=row[3],
                reason=row[4],
                status=row[5],
                resolution=row[6],
                created_at=row[7],
                resolved_at=row[8]
            )
        return None
    
    def update_dispute(self, dispute_id: str, updates: dict) -> bool:
        cursor = self.conn.cursor()
        set_clause = ", ".join(f"{key} = ?" for key in updates.keys())
        values = list(updates.values())
        values.append(dispute_id)
        cursor.execute(
            f"UPDATE disputes SET {set_clause} WHERE dispute_id = ?",
            values
        )
        self.conn.commit()
        return cursor.rowcount > 0
    
    def close(self):
        self.conn.close()