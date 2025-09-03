import random
from database_manager import DatabaseManager

# Kết nối DB
db = DatabaseManager("bookstore.db")

# Dọn dữ liệu cũ
db.cursor.execute("DELETE FROM order_items")
db.cursor.execute("DELETE FROM orders")
db.cursor.execute("DELETE FROM books")
db.conn.commit()

# 20 quyển sách mẫu
titles = [
    "Python for Beginners", "Advanced Python", "Machine Learning 101", "Deep Learning Basics",
    "Artificial Intelligence", "Data Science with Python", "SQL Mastery", "Web Development with Flask",
    "Django for Professionals", "Effective Java", "C++ Primer", "Clean Code",
    "Refactoring", "Design Patterns", "Algorithms Unlocked", "Computer Networks",
    "Operating System Concepts", "Discrete Mathematics", "Linear Algebra", "Probability and Statistics"
]

for i, title in enumerate(titles, start=1):
    db.add_book(
        title=title,
        author=f"Author {i}",
        genre=random.choice(["Programming", "AI", "Math", "Software Engineering", "Data"]),
        description=f"Description for {title}",
        shelf_position=f"Shelf {random.randint(1, 5)}",
        buy_price=random.randint(50, 100),   # giá nhập
        sell_price=random.randint(120, 200), # giá bán
        stock=random.randint(10, 30),
    )
db.conn.commit()
print("✅ Inserted 20 sample books.")

# Lấy danh sách ID sách
books_df = db.get_books()
book_ids = books_df["id"].tolist()

# Tạo 5 đơn hàng
for _ in range(5):
    order_items = []
    for book_id in random.sample(book_ids, k=random.randint(2, 5)):
        qty = random.randint(1, 3)
        book = books_df[books_df["id"] == book_id].iloc[0]
        order_items.append({
            "book_id": int(book_id),
            "quantity": qty,
            "unit_price": int(book["sell_price"]),
            "total": int(book["sell_price"]) * qty
        })

    order = db.create_order(order_items)
    print(f"✅ Created order {order['order_id']} with {order['total_qty']} books, total {order['total_amount']}")

db.close()
