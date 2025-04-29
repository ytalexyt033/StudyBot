import sqlite3
import uuid
from typing import Dict, Any, List, Optional
from pathlib import Path
from models.enums import OrderStatus, UserRole, DisputeStatus

class Database:
    def __init__(self, db_path: Path):
        self.conn = sqlite3.connect(db_path)
        self.create_tables()
    
    def create_tables(self):
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
    
    def add_user(self, user_id: int, username: str, first_name: str, last_name: str):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO users (user_id, username, first_name, last_name) VALUES (?, ?, ?, ?)",
            (user_id, username, first_name, last_name)
        )
        self.conn.commit()
    
    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if row:
            columns = [column[0] for column in cursor.description]
            return dict(zip(columns, row))
        return None
    
    def set_user_role(self, user_id: int, role: str) -> bool:
        if role not in [r.value for r in UserRole]:
            return False
        
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE users SET role = ? WHERE user_id = ?",
            (role, user_id))
        self.conn.commit()
        return True
    
    def add_order(self, order_data: Dict[str, Any]) -> str:
        order_id = str(uuid.uuid4())
        cursor = self.conn.cursor()
        cursor.execute(
            """INSERT INTO orders (
                order_id, type, subject, description, deadline, budget,
                client_id, status, file_path, message_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                order_id, order_data['type'], order_data['subject'],
                order_data['description'], order_data['deadline'],
                order_data['budget'], order_data['client_id'],
                OrderStatus.ACTIVE.value, order_data.get('file_path'), None
            )
        )
        self.conn.commit()
        return order_id
    
    def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,))
        row = cursor.fetchone()
        if row:
            columns = [column[0] for column in cursor.description]
            return dict(zip(columns, row))
        return None
    
    def update_order(self, order_id: str, updates: Dict[str, Any]):
        cursor = self.conn.cursor()
        set_clause = ", ".join(f"{key} = ?" for key in updates.keys())
        values = list(updates.values())
        values.append(order_id)
        cursor.execute(
            f"UPDATE orders SET {set_clause} WHERE order_id = ?",
            values
        )
        self.conn.commit()
    
    def get_user_orders(self, user_id: int, status: Optional[str] = None) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        query = "SELECT * FROM orders WHERE client_id = ?"
        params = [user_id]
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        if rows:
            columns = [column[0] for column in cursor.description]
            return [dict(zip(columns, row)) for row in rows]
        return []
    
    def get_executor_orders(self, executor_id: int, status: Optional[str] = None) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        query = "SELECT * FROM orders WHERE executor_id = ?"
        params = [executor_id]
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        if rows:
            columns = [column[0] for column in cursor.description]
            return [dict(zip(columns, row)) for row in rows]
        return []
    
    def get_active_orders(self) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM orders WHERE status = ?", (OrderStatus.ACTIVE.value,))
        rows = cursor.fetchall()
        if rows:
            columns = [column[0] for column in cursor.description]
            return [dict(zip(columns, row)) for row in rows]
        return []
    
    def add_chat_message(self, order_id: str, user_id: int, message: str, is_file: bool = False, file_path: Optional[str] = None):
        cursor = self.conn.cursor()
        cursor.execute(
            """INSERT INTO chat_messages (
                order_id, user_id, message, is_file, file_path
            ) VALUES (?, ?, ?, ?, ?)""",
            (order_id, user_id, message, int(is_file), file_path)
        )
        self.conn.commit()
    
    def get_chat_messages(self, order_id: str) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT cm.*, u.username, u.first_name, u.last_name 
            FROM chat_messages cm
            JOIN users u ON cm.user_id = u.user_id
            WHERE cm.order_id = ?
            ORDER BY cm.created_at""",
            (order_id,)
        )
        rows = cursor.fetchall()
        if rows:
            columns = [column[0] for column in cursor.description]
            return [dict(zip(columns, row)) for row in rows]
        return []
    
    def add_dispute(self, order_id: str, opened_by: int, reason: str) -> str:
        dispute_id = str(uuid.uuid4())
        cursor = self.conn.cursor()
        cursor.execute(
            """INSERT INTO disputes (
                dispute_id, order_id, opened_by, reason, status
            ) VALUES (?, ?, ?, ?, ?)""",
            (dispute_id, order_id, opened_by, reason, DisputeStatus.OPENED.value)
        )
        
        cursor.execute(
            "UPDATE orders SET status = ? WHERE order_id = ?",
            (OrderStatus.DISPUTE.value, order_id)
        )
        
        self.conn.commit()
        return dispute_id
    
    def update_dispute(self, dispute_id: str, updates: Dict[str, Any]):
        cursor = self.conn.cursor()
        set_clause = ", ".join(f"{key} = ?" for key in updates.keys())
        values = list(updates.values())
        values.append(dispute_id)
        cursor.execute(
            f"UPDATE disputes SET {set_clause} WHERE dispute_id = ?",
            values
        )
        self.conn.commit()
    
    def get_dispute(self, dispute_id: str) -> Optional[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM disputes WHERE dispute_id = ?", (dispute_id,))
        row = cursor.fetchone()
        if row:
            columns = [column[0] for column in cursor.description]
            return dict(zip(columns, row))
        return None
    
    def get_order_dispute(self, order_id: str) -> Optional[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM disputes WHERE order_id = ?", (order_id,))
        row = cursor.fetchone()
        if row:
            columns = [column[0] for column in cursor.description]
            return dict(zip(columns, row))
        return None
    
    def add_rating(self, order_id: str, executor_id: int, customer_id: int, rating: int, comment: str):
        cursor = self.conn.cursor()
        cursor.execute(
            """INSERT INTO ratings (
                order_id, executor_id, customer_id, rating, comment
            ) VALUES (?, ?, ?, ?, ?)""",
            (order_id, executor_id, customer_id, rating, comment)
        )
        
        cursor.execute(
            """UPDATE users 
            SET rating = (
                SELECT AVG(rating) FROM ratings WHERE executor_id = ?
            ), 
            completed_orders = completed_orders + 1
            WHERE user_id = ?""",
            (executor_id, executor_id)
        )
        
        self.conn.commit()