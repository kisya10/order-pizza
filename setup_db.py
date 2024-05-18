import sqlite3

conn = sqlite3.connect('pizza.db')
c = conn.cursor()

# Create tables
c.execute('''
CREATE TABLE users (
    username TEXT PRIMARY KEY,
    password TEXT NOT NULL
)
''')

c.execute('''
CREATE TABLE pizzas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    price REAL NOT NULL
)
''')

c.execute('''
CREATE TABLE cart (
    username TEXT,
    item_id INTEGER,
    FOREIGN KEY (username) REFERENCES users(username),
    FOREIGN KEY (item_id) REFERENCES pizzas(id)
)
''')

c.execute('''
CREATE TABLE orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    item_id INTEGER,
    FOREIGN KEY (username) REFERENCES users(username),
    FOREIGN KEY (item_id) REFERENCES pizzas(id)
)
''')

# Insert sample data into pizzas table
c.execute("INSERT INTO pizzas (name, price) VALUES ('Classified Chicken', 18.99)")
c.execute("INSERT INTO pizzas (name, price) VALUES ('Beef Pepperoni', 19.99)")
c.execute("INSERT INTO pizzas (name, price) VALUES ('Hawaiian', 18.99)")
c.execute("INSERT INTO pizzas (name, price) VALUES ('BBQ Chicken', 17.99)")
c.execute("INSERT INTO pizzas (name, price) VALUES ('Veggie', 17.99)")

conn.commit()
conn.close()
