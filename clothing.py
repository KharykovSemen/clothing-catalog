from nicegui import ui
import sqlite3
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Product:
    id: Optional[int] = None
    name: str = ""
    price: float = 0.0
    category: str = ""  # Мужская/Женская
    size: str = ""
    quantity: int = 0
    color: str = ""  # для фона


class Cart:
    def __init__(self):
        self.items = []  # список товаров в корзине
    
    def add(self, product: Product):
        self.items.append(product)
        ui.notify(f'Товар "{product.name}" добавлен в корзину', type='positive')
    
    def remove(self, index: int):
        removed = self.items.pop(index)
        ui.notify(f'Товар "{removed.name}" удален из корзины', type='warning')
    
    def clear(self):
        self.items.clear()
    
    def total(self) -> float:
        return sum(item.price for item in self.items)
    
    def count(self) -> int:
        return len(self.items)


class Database:
    def __init__(self, db_file='shop.db'):
        self.db_file = db_file
        self._init_db()
        self._add_sample_products()
    
    def _init_db(self):
        with sqlite3.connect(self.db_file) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    price REAL NOT NULL,
                    category TEXT,
                    size TEXT,
                    quantity INTEGER DEFAULT 0,
                    color TEXT
                )
            ''')
    
    def _add_sample_products(self):
        with sqlite3.connect(self.db_file) as conn:
            count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
            if count == 0:
                samples = [
                    ('Футболка мужская', 1299, 'Мужская', 'M', 25, '#3498db'),
                    ('Джинсы мужские', 3499, 'Мужская', 'L', 15, '#2c3e50'),
                    ('Куртка мужская', 8999, 'Мужская', 'XL', 8, '#34495e'),
                    ('Футболка женская', 1299, 'Женская', 'S', 20, '#e74c3c'),
                    ('Джинсы женские', 3499, 'Женская', 'M', 12, '#c0392b'),
                    ('Платье', 2799, 'Женская', 'M', 10, '#e67e22'),
                    ('Шорты мужские', 999, 'Мужская', 'L', 30, '#27ae60'),
                    ('Юбка', 1999, 'Женская', 'S', 15, '#9b59b6'),
                    ('Свитер женский', 3999, 'Женская', 'M', 7, '#f39c12'),
                ]
                for item in samples:
                    conn.execute('''
                        INSERT INTO products (name, price, category, size, quantity, color)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', item)
    
    def get_products(self, category: str = None, size: str = None, search: str = None) -> List[Product]:
        with sqlite3.connect(self.db_file) as conn:
            conn.row_factory = sqlite3.Row
            query = "SELECT * FROM products WHERE 1=1"
            params = []
            
            if category and category != 'Все':
                query += " AND category = ?"
                params.append(category)
            
            if size and size != 'Все':
                query += " AND size = ?"
                params.append(size)
            
            if search and search.strip():
                query += " AND name LIKE ?"
                params.append(f'%{search.strip()}%')
            
            cursor = conn.execute(query, params)
            return [Product(**dict(row)) for row in cursor.fetchall()]


class ClothingCatalog:
    def __init__(self):
        self.db = Database()
        self.cart = Cart()
        self._create_ui()
    
    def _create_ui(self):
        # Шапка
        with ui.header().style('background-color: #2c3e50'):
            with ui.row().classes('w-full items-center justify-between'):
                ui.label(' Магазин одежды').style('font-size: 1.5rem; font-weight: bold')
                
                with ui.row().classes('gap-2'):
                    ui.button('Каталог', on_click=self._show_catalog, icon='store').props('flat')
                    ui.button('Корзина', on_click=self._show_cart, icon='shopping_cart').props('flat')
        
        # Основной контент
        self.content = ui.column().classes('w-full p-4')
        self._show_catalog()
    
    def _clear_content(self):
        self.content.clear()
    
    def _show_catalog(self):
        self._clear_content()
        
        with self.content:
            ui.label('Каталог товаров').style('font-size: 2rem; font-weight: bold').classes('mb-4')
            
            # Поиск и фильтры
            with ui.column().classes('w-full gap-4 mb-6'):
                # Строка поиска
                with ui.row().classes('w-full items-center gap-2'):
                    self.search_input = ui.input(
                        placeholder='Поиск по названию...',
                        on_change=self._update_catalog
                    ).props('outlined').classes('flex-grow')
                    ui.icon('search').classes('text-gray-400 -ml-10')
                
                # Фильтры
                with ui.row().classes('gap-4 items-center'):
                    ui.label('Фильтры:').style('font-weight: bold')
                    
                    self.category_filter = ui.select(
                        label='Категория',
                        options=['Все', 'Мужская', 'Женская'],
                        value='Все',
                        on_change=self._update_catalog
                    ).classes('w-40')
                    
                    self.size_filter = ui.select(
                        label='Размер',
                        options=['Все', 'XS', 'S', 'M', 'L', 'XL'],
                        value='Все',
                        on_change=self._update_catalog
                    ).classes('w-40')
                    
                    # Кнопка сброса фильтров
                    ui.button(
                        'Сбросить', 
                        on_click=self._reset_filters,
                        icon='clear'
                    ).props('flat').classes('ml-auto')
            
            # Информация о количестве найденных товаров
            self.results_info = ui.label().classes('text-gray-600 mb-2')
            
            # Сетка товаров
            self.products_grid = ui.grid(columns=3).classes('w-full gap-4')
            self._update_catalog()
    
    def _reset_filters(self):
        self.search_input.value = ''
        self.category_filter.value = 'Все'
        self.size_filter.value = 'Все'
        self._update_catalog()
    
    def _update_catalog(self):
        self.products_grid.clear()
        
        products = self.db.get_products(
            category=self.category_filter.value if self.category_filter.value != 'Все' else None,
            size=self.size_filter.value if self.size_filter.value != 'Все' else None,
            search=self.search_input.value
        )
        
        # Обновляем информацию о количестве
        if hasattr(self, 'results_info'):
            if self.search_input.value:
                self.results_info.set_text(f'Найдено товаров: {len(products)} по запросу "{self.search_input.value}"')
            else:
                self.results_info.set_text(f'Всего товаров: {len(products)}')
        
        with self.products_grid:
            if not products:
                with ui.column().classes('items-center justify-center p-8 col-span-3'):
                    ui.icon('search_off', size='4rem').classes('text-gray-400')
                    ui.label('Товары не найдены').classes('text-center text-gray-500 text-lg')
                    if self.search_input.value:
                        ui.label(f'По запросу "{self.search_input.value}" ничего не найдено').classes('text-gray-400')
            else:
                for product in products:
                    self._create_product_card(product)
    
    def _create_product_card(self, product: Product):
        with ui.card().classes('w-full hover:shadow-lg transition-shadow'):
            # Изображение (цветной фон с иконкой)
            with ui.column().classes('w-full h-40 items-center justify-center rounded-t-lg').style(
                f'background-color: {product.color or "#95a5a6"}'
            ):
                ui.icon('checkroom', size='3rem').classes('text-white')
                ui.label(product.category).classes('text-white text-sm font-bold')
            
            # Информация о товаре
            with ui.column().classes('p-3 gap-2'):
                # Подсветка совпадений при поиске
                if self.search_input.value and self.search_input.value.lower() in product.name.lower():
                    ui.html(f'<span class="font-bold text-lg">{self._highlight_text(product.name, self.search_input.value)}</span>')
                else:
                    ui.label(product.name).classes('font-bold text-lg')
                
                ui.label(f'{product.price:,.0f} ₽').classes('text-blue-600 font-bold text-xl')
                
                with ui.row().classes('gap-2'):
                    ui.badge(product.category, color='blue')
                    ui.badge(f'Размер {product.size}', color='gray')
                
                # Наличие
                if product.quantity > 0:
                    ui.badge(f'В наличии: {product.quantity} шт.', color='green')
                    
                    # Кнопка добавления в корзину
                    ui.button(
                        'В корзину', 
                        on_click=lambda p=product: self.cart.add(p),
                        icon='add_shopping_cart'
                    ).props('outline').classes('mt-2')
                else:
                    ui.badge('Нет в наличии', color='red')
    
    def _highlight_text(self, text: str, search: str) -> str:
        """Подсвечивает совпадения при поиске"""
        if not search:
            return text
        search_lower = search.lower()
        text_lower = text.lower()
        
        if search_lower in text_lower:
            start = text_lower.index(search_lower)
            end = start + len(search)
            return f'{text[:start]}<span class="bg-yellow-200">{text[start:end]}</span>{text[end:]}'
        return text
    
    def _show_cart(self):
        self._clear_content()
        
        with self.content:
            ui.label('Корзина').style('font-size: 2rem; font-weight: bold').classes('mb-4')
            
            if not self.cart.items:
                with ui.column().classes('items-center justify-center p-8'):
                    ui.icon('shopping_cart', size='4rem').classes('text-gray-400')
                    ui.label('Корзина пуста').classes('text-gray-500 text-lg')
                    ui.label('Добавьте товары из каталога').classes('text-gray-400')
                    ui.button('Вернуться к покупкам', on_click=self._show_catalog).props('flat').classes('mt-4')
                return
            
            # Список товаров в корзине
            with ui.column().classes('w-full gap-2'):
                for i, item in enumerate(self.cart.items):
                    with ui.card().classes('w-full p-4'):
                        with ui.row().classes('w-full items-center justify-between'):
                            with ui.row().classes('items-center gap-4'):
                                # Цветной квадратик
                                ui.icon('checkroom').style(f'color: {item.color}; font-size: 2rem')
                                
                                with ui.column().classes('gap-1'):
                                    ui.label(item.name).classes('font-bold')
                                    ui.label(f'{item.category} | Размер {item.size}').classes('text-sm text-gray-600')
                            
                            with ui.row().classes('items-center gap-4'):
                                ui.label(f'{item.price:,.0f} ₽').classes('font-bold')
                                ui.button(icon='delete', on_click=lambda idx=i: self._remove_from_cart(idx)).props('flat dense round')
                
                # Итого
                with ui.card().classes('w-full p-4 mt-4'):
                    with ui.row().classes('w-full items-center justify-between'):
                        ui.label('Итого:').style('font-size: 1.2rem')
                        ui.label(f'{self.cart.total():,.0f} ₽').style('font-size: 1.5rem; font-weight: bold; color: #2c3e50')
                    
                    with ui.row().classes('w-full justify-end gap-2 mt-4'):
                        ui.button('Очистить корзину', on_click=self._clear_cart).props('outline')
                        ui.button('Оформить заказ', on_click=self._checkout).props('color=positive')
    
    def _remove_from_cart(self, index: int):
        self.cart.remove(index)
        self._show_cart()  # обновляем отображение корзины
    
    def _clear_cart(self):
        self.cart.clear()
        self._show_cart()
    
    def _checkout(self):
        if not self.cart.items:
            ui.notify('Корзина пуста', type='warning')
            return
        
        total = self.cart.total()
        self.cart.clear()
        ui.notify(f'Заказ оформлен! Сумма: {total:,.0f} ₽', type='positive')
        self._show_catalog()


if __name__ == '__main__':
    ClothingCatalog()
    ui.run(
        title='Магазин одежды',
        port=8080,
        reload=False
    )