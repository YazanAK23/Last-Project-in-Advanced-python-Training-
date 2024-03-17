from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os 
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
engine = create_engine('sqlite:///bookstore.db')

# Create a session
Session = sessionmaker(bind=engine)
session = Session()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bookstore.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'  # Change this to a random secret key
db = SQLAlchemy(app)


# SQLAlchemy Models
class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return f"Book('{self.title}', '{self.author}', '{self.price}', '{self.quantity}', '{self.category}')"

class ShoppingCart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    items = db.relationship('OrderItem', backref='cart', lazy=True, overlaps="cart")
    purchased_orders = db.relationship('Order', backref='cart', lazy=True)





class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('shopping_cart.id'), nullable=False)
    purchase_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)



class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    shopping_cart_id = db.Column(db.Integer, db.ForeignKey('shopping_cart.id'), nullable=False)



# Routes
@app.route('/books', methods=['GET'])
def get_books():
    books = Book.query.all()
    output = []
    for book in books:
        book_data = {'id': book.id, 'title': book.title, 'author': book.author,
                     'price': book.price, 'quantity': book.quantity, 'category': book.category}
        output.append(book_data)
    return jsonify({'books': output})


@app.route('/books', methods=['POST'])
def add_book():
    data = request.json
    new_book = Book(title=data['title'], author=data['author'], price=data['price'],
                    quantity=data['quantity'], category=data['category'])
    db.session.add(new_book)
    db.session.commit()
    return jsonify({'message': 'Book added successfully'}), 201


@app.route('/books/<int:book_id>', methods=['GET'])
def get_book(book_id):
    book = Book.query.get_or_404(book_id)
    book_data = {'id': book.id, 'title': book.title, 'author': book.author,
                 'price': book.price, 'quantity': book.quantity, 'category': book.category}
    return jsonify({'book': book_data})


@app.route('/books/<int:book_id>', methods=['PUT'])
def update_book(book_id):
    book = Book.query.get_or_404(book_id)
    data = request.json
    book.title = data['title']
    book.author = data['author']
    book.price = data['price']
    book.quantity = data['quantity']
    book.category = data['category']
    db.session.commit()
    return jsonify({'message': 'Book updated successfully'})


@app.route('/books/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)
    db.session.delete(book)
    db.session.commit()
    return jsonify({'message': 'Book deleted successfully'})


@app.route('/inventory', methods=['GET'])
def view_inventory():
    books = Book.query.all()
    output = []
    for book in books:
        book_data = {'id': book.id, 'title': book.title, 'author': book.author,
                     'price': book.price, 'quantity': book.quantity, 'category': book.category}
        output.append(book_data)
    return jsonify({'inventory': output})


# Route for purchasing books
@app.route('/purchase', methods=['POST'])
def purchase_books():
    data = request.json
    cart_id = data['cart_id']  # Assuming you pass the shopping cart ID in the request
    book_id = data['book_id']
    quantity = data['quantity']

    # Check if the book exists
    book = Book.query.get(book_id)
    if not book:
        return jsonify({'error': 'Book not found'}), 404

    # Check if there are enough quantities available
    if book.quantity < quantity:
        return jsonify({'error': 'Not enough quantity available'}), 400

    # Create an order item
    order_item = OrderItem(book_id=book_id, quantity=quantity, shopping_cart_id=cart_id)
    db.session.add(order_item)

    # Create or retrieve the shopping cart
    shopping_cart = ShoppingCart.query.get(cart_id)
    if not shopping_cart:
        shopping_cart = ShoppingCart(id=cart_id)
        db.session.add(shopping_cart)

    # Create an order if it doesn't exist
    order = Order.query.filter_by(cart_id=cart_id).first()
    if not order:
        order = Order(cart_id=cart_id)
        db.session.add(order)

    # Add the order item to the order
    order_item.order_id = order.id

    # Update the quantity of the book in inventory (assuming you decrement it)
    book.quantity -= quantity

    # Commit changes to the database
    db.session.commit()

    return jsonify({'message': 'Purchase successful'})


#View Purchased Orders
@app.route('/purchased_orders/<int:cart_id>', methods=['GET'])
def view_purchased_orders_by_cart(cart_id):
    orders = Order.query.filter_by(cart_id=cart_id).all()
    if not orders:
        return jsonify({'error': 'No orders found for this cart'}), 404

    output = []
    for order in orders:
        order_data = {'id': order.id, 'purchase_date': order.purchase_date,
                      'items': [{'book_id': item.book_id, 'quantity': item.quantity} for item in order.orderitem]}
        output.append(order_data)

    return jsonify({'purchased_orders': output})


#delete books from the card
@app.route('/cart/<int:book_id>', methods=['DELETE'])
def delete_book_from_cart(book_id):
    # Example payload might need to include cart_id to identify the specific cart
    data = request.json
    cart_id = data['cart_id']
    order_item = OrderItem.query.filter_by(book_id=book_id, shopping_cart_id=cart_id).first()
    if order_item:
        db.session.delete(order_item)
        db.session.commit()
        return jsonify({'message': 'Book removed from cart successfully'})
    else:
        return jsonify({'error': 'Book not found in cart'}), 404


#View Shopping Cart
@app.route('/cart/<int:cart_id>', methods=['GET'])
def view_shopping_cart(cart_id):
    cart = ShoppingCart.query.get_or_404(cart_id)
    items = OrderItem.query.filter_by(shopping_cart_id=cart_id).all()

    cart_items = []
    for item in items:
        book = Book.query.get(item.book_id)
        cart_items.append({'book_id': item.book_id, 'title': book.title, 'quantity': item.quantity})

    return jsonify({'cart_id': cart_id, 'items': cart_items})

# Add Book to Shopping Cart
@app.route('/cart/add', methods=['POST'])
def add_book_to_cart():
    data = request.json
    cart_id = data['cart_id']
    book_id = data['book_id']
    quantity = data['quantity']

    # Check if the book exists and if there's enough stock
    book = Book.query.get_or_404(book_id)
    if book.quantity < quantity:
        return jsonify({'error': 'Not enough stock available'}), 400

    # Check if the cart exists, if not create it
    shopping_cart = ShoppingCart.query.get(cart_id)
    if not shopping_cart:
        shopping_cart = ShoppingCart(id=cart_id)
        db.session.add(shopping_cart)

    # Create and add the new order item
    new_item = OrderItem(book_id=book_id, quantity=quantity, shopping_cart_id=cart_id)
    db.session.add(new_item)
    db.session.commit()

    return jsonify({'message': 'Book added to cart successfully'})





@app.route('/inventory/search', methods=['GET'])
def search_inventory():
    title = request.args.get('title')
    books = Book.query.filter(Book.title.ilike(f'%{title}%')).all()
    output = []
    for book in books:
        book_data = {'id': book.id, 'title': book.title, 'author': book.author,
                     'price': book.price, 'quantity': book.quantity, 'category': book.category}
        output.append(book_data)
    return jsonify({'matching_books': output})


@app.route('/category/<category_name>', methods=['GET'])
def view_books_by_category(category_name):
    books = Book.query.filter_by(category=category_name).all()
    output = []
    for book in books:
        book_data = {'id': book.id, 'title': book.title, 'author': book.author,
                     'price': book.price, 'quantity': book.quantity, 'category': book.category}
        output.append(book_data)
    return jsonify({'books_in_category': output})


@app.route('/category/search', methods=['GET'])
def search_by_category():
    category_name = request.args.get('category_name')
    books = Book.query.filter_by(category=category_name).all()
    output = []
    for book in books:
        book_data = {'id': book.id, 'title': book.title, 'author': book.author,
                     'price': book.price, 'quantity': book.quantity, 'category': book.category}
        output.append(book_data)
    return jsonify({'books_in_category': output})




# Create SQLAlchemy engine

if __name__ == "__main__":
    db.create_all()
    app.run(debug=True)
    with app.app_context():
        # Add some  data only if the database is empty
        if not Book.query.all():
            # Create some  books
            book1 = Book(title="Python Programming", author="Guido van Rossum", price=29.99, quantity=10, category="Programming")
            book2 = Book(title="Data Structures and Algorithms", author="John Doe", price=39.99, quantity=5, category="Programming")
            book3 = Book(title="To Kill a Mockingbird", author="Harper Lee", price=15.00, quantity=20, category="Fiction")
            book4 = Book(title="1984", author="George Orwell", price=12.99, quantity=15, category="Fiction")

            book5 = Book(title="The Great Gatsby", author="F. Scott Fitzgerald", price=17.99, quantity=8, category="Fiction")
            book6 = Book(title="The Catcher in the Rye", author="J.D. Salinger", price=14.50, quantity=12, category="Fiction")
            book7 = Book(title="The Hobbit", author="J.R.R. Tolkien", price=21.99, quantity=15, category="Fantasy")
            book8 = Book(title="Pride and Prejudice", author="Jane Austen", price=12.00, quantity=10, category="Romance")

            # Add these books to the database
            db.session.add_all([book5, book6, book7, book8])
            db.session.commit()


            print("data added successfully.")


