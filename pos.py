import sys
import os
import json
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5 import QtGui
from pos_ui import Ui_pos


class POSApp(QMainWindow, Ui_pos):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        #add editable amount on add to cart (should show amount when a product is clicked (C001 x3))

        # Data for POS
        self.cart = []
        self.products = {
            "C001": ("Chocolate Moist", 850.00),
            "C002": ("Yema Vanilla", 760.00),
            "C003": ("Caramel Cake", 820.00),
            "C004": ("Ube Caramel", 750.00),
            "C005": ("Red Velvet", 850.00),
            "C006": ("Pandan Cake", 760.00),
            "C007": ("Strawberry Cake", 780.00),
            "C008": ("Biscoff Mocha", 900.00),
            "C009": ("Bento Cake", 370.00),
            "C010": ("Cupcake", 40.00),
        }

        # Connect buttons to functions
        self.btnC001.clicked.connect(lambda: self.add_to_cart("C001"))
        self.btnC002.clicked.connect(lambda: self.add_to_cart("C002"))
        self.btnC003.clicked.connect(lambda: self.add_to_cart("C003"))
        self.btnC004.clicked.connect(lambda: self.add_to_cart("C004"))
        self.btnC005.clicked.connect(lambda: self.add_to_cart("C005"))
        self.btnC006.clicked.connect(lambda: self.add_to_cart("C006"))
        self.btnC007.clicked.connect(lambda: self.add_to_cart("C007"))
        self.btnC008.clicked.connect(lambda: self.add_to_cart("C008"))
        self.btnC009.clicked.connect(lambda: self.add_to_cart("C009"))
        self.btnC010.clicked.connect(lambda: self.add_to_cart("C010"))

        self.btnClear.clicked.connect(self.clear_cart)
        self.btnCheckout.clicked.connect(self.checkout)

    def add_to_cart(self, product_code):
        """Add product to cart."""
        product_name, price = self.products[product_code]
        self.cart.append((product_name, price))
        self.update_cart_display()

    def update_cart_display(self):
        """Update the cart display."""
        if self.cart:
            cart_summary = "\n".join([f"{item[0]} - ₱{item[1]:.2f}" for item in self.cart])
            self.cartlabel.setText(cart_summary)
            
            total = sum(item[1] for item in self.cart)
            self.checkoutlabel.setText(f"\n\nTotal: ₱{total:.2f}")
            
        else:
            self.cartlabel.setText("Cart is empty")
            self.checkoutlabel.setText("Total: ₱0.00")
        
    def clear_cart(self):
        """Clear the cart."""
        self.cart.clear()
        self.update_cart_display()

    def checkout(self):
        """Process checkout."""
        if not self.cart:
            QMessageBox.warning(self, "Checkout Error", "Cart is empty!")
            return

        # Create Receipt
        counter_path = os.path.join("json","receipt_counter.json")
        with open(counter_path, "r") as json_file:
            rcptNum = json.load(json_file)
            
        counter_update = rcptNum + 1
        receipt = f"R#{counter_update:05}.json"
        file_path = os.path.join("receipts", receipt)
        
        # Write data to the JSON file
        with open(file_path, "w") as json_file:
            json.dump(self.cart, json_file, indent=4)
        
        # Update Receipt Counter
        with open(counter_path, "w") as json_file:
            json.dump(counter_update, json_file)
        
        total = sum(item[1] for item in self.cart)
        QMessageBox.information(self, "Checkout", f"Total Amount: ₱{total:.2f}\nThank you for your purchase!")
        self.clear_cart()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = POSApp()
    window.show()
    sys.exit(app.exec_())
