import logging
import os
from tkcalendar import DateEntry
import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox
from chatbot import chat_with_customer, chat_with_management
from datetime import datetime
from voice_utils import recognize_speech, speak_text, translate_text
from database_manager import DatabaseManager

logging.basicConfig(filename='app.log', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

pd.set_option('future.no_silent_downcasting', True)

class BookStoreAIManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Book Store AI Manager")
        self.root.geometry("800x700")
        self.customer_cart_tree = ttk.Treeview(root)

        # Khởi tạo database
        self.db = DatabaseManager()

        # Dữ liệu từ database
        self.inventory_df = self.db.get_books()
        self.revenue_df = self.db.get_revenue()

        # Biến cờ
        self.sound_enabled = True
        self.current_order = []

        # Tạo Notebook cho các tab
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True)

        self.setup_inventory_tab()
        self.optimization_history = []
        self.setup_profit_tab()
        self.setup_staff_tab()
        self.setup_customer_tab()
        self.setup_history_tab()

    def setup_inventory_tab(self):
        """Inventory Management Tab"""
        self.inventory_frame = tk.Frame(self.notebook, bg="#ecf0f1")
        self.notebook.add(self.inventory_frame, text="Inventory")

        # Header
        header_frame = tk.Frame(self.inventory_frame, bg="#2c3e50")
        header_frame.pack(fill="x")

        tk.Label(
            header_frame, text="📚 Inventory Management",
            font=("Arial", 14, "bold"),
            bg="#2c3e50", fg="white"
        ).pack(side="left", padx=15, pady=10)

        tk.Button(
            header_frame, text="🔄 Refresh",
            bg="#27ae60", fg="white",
            activebackground="#2ecc71",
            command=self.open_inventory_tab
        ).pack(side="right", padx=10, pady=5)

        # Toolbar
        toolbar = tk.Frame(self.inventory_frame, bg="#ecf0f1")
        toolbar.pack(fill="x", padx=10, pady=5)

        tk.Button(toolbar, text="➕ Add Book", command=self.open_import_stock_popup).pack(side="left", padx=5)
        tk.Button(toolbar, text="❌ Delete Book", command=self.delete_book).pack(side="left", padx=5)
        tk.Button(toolbar, text="📊 Optimize Stock", command=self.optimize_inventory).pack(side="left", padx=5)

        tk.Label(toolbar, text="Search Title:", bg="#ecf0f1").pack(side="left", padx=(20, 5))
        self.search_entry = tk.Entry(toolbar)
        self.search_entry.pack(side="left", padx=5)
        tk.Button(toolbar, text="🔍 Search", command=self.search_books).pack(side="left", padx=5)

        # Table
        table_frame = tk.Frame(self.inventory_frame)
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        columns = ('id', 'title', 'author', 'genre', 'description',
                   'shelf_position', 'buy_price', 'sell_price', 'stock')

        self.inventory_tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=20)

        headers = {
            'id': "ID",
            'title': "Title",
            'author': "Author",
            'genre': "Genre",
            'description': "Description",
            'shelf_position': "Shelf",
            'buy_price': "Buy Price",
            'sell_price': "Sell Price",
            'stock': "Stock"
        }

        for col in columns:
            self.inventory_tree.heading(col, text=headers[col])
            if col in ['title', 'description']:
                self.inventory_tree.column(col, width=200, anchor='center')
            else:
                self.inventory_tree.column(col, width=100, anchor='center')

        # Alternating row colors
        self.inventory_tree.tag_configure("oddrow", background="white")
        self.inventory_tree.tag_configure("evenrow", background="#f2f2f2")

        # Scrollbars
        y_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.inventory_tree.yview)
        x_scroll = ttk.Scrollbar(table_frame, orient="horizontal", command=self.inventory_tree.xview)
        self.inventory_tree.configure(yscroll=y_scroll.set, xscroll=x_scroll.set)

        y_scroll.pack(side="right", fill="y")
        x_scroll.pack(side="bottom", fill="x")
        self.inventory_tree.pack(fill="both", expand=True)

        # Load data
        self.open_inventory_tab()

    def search_books(self):
        keyword = self.search_entry.get().lower()
        for row in self.inventory_tree.get_children():
            self.inventory_tree.delete(row)

        books = self.db.get_books()
        filtered = books[books["title"].str.lower().str.contains(keyword, na=False)]

        for _, row in filtered.iterrows():
            self.inventory_tree.insert(
                "",
                "end",
                values=(
                    row["id"],
                    row["title"],
                    row["author"],
                    row["genre"],
                    row["stock"],
                    f"{row['buy_price']:,} VNĐ",
                    f"{row['sell_price']:,} VNĐ"
                )
            )

    def open_inventory_tab(self):
        for row in self.inventory_tree.get_children():
            self.inventory_tree.delete(row)
        logging.debug(f"Before reload: inventory_df shape {self.inventory_df.shape}")
        self.inventory_df = self.db.get_books()
        logging.debug(f"After reload: inventory_df shape {self.inventory_df.shape}, sample: {self.inventory_df.head().to_dict()}")
        inventory = self.inventory_df
        if not inventory.empty:
            for _, row in inventory.iterrows():
                self.inventory_tree.insert('', 'end', values=(row['id'], row['title'], row['author'], row['genre'], row['description'], row['shelf_position'], row['buy_price'], row['sell_price'], row['stock']))
        else:
            self.inventory_tree.insert('', 'end', values=("", "Không có sách nào trong kho.", "", "", "", "", "", "", ""))
        logging.debug("Inventory tab refreshed.")
    try:
            from tkcalendar import DateEntry
    except ImportError:
        DateEntry = None

    def setup_profit_tab(self):
        """Profit Analyzer Tab"""
        self.profit_frame = tk.Frame(self.notebook, bg="#ecf0f1")
        self.notebook.add(self.profit_frame, text="Profit Analyzer")

        # ==== Header ====
        header_frame = tk.Frame(self.profit_frame, bg="#2c3e50")
        header_frame.pack(fill="x")

        self.profit_label = tk.Label(
            header_frame,
            text="💰 Profit Analysis",
            font=("Arial", 14, "bold"),
            bg="#2c3e50", fg="white"
        )
        self.profit_label.pack(side="left", padx=15, pady=10)

        filter_frame = tk.Frame(header_frame, bg="#2c3e50")
        filter_frame.pack(side="right", padx=10)

        tk.Label(filter_frame, text="From:", bg="#2c3e50", fg="white").pack(side="left", padx=2)
        if DateEntry:
            self.start_date = DateEntry(filter_frame, width=10, date_pattern="yyyy-mm-dd")
        else:
            self.start_date = tk.Entry(filter_frame, width=12)
        self.start_date.pack(side="left", padx=2)

        tk.Label(filter_frame, text="To:", bg="#2c3e50", fg="white").pack(side="left", padx=2)
        if DateEntry:
            self.end_date = DateEntry(filter_frame, width=10, date_pattern="yyyy-mm-dd")
        else:
            self.end_date = tk.Entry(filter_frame, width=12)
        self.end_date.pack(side="left", padx=2)

        tk.Button(
            filter_frame, text="Apply Filter",
            bg="#2980b9", fg="white",
            activebackground="#3498db",
            command=self.apply_profit_filter
        ).pack(side="left", padx=5)

        tk.Button(
            filter_frame, text="🔄 Refresh",
            bg="#27ae60", fg="white",
            activebackground="#2ecc71",
            command=self.open_profit_tab
        ).pack(side="left", padx=5)

        # Table
        table_frame = tk.Frame(self.profit_frame)
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        profit_columns = ("title", "quantity", "total_amount", "profit")
        self.profit_tree = ttk.Treeview(table_frame, columns=profit_columns, show="headings", height=15)

        headers = {
            "title": "Book Title",
            "quantity": "Quantity Sold",
            "total_amount": "Revenue (VNĐ)",
            "profit": "Profit (VNĐ)"
        }

        for col in profit_columns:
            self.profit_tree.heading(col, text=headers[col])
            if col == "title":
                self.profit_tree.column(col, width=200, anchor="center")
            else:
                self.profit_tree.column(col, width=120, anchor="center")

        self.profit_tree.tag_configure("oddrow", background="white")
        self.profit_tree.tag_configure("evenrow", background="#f2f2f2")

        # Scrollbars
        y_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.profit_tree.yview)
        x_scroll = ttk.Scrollbar(table_frame, orient="horizontal", command=self.profit_tree.xview)
        self.profit_tree.configure(yscroll=y_scroll.set, xscroll=x_scroll.set)

        y_scroll.pack(side="right", fill="y")
        x_scroll.pack(side="bottom", fill="x")
        self.profit_tree.pack(fill="both", expand=True)

        # Chart Area
        self.profit_chart_frame = tk.Frame(self.profit_frame, bg="#ecf0f1", height=400)
        self.profit_chart_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Load full data initially
        self.open_profit_tab()

    def apply_profit_filter(self):
        """Filter profit by date range"""
        start = self.start_date.get()
        end = self.end_date.get()

        try:
            start_dt = datetime.strptime(start, "%Y-%m-%d") if start else None
            end_dt = datetime.strptime(end, "%Y-%m-%d") if end else None
        except Exception:
            messagebox.showerror("Error", "Invalid date format. Use YYYY-MM-DD.")
            return

        self.open_profit_tab(start_dt, end_dt)

    def open_profit_tab(self, start_date=None, end_date=None):
        """Load profit data into table and chart (optionally filter by date)"""
        for row in self.profit_tree.get_children():
            self.profit_tree.delete(row)
        for widget in self.profit_chart_frame.winfo_children():
            widget.destroy()

        revenue_df = self.db.get_revenue()
        books = self.db.get_books()

        if revenue_df.empty:
            self.profit_label.config(text="💰 Profit Analysis | No revenue data available")
            self.profit_tree.insert("", "end", values=("No data", "", "", ""))
            return

        # Filter
        if start_date:
            revenue_df = revenue_df[revenue_df["timestamp"] >= start_date.strftime("%Y-%m-%d")]
        if end_date:
            revenue_df = revenue_df[revenue_df["timestamp"] <= end_date.strftime("%Y-%m-%d")]

        if revenue_df.empty:
            self.profit_label.config(text="💰 Profit Analysis | No data in this range")
            self.profit_tree.insert("", "end", values=("No data", "", "", ""))
            return

        # Aggregate
        aggregated = (
            revenue_df.groupby("book_id")
            .agg({"quantity": "sum", "total_amount": "sum", "profit": "sum"})
            .reset_index()
        )

        aggregated = aggregated.merge(
            books[["id", "title"]],
            left_on="book_id", right_on="id",
            how="left"
        ).drop(columns=["id"])

        total_revenue = aggregated["total_amount"].sum()
        total_profit = aggregated["profit"].sum()

        self.profit_label.config(
            text=f"💰 Profit Analysis | Total Revenue: {total_revenue:,.0f} VNĐ | Total Profit: {total_profit:,.0f} VNĐ"
        )

        for i, row in aggregated.iterrows():
            tag = "evenrow" if i % 2 == 0 else "oddrow"
            self.profit_tree.insert(
                "", "end",
                values=(row["title"], row["quantity"], f"{row['total_amount']:.0f}", f"{row['profit']:.0f}"),
                tags=(tag,)
            )

        # Chart
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

        fig = Figure(figsize=(10, 5), dpi=100)
        ax = fig.add_subplot(111)
        aggregated.plot(kind="bar", x="title", y="profit", ax=ax, color="#4ECDC4", legend=False)
        ax.set_title("Profit per Book", fontsize=12)
        ax.set_ylabel("Profit (VNĐ)")
        ax.tick_params(axis="x", labelsize=8, rotation=45)

        canvas = FigureCanvasTkAgg(fig, self.profit_chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def setup_staff_tab(self):
        self.staff_frame = tk.Frame(self.notebook, bg="#f4f6f9")
        self.notebook.add(self.staff_frame, text="Staff")

        # Tiêu đề
        tk.Label(self.staff_frame, text="Staff Management", font=("Arial", 14, "bold"),
                 bg="#f4f6f9", fg="#2c3e50").pack(pady=10)

        # Frame chia đôi
        main_frame = tk.Frame(self.staff_frame, bg="#f4f6f9")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Chatbot (Trái)
        chatbot_frame = tk.LabelFrame(main_frame, text="Management Chatbot", font=("Arial", 12, "bold"),
                                      bg="#f4f6f9", fg="#34495e", padx=10, pady=10)
        chatbot_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        self.staff_chat_text = tk.Text(chatbot_frame, height=25, wrap="word", state="normal",
                                       bg="#ffffff", fg="#2c3e50", font=("Arial", 10))
        self.staff_chat_text.pack(fill="both", expand=True, pady=5)

        input_frame = tk.Frame(chatbot_frame, bg="#f4f6f9")
        input_frame.pack(fill="x", pady=5)

        self.staff_chat_input = tk.Entry(input_frame, width=40)
        self.staff_chat_input.pack(side="left", fill="x", expand=True, padx=5)
        tk.Button(input_frame, text="Send", command=self.chat_with_management_ui,
                  bg="#3498db", fg="white").pack(side="right", padx=5)

        # Order Management (Phải)
        order_frame = tk.LabelFrame(main_frame, text="Create Order", font=("Arial", 12, "bold"),
                                    bg="#f4f6f9", fg="#34495e", padx=10, pady=10)
        order_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)

        # Form nhập
        form_frame = tk.Frame(order_frame, bg="#f4f6f9")
        form_frame.pack(anchor="w", pady=5, fill="x")

        tk.Label(form_frame, text="Book Title/ID:", bg="#f4f6f9").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.product_entry = tk.Entry(form_frame, width=25)
        self.product_entry.grid(row=0, column=1, padx=5, pady=2)

        tk.Label(form_frame, text="Quantity:", bg="#f4f6f9").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.quantity_entry = tk.Entry(form_frame, width=10)
        self.quantity_entry.grid(row=1, column=1, padx=5, pady=2, sticky="w")

        # Hàng chứa nút Add + Remove
        button_frame = tk.Frame(form_frame, bg="#f4f6f9")
        button_frame.grid(row=2, column=0, columnspan=2, pady=5)

        tk.Button(button_frame, text="➕ Add to Order", command=self.add_product_to_order,
                  bg="#27ae60", fg="white").pack(side=tk.LEFT, padx=5)

        tk.Button(button_frame, text="🗑️ Remove Item", command=self.remove_selected_item,
                  bg="red", fg="white").pack(side=tk.LEFT, padx=5)


        # Nút điều khiển giỏ hàng
        cart_button_frame = tk.Frame(order_frame, bg="#f4f6f9")
        cart_button_frame.pack(anchor="w", pady=5)

        # Table giỏ hàng
        self.order_tree_staff = ttk.Treeview(order_frame,
                                             columns=("title", "qty", "unit_price", "total"),
                                             show="headings")
        self.order_tree_staff.heading("title", text="Book Title")
        self.order_tree_staff.heading("qty", text="Quantity")
        self.order_tree_staff.heading("unit_price", text="Unit Price")
        self.order_tree_staff.heading("total", text="Total")

        self.order_tree_staff.pack(pady=5, fill="both", expand=True)

        # Tổng tiền + Thanh toán
        self.total_order_label_staff = tk.Label(order_frame, text="Total: 0 VND",
                                                font=("Arial", 10, "bold"), bg="#f4f6f9")
        self.total_order_label_staff.pack(anchor="e", pady=5)

        tk.Button(order_frame, text="Complete Payment", bg="#e67e22", fg="white",
                  command=self.complete_payment).pack(anchor="e", pady=5)

        # Khởi tạo giỏ hàng rỗng
        self.current_order = []

    def add_product_to_order(self):
        title_or_id = self.product_entry.get().strip()
        if not title_or_id:
            messagebox.showwarning("Warning", "Please enter book ID or Title.")
            return
        try:
            qty = int(self.quantity_entry.get().strip() or 1)
        except ValueError:
            messagebox.showerror("Error", "Quantity must be a number.")
            return
        if qty <= 0:
            messagebox.showerror("Error", "Quantity must be greater than 0.")
            return

        import sqlite3, os
        db_path = os.path.join(os.path.dirname(__file__), "bookstore.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Tìm sách theo ID hoặc Title
        if title_or_id.isdigit():
            cursor.execute(
                "SELECT id, title, buy_price, sell_price, stock FROM books WHERE id = ?",
                (title_or_id,),
            )
        else:
            cursor.execute(
                "SELECT id, title, buy_price, sell_price, stock FROM books WHERE LOWER(title) = LOWER(?)",
                (title_or_id,),
            )

        book = cursor.fetchone()
        conn.close()

        if not book:
            messagebox.showerror("Error", "Book not found in inventory.")
            return

        book_id, title, buy_price, sell_price, stock = book

        # Số lượng đã có sẵn trong giỏ với cùng book_id
        reserved = sum(it["quantity"] for it in self.current_order if it["book_id"] == book_id)
        available = (stock or 0) - reserved

        # Kiểm tra tồn kho
        if available <= 0:
            messagebox.showwarning("Insufficient Stock", f"'{title}' is out of stock.")
            return

        if qty > available:
            messagebox.showwarning(
                "Insufficient Stock",
                f"Only {available} copies of '{title}' left (in stock minus items already in the cart)."
            )
            return

        total = sell_price * qty

        # Lưu vào giỏ hàng tạm
        self.current_order.append({
            "book_id": book_id,
            "title": title,
            "quantity": qty,
            "unit_price": sell_price,
            "total": total
        })

        # Hiển thị lên bảng Staff
        self.order_tree_staff.insert("", "end", values=(title, qty, sell_price, total))

        # Cập nhật tổng tiền
        total_amount = sum(item["total"] for item in self.current_order)
        self.total_order_label_staff.config(text=f"Total: {total_amount:,} VND")

        # Đồng bộ giỏ hàng bên Customer
        self.sync_customer_cart()

    def update_cart_tree_staff(self):
        # Xoá toàn bộ dữ liệu cũ trong Treeview staff
        for item in self.order_tree_staff.get_children():
            self.order_tree_staff.delete(item)

        total_amount = 0
        for book in self.current_order:
            qty = book["quantity"]
            price = book["unit_price"]
            total = qty * price
            total_amount += total

            self.order_tree_staff.insert("", "end", values=(
                book["title"], qty, f"{price:,}", f"{total:,}"
            ))

        # Cập nhật label tổng
        self.total_order_label_staff.config(text=f"Total: {total_amount:,} VND")

    def remove_selected_item(self):
        selected = self.order_tree_staff.selection()
        if not selected:
            messagebox.showwarning("No selection", "⚠️ Vui lòng chọn một sản phẩm để xoá.")
            return

        values = self.order_tree_staff.item(selected, "values")
        title_to_remove = values[0]

        # Xoá khỏi current_order
        self.current_order = [book for book in self.current_order if book["title"] != title_to_remove]

        # Cập nhật lại giỏ hàng staff
        self.update_cart_tree_staff()

        # Đồng bộ sang Customer tab
        self.sync_customer_cart()

    def update_order_total(self):
        total = sum(item["total"] for item in self.current_order)
        self.total_order_label_staff.config(text=f"Total: {total} VND")

    def complete_payment(self):
        if not self.current_order:
            messagebox.showwarning("Empty", "No items in the order.")
            return

        try:
            # Ghi order vào database qua DatabaseManager
            result = self.db.create_order(self.current_order)

            # Reset giỏ hàng Staff
            self.current_order.clear()
            self.order_tree_staff.delete(*self.order_tree_staff.get_children())
            self.total_order_label_staff.config(text="Total: 0 VND")

            # Reset giỏ hàng Customer
            self.customer_cart_tree.delete(*self.customer_cart_tree.get_children())
            self.customer_total_label.config(text="Total: 0 VND")

            # Thông báo
            messagebox.showinfo(
                "Success",
                f"Order {result['order_id']} completed!\n"
                f"Total books: {result['total_qty']}, Amount: {result['total_amount']:,} VND"
            )

        except Exception as e:
            messagebox.showerror("Error", f"Failed to complete order:\n{e}")

    def sync_customer_cart(self):
        # Xóa dữ liệu cũ
        for item in self.customer_cart_tree.get_children():
            self.customer_cart_tree.delete(item)

        total_qty, total_amount = 0, 0

        for book in self.current_order:
            title = book["title"]
            qty = book["quantity"]
            price = book["unit_price"]
            total = qty * price

            total_qty += qty
            total_amount += total

            self.customer_cart_tree.insert("", "end",
                                           values=(title, qty, f"{price:,}", f"{total:,}"))

        # Update tổng
        self.customer_total_label.config(
            text=f"Total books: {total_qty} | Total amount: {total_amount:,} VND"
        )

    def chat_with_management_ui(self):
        question = self.staff_chat_input.get()
        self.staff_chat_input.delete(0, tk.END)
        self.staff_chat_text.insert(tk.END, f"You: {question}\n")

        context = self.get_inventory_context()
        reply = chat_with_management(question, context)

        self.staff_chat_text.insert(tk.END, f"Manager: {reply}\n")
        self.staff_chat_text.see(tk.END)

    def setup_customer_tab(self):
        self.customer_frame = tk.Frame(self.notebook, bg="#f9f9f9")
        self.notebook.add(self.customer_frame, text="Customer")

        # Layout chia đôi: Giỏ hàng bên trái, Chatbot bên phải
        left_frame = tk.Frame(self.customer_frame, bg="#f9f9f9", bd=2, relief="groove")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        right_frame = tk.Frame(self.customer_frame, bg="#f9f9f9", bd=2, relief="groove")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 🛒 CART VIEW
        tk.Label(left_frame, text="🛍️ Your Cart", font=("Arial", 14, "bold"), bg="#f9f9f9").pack(pady=5)

        cart_frame = tk.Frame(left_frame, bg="#f9f9f9")
        cart_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("Title", "Quantity", "Price (VND)", "Total (VND)")
        self.customer_cart_tree = ttk.Treeview(cart_frame, columns=columns, show="headings", height=15)
        for col in columns:
            self.customer_cart_tree.heading(col, text=col)
            self.customer_cart_tree.column(col, width=130, anchor="center")

        self.customer_cart_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        scrollbar = ttk.Scrollbar(cart_frame, orient="vertical", command=self.customer_cart_tree.yview)
        self.customer_cart_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Total
        self.customer_total_label = tk.Label(
            left_frame,
            text="Total books: 0 | Total amount: 0 VND",
            font=("Arial", 12, "bold"),
            bg="#f9f9f9",
            fg="darkred"
        )
        self.customer_total_label.pack(side=tk.BOTTOM, pady=10)

        # CUSTOMER CHATBOT
        tk.Label(right_frame, text="🤖 Ask Assistant", font=("Arial", 13, "bold"), bg="#f9f9f9").pack(pady=5)

        self.customer_chat_text = tk.Text(right_frame, height=25, width=55,
                                          state=tk.DISABLED, wrap=tk.WORD, bg="white")
        self.customer_chat_text.pack(pady=5, padx=5, fill=tk.BOTH, expand=True)

        chat_entry_frame = tk.Frame(right_frame, bg="#f9f9f9")
        chat_entry_frame.pack(fill=tk.X, pady=5)

        self.customer_chat_entry = tk.Entry(chat_entry_frame, width=40)
        self.customer_chat_entry.pack(side=tk.LEFT, padx=5, pady=5)

        tk.Button(chat_entry_frame, text="Send", command=self.send_customer_message).pack(side=tk.LEFT, padx=5)
        tk.Button(chat_entry_frame, text="🎤 Voice", command=self.send_customer_voice).pack(side=tk.LEFT, padx=5)

    def customer_chatbot(self, user_msg, target_lang="en"):
        """
        Chatbot cho khách hàng:
        - Dịch câu hỏi sang tiếng Anh (cho AI dễ hiểu hơn).
        - Kiểm tra database: nếu có sách thì trả thông tin từ DB.
        - Nếu không thì gọi AI trả lời.
        - Cuối cùng dịch lại sang ngôn ngữ của khách (target_lang).
        """
        # 1. Dịch sang tiếng Anh cho AI dễ hiểu
        question_en = translate_text(user_msg, src="auto", dest="en")

        # 2. Kiểm tra DB xem có sách nào khớp không
        books_df = self.db.get_books()
        found = books_df[books_df["title"].str.lower() == user_msg.lower()]

        if not found.empty:
            book = found.iloc[0]
            reply = (
                f"📚 {book['title']}\n"
                f"✍️ Author: {book['author']}\n"
                f"📖 Genre: {book['genre']}\n"
                f"📝 Description: {book['description']}\n"
                f"📌 Shelf Position: {book['shelf_position']}\n"
                f"💰 Price: {book['sell_price']} VND\n"
                f"📦 Stock: {book['stock']}"
            )
        else:
            # 3. Nếu không tìm thấy sách -> hỏi AI
            reply_en = chat_with_customer(question_en)
            # 4. Dịch lại sang target_lang
            reply = translate_text(reply_en, src="en", dest=target_lang)

        return reply

    def send_customer_message(self):
        user_msg = self.customer_chat_entry.get()
        if not user_msg:
            return
        self.customer_chat_entry.delete(0, tk.END)

        self.customer_chat_text.config(state=tk.NORMAL)
        self.customer_chat_text.insert(tk.END, f"You: {user_msg}\n")

        reply = self.customer_chatbot(user_msg, target_lang="en")

        self.customer_chat_text.insert(tk.END, f"Assistant: {reply}\n\n")
        self.customer_chat_text.config(state=tk.DISABLED)
        self.customer_chat_text.see(tk.END)

        if self.sound_enabled:
            speak_text(reply, lang="en")

    def send_customer_voice(self):
        question = recognize_speech()
        if not question.strip():
            self.customer_chat_text.insert(tk.END, "🤖: Sorry, i can't hear you. Can you please try again ?\n")
            self.customer_chat_text.see(tk.END)
            return

        self.customer_chat_text.insert(tk.END, f"You: {question}\n")
        reply = chat_with_customer(question)
        self.customer_chat_text.insert(tk.END, f"🤖: {reply}\n")
        self.customer_chat_text.see(tk.END)
        if self.sound_enabled:
            speak_text(reply, lang='en')

    def refresh_customer_tab(self):
        self.customer_chat_text.delete(1.0, tk.END)
        self.customer_chat_input.delete(0, tk.END)
        for row in self.order_tree.get_children():
            self.order_tree.delete(row)
        self.total_order_label.config(text="Tổng tiền: 0 VNĐ")
        logging.debug("Customer tab refreshed.")

    def toggle_sound(self):
        self.sound_enabled = not self.sound_enabled
        self.toggle_sound_button.config(text="Tắt tiếng" if not self.sound_enabled else "Bật tiếng")

    def get_inventory_context(self):
        context = "Danh sách sách trong kho:\n"
        inventory = self.db.get_books()
        for _, book in inventory.iterrows():
            context += f"- {book['title']} (Thể loại: {book['genre']}, Vị trí: {book['shelf_position']}, Giá: {book['sell_price']} VNĐ, Tồn kho: {book['stock']} bản)\n"
        revenue = self.db.get_revenue()
        if not revenue.empty:
            context += "Doanh số bán hàng:\n"
            for _, sale in revenue.iterrows():
                book = self.db.get_books()[self.db.get_books()['id'] == sale['book_id']].iloc[0]
                context += f"- {book['title']}: Đã bán {sale['quantity']} bản, Tổng doanh thu: {sale['total_amount']} VNĐ, Lợi nhuận: {sale['profit']} VNĐ\n"
        return context

    def open_import_stock_popup(self):
        popup = tk.Toplevel(self.root)
        popup.title("Add New Book to Stock")
        popup.geometry("400x500")

        # Input fields
        tk.Label(popup, text="Title:").pack()
        title_entry = tk.Entry(popup)
        title_entry.pack()

        tk.Label(popup, text="Author:").pack()
        author_entry = tk.Entry(popup)
        author_entry.pack()

        tk.Label(popup, text="Genre:").pack()
        genre_entry = tk.Entry(popup)
        genre_entry.pack()

        tk.Label(popup, text="Description:").pack()
        desc_entry = tk.Entry(popup)
        desc_entry.pack()

        tk.Label(popup, text="Purchase Price (VND):").pack()
        buy_price_entry = tk.Entry(popup)
        buy_price_entry.pack()

        tk.Label(popup, text="Selling Price (VND):").pack()
        sell_price_entry = tk.Entry(popup)
        sell_price_entry.pack()

        tk.Label(popup, text="Quantity:").pack()
        quantity_entry = tk.Entry(popup)
        quantity_entry.pack()

        tk.Label(popup, text="Shelf Position:").pack()
        shelf_entry = tk.Entry(popup)
        shelf_entry.pack()

        # Save & Cancel buttons
        def save_book():
            try:
                self.db.add_book(
                    title_entry.get(),
                    author_entry.get(),
                    genre_entry.get(),
                    desc_entry.get(),
                    shelf_entry.get(),
                    int(buy_price_entry.get()),
                    int(sell_price_entry.get()),
                    int(quantity_entry.get())
                )
                messagebox.showinfo("Success", "Book added successfully!")
                popup.destroy()
                self.open_inventory_tab()  # refresh inventory
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add book: {e}")

        btn_frame = tk.Frame(popup)
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="✅ Save", command=save_book, bg="#27ae60", fg="white").pack(side="left", padx=5)
        tk.Button(btn_frame, text="❌ Cancel", command=popup.destroy, bg="#e74c3c", fg="white").pack(side="left", padx=5)

    def add_product_to_order(self):
        title_or_id = self.product_entry.get().strip()
        if not title_or_id:
            messagebox.showwarning("Warning", "Please enter book ID or Title.")
            return

        # Get quantity, must be a positive integer
        try:
            qty = int(self.quantity_entry.get().strip() or 1)
        except ValueError:
            messagebox.showerror("Error", "Quantity must be a number.")
            return
        if qty <= 0:
            messagebox.showerror("Error", "Quantity must be greater than 0.")
            return

        import sqlite3, os
        db_path = os.path.join(os.path.dirname(__file__), "bookstore.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Find book by ID or Title (case-insensitive)
        if title_or_id.isdigit():
            cursor.execute(
                "SELECT id, title, buy_price, sell_price, stock FROM books WHERE id = ?",
                (title_or_id,),
            )
        else:
            cursor.execute(
                "SELECT id, title, buy_price, sell_price, stock FROM books WHERE LOWER(title) = LOWER(?)",
                (title_or_id,),
            )

        book = cursor.fetchone()
        conn.close()

        if not book:
            messagebox.showerror("Error", "Book not found in inventory.")
            return

        book_id, title, buy_price, sell_price, stock = book

        # Check reserved quantity already in the cart for this book_id
        reserved = sum(it["quantity"] for it in self.current_order if it["book_id"] == book_id)
        available = (stock or 0) - reserved

        # Validate stock
        if available <= 0:
            messagebox.showwarning("Out of Stock", f"'{title}' is out of stock.")
            return

        if qty > available:
            messagebox.showwarning(
                "Insufficient Stock",
                f"Only {available} copies of '{title}' left (after considering items already in the cart)."
            )
            return

        total = sell_price * qty

        # Add to temporary cart
        self.current_order.append({
            "book_id": book_id,
            "title": title,
            "quantity": qty,
            "unit_price": sell_price,
            "total": total
        })

        # Show in Staff order table
        self.order_tree_staff.insert("", "end", values=(title, qty, sell_price, total))

        # Update total amount
        total_amount = sum(item["total"] for item in self.current_order)
        self.total_order_label_staff.config(text=f"Total: {total_amount:,} VND")

        # Sync cart with Customer tab
        self.sync_customer_cart()

    def delete_book(self):
        selected = self.inventory_tree.selection()
        if selected:
            item = self.inventory_tree.item(selected)
            book_id = item['values'][0]
            self.db.delete_book(book_id)
            self.inventory_df = self.db.get_books()
            self.open_inventory_tab()
            messagebox.showinfo("Success", "The book has been deleted..")
        else:
            messagebox.showerror("Error", "Please select a book.")

    def optimize_inventory(self):
        self.revenue_df = self.db.get_revenue()
        result = "📊 Inventory Optimization Suggestions:\n\n"
        inventory = self.db.get_books()

        unsold_books = []  # list of books that have not been sold

        if not self.revenue_df.empty:
            # Calculate sales per book
            sales = self.revenue_df.groupby("book_id").agg(
                {"quantity": "sum", "total_amount": "sum", "profit": "sum"}
            ).reset_index()
            sales = sales.merge(inventory, left_on="book_id", right_on="id", how="right")

            for _, row in sales.iterrows():
                title = row["title"]
                sold = row["quantity"] if pd.notna(row["quantity"]) else 0
                stock = row["stock"]
                buy_price = row["buy_price"]
                sell_price = row["sell_price"]

                # Profit margin %
                margin = (sell_price - buy_price) / sell_price * 100 if sell_price > 0 else 0

                # Assume sales data for the last 30 days
                daily_sales = sold / 30 if sold > 0 else 0
                days_to_sell = stock / daily_sales if daily_sales > 0 else float("inf")

                if sold == 0:
                    unsold_books.append(title)
                    result += f"❌ {title}: No sales → suggest discount to {int(sell_price*0.7)} VND or stop importing.\n"
                    continue

                if days_to_sell > 90:
                    new_price = int(sell_price * 0.85)
                    result += f"⚠️ {title}: Slow selling (stock lasts {days_to_sell:.0f} days) → reduce price to {new_price} VND.\n"

                elif 30 <= days_to_sell <= 90:
                    result += f"ℹ️ {title}: Average selling (stock lasts {days_to_sell:.0f} days) → keep current price {sell_price} VND.\n"

                elif days_to_sell < 30:
                    suggest_import = int(daily_sales * 60)  # import for ~2 months demand
                    total_cost = suggest_import * buy_price
                    result += f"🔥 {title}: Fast selling (may run out in {days_to_sell:.0f} days) → suggest importing {suggest_import} copies (~{total_cost} VND cost).\n"

                # Profit margin comments
                if margin < 10:
                    result += f"   💡 Low profit margin ({margin:.1f}%) → consider raising price or discontinuing.\n"
                elif margin > 40:
                    result += f"   💰 High profit margin ({margin:.1f}%) → should promote more.\n"

        else:
            result += "No sales data available for optimization."

        # List unsold books
        if unsold_books:
            result += "\n📕 Unsold books list:\n"
            for t in unsold_books:
                result += f" - {t}\n"

        # Show popup
        self.optimization_history.append(result)
        popup = tk.Toplevel(self.root)
        popup.title("Inventory Optimization Suggestions")
        popup.geometry("600x400")
        tk.Label(popup, text=result, justify="left", anchor="w", font=("Arial", 10)).pack(
            pady=10, fill="both", expand=True
        )

    def setup_history_tab(self):
        self.history_frame = tk.Frame(self.notebook, bg="#f4f6f9")
        self.notebook.add(self.history_frame, text="History")

        # Thanh tìm kiếm
        search_frame = tk.Frame(self.history_frame, bg="#f4f6f9")
        search_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(search_frame, text="Search:", bg="#f4f6f9").pack(side="left")
        self.history_search_entry = tk.Entry(search_frame, width=30)
        self.history_search_entry.pack(side="left", padx=5)

        tk.Button(search_frame, text="🔍 Search", command=self.search_history,
                  bg="#3498db", fg="white").pack(side="left", padx=5)

        tk.Button(search_frame, text="⟳ Refresh", command=self.load_order_history,
                  bg="#27ae60", fg="white").pack(side="left", padx=5)

        tk.Button(search_frame, text="📤 Export", command=self.export_history,
                  bg="#e67e22", fg="white").pack(side="left", padx=5)

        # Bảng danh sách đơn hàng
        columns = ("Order ID", "Total Qty", "Total Amount", "Date")
        self.history_tree = ttk.Treeview(self.history_frame, columns=columns, show="headings")
        for col in columns:
            self.history_tree.heading(col, text=col)
            self.history_tree.column(col, anchor="center")
        self.history_tree.pack(fill="both", expand=True, padx=10, pady=5)

        self.history_tree.bind("<<TreeviewSelect>>", self.show_order_details)

        # Bảng chi tiết đơn hàng
        detail_frame = tk.LabelFrame(self.history_frame, text="Order Details", bg="#f4f6f9")
        detail_frame.pack(fill="both", expand=True, padx=10, pady=5)

        detail_cols = ("title", "quantity", "unit_price", "total")
        self.history_detail_tree = ttk.Treeview(detail_frame, columns=detail_cols, show="headings", height=6)
        for col in detail_cols:
            self.history_detail_tree.heading(col, text=col.capitalize())
            self.history_detail_tree.column(col, anchor="center", width=120)
        self.history_detail_tree.pack(fill="both", expand=True, padx=5, pady=5)

    def load_order_history(self):
        import sqlite3, os
        db_path = os.path.join(os.path.dirname(__file__), "bookstore.db")

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""
                       SELECT o.id AS order_id,
                              SUM(oi.quantity) AS total_qty,
                              SUM(oi.total) AS total_amount,
                              o.created_at
                       FROM orders o
                                JOIN order_items oi ON o.id = oi.order_id
                       GROUP BY o.id, o.created_at
                       ORDER BY o.created_at DESC
                       """)
        rows = cursor.fetchall()
        conn.close()

        # Clear bảng cũ
        for r in self.history_tree.get_children():
            self.history_tree.delete(r)

        if not rows:
            self.history_tree.insert("", "end", values=("Không có đơn hàng", "", "", ""))
            return

        for order_id, qty, amount, date in rows:
            self.history_tree.insert(
                "",
                "end",
                values=(order_id, qty, f"{(amount or 0):,} VND", date)
            )

    def show_order_details(self, event=None):
        sel = self.history_tree.selection()
        if not sel:
            return
        order_id = self.history_tree.item(sel[0])["values"][0]

        import sqlite3, os
        db_path = os.path.join(os.path.dirname(__file__), "bookstore.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""
                       SELECT b.title,
                              oi.quantity,
                              CASE WHEN oi.unit_price IS NULL OR oi.unit_price = 0
                                       THEN b.sell_price ELSE oi.unit_price END as unit_price,
                              (oi.quantity * CASE WHEN oi.unit_price IS NULL OR oi.unit_price = 0
                                                      THEN b.sell_price ELSE oi.unit_price END) as total
                       FROM order_items oi
                                JOIN books b ON oi.book_id = b.id
                       WHERE oi.order_id = ?
                       """, (order_id,))
        rows = cursor.fetchall()
        conn.close()

        for r in self.history_detail_tree.get_children():
            self.history_detail_tree.delete(r)

        if not rows:
            self.history_detail_tree.insert("", "end", values=("Không có chi tiết", "", "", ""))
            return

        for title, qty, unit_price, total in rows:
            self.history_detail_tree.insert(
                "",
                "end",
                values=(title, qty, unit_price, total)
            )


        for r in self.history_detail_tree.get_children():
            self.history_detail_tree.delete(r)

        if not rows:
            self.history_detail_tree.insert("", "end", values=("Không có chi tiết", "", "", ""))
            return

        for title, qty, unit_price, total in rows:
            self.history_detail_tree.insert(
                "",
                "end",
                values=(title, qty, unit_price, total)
            )

    def search_history(self):
        keyword = self.history_search_entry.get().strip()
        if not keyword:
            self.load_order_history()
            return

        import sqlite3, os
        db_path = os.path.join(os.path.dirname(__file__), "bookstore.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""
                       SELECT o.id AS order_id,
                              SUM(oi.quantity) AS total_qty,
                              SUM(oi.total) AS total_amount,
                              o.created_at
                       FROM orders o
                                JOIN order_items oi ON o.id = oi.order_id
                       WHERE o.id LIKE ? OR o.created_at LIKE ?
                       GROUP BY o.id, o.created_at
                       ORDER BY o.created_at DESC
                       """, (f"%{keyword}%", f"%{keyword}%"))
        rows = cursor.fetchall()
        conn.close()

        # Xóa dữ liệu cũ
        for r in self.history_tree.get_children():
            self.history_tree.delete(r)

        if not rows:
            self.history_tree.insert("", "end", values=("Không tìm thấy đơn hàng", "", "", ""))
            return

        for order_id, qty, amount, date in rows:
            self.history_tree.insert(
                "",
                "end",
                values=(order_id, qty, f"{(amount or 0):,} VND", date)
            )

    def export_history(self):
        import sqlite3, os, pandas as pd
        from tkinter import filedialog, messagebox

        db_path = os.path.join(os.path.dirname(__file__), "bookstore.db")
        conn = sqlite3.connect(db_path)

        query = """
                SELECT o.id AS order_id,
                       SUM(oi.quantity) AS total_qty,
                       SUM(oi.total) AS total_amount,
                       o.created_at
                FROM orders o
                         JOIN order_items oi ON o.id = oi.order_id
                GROUP BY o.id, o.created_at
                ORDER BY o.created_at DESC \
                """
        df = pd.read_sql(query, conn)
        conn.close()

        if df.empty:
            messagebox.showinfo("Export", "No data to export.")
            return

        # Chọn nơi lưu file
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
        )
        if not file_path:
            return

        # Xuất ra Excel
        df.to_excel(file_path, index=False)
        messagebox.showinfo("Export", f"Data export successful!\n{file_path}")

if __name__ == "__main__":
    root = tk.Tk()
    app = BookStoreAIManager(root)
    root.mainloop()