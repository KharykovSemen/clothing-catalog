from nicegui import ui
import sqlite3
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Product:
    id: Optional[int] = None
    name: str = ""
    price: float = 0.0
    category: str = ""
    size: str = ""
    quantity: int = 0
    image_color: str = ""  # цвет для фона


class SimpleDB:
    def __init__(self, db_file='catalog.db'):
        self.db_file = db_file
        self.init_db()
        self.add_sample_products()
    
    def init_db(self):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                category TEXT,
                size TEXT,
                quantity INTEGER DEFAULT 0,
                image_color TEXT
            )
        ''')
        conn.commit()
        conn.close()
    
    def add_sample_products(self):
        sample_products = [
            Product(name='Футболка мужская', price=1299, category='Мужская', size='M', quantity=25, image_color='#3498db'),
            Product(name='Джинсы мужские', price=3499, category='Мужская', size='L', quantity=15, image_color='#2980b9'),
            Product(name='Куртка мужская', price=8999, category='Мужская', size='XL', quantity=8, image_color='#2c3e50'),
            Product(name='Футболка женская', price=1299, category='Женская', size='S', quantity=20, image_color='#e74c3c'),
            Product(name='Джинсы женские', price=3499, category='Женская', size='M', quantity=12, image_color='#c0392b'),
            Product(name='Платье', price=2799, category='Женская', size='M', quantity=10, image_color='#e67e22'),
        ]
        
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM products")
        count = cursor.fetchone()[0]
        
        if count == 0:
            for product in sample_products:
                self.add_product(product)
        
        conn.close()
    
    def get_all_products(self) -> List[Product]:
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products")
        
        products = []
        for row in cursor.fetchall():
            p = Product()
            for key in row.keys():
                setattr(p, key, row[key])
            products.append(p)
        
        conn.close()
        return products
    
    def get_product(self, product_id: int) -> Optional[Product]:
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        row = cursor.fetchone()
        
        if row:
            p = Product()
            for key in row.keys():
                setattr(p, key, row[key])
            conn.close()
            return p
        
        conn.close()
        return None
    
    def add_product(self, product: Product) -> int:
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO products (name, price, category, size, quantity, image_color)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (product.name, product.price, product.category, product.size, product.quantity, product.image_color))
        
        product_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return product_id
    
    def update_product(self, product: Product) -> bool:
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE products SET
                name = ?, price = ?, category = ?,
                size = ?, quantity = ?, image_color = ?
            WHERE id = ?
        ''', (product.name, product.price, product.category, product.size, product.quantity, product.image_color, product.id))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success
    
    def search_products(self, search_text: str = "") -> List[Product]:
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if search_text:
            cursor.execute("SELECT * FROM products WHERE name LIKE ?", (f"%{search_text}%",))
        else:
            cursor.execute("SELECT * FROM products")
        
        products = []
        for row in cursor.fetchall():
            p = Product()
            for key in row.keys():
                setattr(p, key, row[key])
            products.append(p)
        
        conn.close()
        return products


class SimpleCatalog:
    def __init__(self):
        self.db = SimpleDB()
        self.editing_id = None
        self.create_ui()
    
    def create_ui(self):
        with ui.header().style('background-color: #2196F3'):
            ui.label('Каталог одежды').style('font-size: 1.5rem; font-weight: bold')
            with ui.row():
                ui.button('Каталог', on_click=self.show_catalog, icon='storefront')
                ui.button('Добавить', on_click=self.show_add_form, icon='add')
        
        self.content = ui.column().classes('w-full p-4')
        self.show_catalog()
    
    def clear_content(self):
        self.content.clear()
    
    def show_catalog(self):
        self.clear_content()
        self.editing_id = None
        
        with self.content:
            ui.label('Каталог товаров').style('font-size: 1.5rem; font-weight: bold')
            
            self.search_input = ui.input(placeholder='Поиск по названию...', 
                                         on_change=self.update_products).props('outlined').classes('w-64')
            
            self.products_container = ui.column().classes('w-full mt-4')
            self.update_products()
    
    def update_products(self):
        if not hasattr(self, 'products_container'):
            return
        
        self.products_container.clear()
        search = self.search_input.value if hasattr(self, 'search_input') else ''
        products = self.db.search_products(search)
        
        with self.products_container:
            if not products:
                ui.label('Товары не найдены').classes('text-center text-gray-500 p-8')
            else:
                with ui.grid(columns=3).classes('w-full gap-4'):
                    for product in products:
                        self.create_product_card(product)
    
    def create_product_card(self, product: Product):
        with ui.card().classes('w-full'):
            # Фото товара (цветной прямоугольник)
            with ui.column().classes('w-full h-48 items-center justify-center rounded-t-lg').style(f'background-color: {product.image_color or "#95a5a6"}'):
                ui.icon('checkroom', size='3rem').classes('text-white')
                ui.label(product.category).classes('text-white font-bold')
            
            # Информация
            with ui.column().classes('p-3 gap-2'):
                ui.label(product.name).classes('font-bold text-lg')
                ui.label(f'{product.price:.0f} ₽').classes('text-blue-600 font-bold')
                
                with ui.row().classes('gap-2'):
                    ui.badge(product.category, color='blue')
                    ui.badge(f'Размер: {product.size}', color='gray')
                
                if product.quantity > 0:
                    ui.badge(f'В наличии: {product.quantity} шт.', color='green')
                else:
                    ui.badge('Нет в наличии', color='red')
                
                ui.button('Изменить', on_click=lambda p=product: self.edit_product(p.id)).props('flat')
    
    def show_add_form(self):
        self.clear_content()
        
        product = Product()
        title = 'Добавить товар'
        
        if self.editing_id:
            product = self.db.get_product(self.editing_id)
            if product:
                title = 'Изменить товар'
        
        with self.content:
            ui.label(title).style('font-size: 1.5rem; font-weight: bold')
            
            with ui.card().classes('w-full max-w-xl mx-auto p-6'):
                # Основная информация
                self.name_input = ui.input(label='Название *', value=product.name,
                                          validation={'Обязательно': lambda v: bool(v)}).props('outlined')
                
                self.price_input = ui.number(label='Цена *', value=product.price, min=0,
                                            validation={'Должна быть > 0': lambda v: v > 0}).props('outlined')
                
                self.category_input = ui.select(label='Категория *',
                                              options=['Мужская', 'Женская'],
                                              value=product.category or 'Мужская').props('outlined')
                
                self.size_input = ui.select(label='Размер *',
                                          options=['XS', 'S', 'M', 'L', 'XL'],
                                          value=product.size or 'M').props('outlined')
                
                self.quantity_input = ui.number(label='Количество', value=product.quantity, min=0).props('outlined')
                
                # Выбор цвета для фото
                colors = [
                    {'label': 'Синий', 'value': '#3498db'},
                    {'label': 'Темно-синий', 'value': '#2980b9'},
                    {'label': 'Черный', 'value': '#2c3e50'},
                    {'label': 'Красный', 'value': '#e74c3c'},
                    {'label': 'Бордовый', 'value': '#c0392b'},
                    {'label': 'Оранжевый', 'value': '#e67e22'},
                    {'label': 'Зеленый', 'value': '#27ae60'},
                    {'label': 'Серый', 'value': '#95a5a6'},
                ]
                
                self.color_input = ui.select(label='Цвет товара',
                                           options=colors,
                                           value=product.image_color or '#3498db').props('outlined')
                
                # Предпросмотр цвета
                with ui.row().classes('items-center gap-2'):
                    ui.label('Предпросмотр:')
                    ui.icon('checkroom').style(f'color: {self.color_input.value}; font-size: 2rem')
                
                # Кнопки
                with ui.row().classes('w-full justify-end gap-2 mt-4'):
                    ui.button('Отмена', on_click=self.show_catalog).props('flat')
                    if self.editing_id:
                        ui.button('Сохранить', on_click=self.save_product, icon='save').props('color=primary')
                    else:
                        ui.button('Добавить', on_click=self.save_product, icon='add').props('color=primary')
    
    def edit_product(self, product_id: int):
        self.editing_id = product_id
        self.show_add_form()
    
    def save_product(self):
        if not self.name_input.value or self.price_input.value <= 0:
            ui.notify('Заполните обязательные поля', type='warning')
            return
        
        product = Product(
            id=self.editing_id,
            name=self.name_input.value,
            price=float(self.price_input.value),
            category=self.category_input.value,
            size=self.size_input.value,
            quantity=int(self.quantity_input.value),
            image_color=self.color_input.value
        )
        
        try:
            if self.editing_id:
                self.db.update_product(product)
                ui.notify('Товар обновлён', type='positive')
            else:
                self.db.add_product(product)
                ui.notify('Товар добавлен', type='positive')
            
            self.show_catalog()
        except Exception as e:
            ui.notify(f'Ошибка: {e}', type='negative')


if __name__ == '__main__':
    SimpleCatalog()
    ui.run(title='Каталог одежды', port=8080, reload=False)