import sqlite3
import pandas as pd
from datetime import datetime
import uuid


class DatabaseManager:
    def __init__(self, db_name="bookstore.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        """Tạo các bảng cần thiết"""
        self.cursor.execute("""
                            CREATE TABLE IF NOT EXISTS books (
                                                                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                                 title TEXT,
                                                                 author TEXT,
                                                                 genre TEXT,
                                                                 description TEXT,
                                                                 shelf_position TEXT,
                                                                 buy_price INTEGER,
                                                                 sell_price INTEGER,
                                                                 stock INTEGER
                            )
                            """)

        self.cursor.execute("""
                            CREATE TABLE IF NOT EXISTS orders (
                                                                  id TEXT PRIMARY KEY,
                                                                  total_qty INTEGER,
                                                                  total_amount INTEGER,
                                                                  created_at TEXT
                            )
                            """)

        self.cursor.execute("""
                            CREATE TABLE IF NOT EXISTS order_items (
                                                                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                                    order_id TEXT,
                                                                    book_id INTEGER,
                                                                    quantity INTEGER,
                                                                    unit_price INTEGER,
                                                                    total INTEGER,
                                                                    FOREIGN KEY(order_id) REFERENCES orders(id) ON DELETE CASCADE,
                                                                    FOREIGN KEY(book_id) REFERENCES books(id) ON DELETE CASCADE
                                )
                            """)

        self.conn.commit()

    #Books

    def add_book(self, title, author, genre, description, shelf_position, buy_price, sell_price, stock):
        self.conn.execute(
            "INSERT INTO books (title, author, genre, description, shelf_position, buy_price, sell_price, stock) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (title, author, genre, description, shelf_position, buy_price, sell_price, stock)
        )
        self.conn.commit()

    def delete_book(self, book_id):
        self.conn.execute("DELETE FROM books WHERE id = ?", (book_id,))
        self.conn.commit()

    def get_books(self):
        df = pd.read_sql_query("SELECT * FROM books", self.conn)
        return df

    def find_book_by_title(self, title):
        query = """
                    SELECT title, author, description, shelf_position, sell_price, stock
                    FROM books
                    WHERE LOWER(title) = LOWER(?) \
                    """
        row = self.conn.execute(query, (title,)).fetchone()
        return row

    #Orders
    def create_order(self, items):
        """Tạo 1 order mới cùng order_items"""
        order_id = str(uuid.uuid4())[:8]
        total_qty = sum(it["quantity"] for it in items)
        total_amount = sum(it["total"] for it in items)

        with self.conn:
            self.conn.execute(
                "INSERT INTO orders (id, total_qty, total_amount, created_at) VALUES (?, ?, ?, ?)",
                (order_id, total_qty, total_amount, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            )

            for it in items:
                # Kiểm tra book_id tồn tại
                book = self.conn.execute("SELECT id FROM books WHERE id = ?", (it["book_id"],)).fetchone()
                if not book:
                    raise ValueError(f"Book ID {it['book_id']} not found in books table")

                self.conn.execute(
                    "INSERT INTO order_items (order_id, book_id, quantity, unit_price, total) VALUES (?, ?, ?, ?, ?)",
                    (order_id, it["book_id"], it["quantity"], it["unit_price"], it["total"]),
                )

                # Giảm tồn kho
                self.conn.execute(
                    "UPDATE books SET stock = stock - ? WHERE id = ?",
                    (it["quantity"], it["book_id"]),
                )

        return {"order_id": order_id, "total_qty": total_qty, "total_amount": total_amount}

    def get_orders(self):
        df = pd.read_sql_query("SELECT * FROM orders", self.conn)
        return df

    def get_order_items(self, order_id):
        df = pd.read_sql_query(
            """
            SELECT oi.id, b.title, oi.quantity, oi.unit_price, oi.total
            FROM order_items oi
                     JOIN books b ON oi.book_id = b.id
            WHERE oi.order_id = ?
            """,
            self.conn,
            params=(order_id,),
        )
        return df

    #Reports
    def get_revenue(self, start_date=None, end_date=None):
        query = """
                SELECT b.id as book_id, b.title,
                       SUM(oi.quantity) as quantity,
                       SUM(oi.total) as total_amount,
                       SUM((b.sell_price - b.buy_price) * oi.quantity) as profit
                FROM order_items oi
                         JOIN books b ON oi.book_id = b.id
                         JOIN orders o ON oi.order_id = o.id
                WHERE 1=1 \
                """
        params = []
        if start_date:
            query += " AND o.created_at >= ?"
            params.append(start_date)
        if end_date:
            query += " AND o.created_at <= ?"
            params.append(end_date)

        query += " GROUP BY b.id, b.title"
        df = pd.read_sql_query(query, self.conn, params=params)
        return df

    def close(self):
        self.conn.close()