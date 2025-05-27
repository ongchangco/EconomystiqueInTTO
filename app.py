import sys, sqlite3, os, json, torch, openpyxl
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import bcrypt


from PyQt5.uic import loadUi
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QToolButton, QFileDialog, QDateEdit, QTableWidget, QLabel, QToolTip, QComboBox, QDialogButtonBox, QPushButton, QListWidget, QApplication, QMainWindow, QMessageBox, QAbstractItemView, QHeaderView, QDialog, QTableWidgetItem, QVBoxLayout, QGraphicsDropShadowEffect, QTextEdit, QLineEdit, QWidget
from PyQt5.QtCore import Qt, QDate, pyqtSignal, QThread, QTimer, QStringListModel, QModelIndex, QSize, QBuffer, QIODevice
from PyQt5.QtGui import  QValidator, QIntValidator, QDoubleValidator, QStandardItemModel, QStandardItem, QIcon, QColor, QPixmap
from transformers import pipeline, GPTNeoForCausalLM, GPT2Tokenizer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

#additional imports for each page
from login_ui import Ui_Login
from signIn_ui import Ui_signUp
from dashboard_ui import Ui_Dashboard
from salesForecast_ui import Ui_SalesForecast
from account_ui import Ui_account
from sales_ui import Ui_Sales
from inventory_ui import Ui_inventoryManagement
from add_item_ui import Ui_Dialog
from restock_ui import Ui_Restock
from productRestock_ui import Ui_PrRestock
from addCritical_ui import Ui_AddCritical
from addExisting_ui import Ui_AddExisting
from addPrExisting_ui import Ui_AddPrExisting
from addPrNew_ui import Ui_addPrNew
from pos_ui import Ui_pos
from critical_ui import Ui_criticalItems
from comparison_ui import Ui_Comparison
from addingWarning_ui import Ui_stockWarning
from wastage_ui import Ui_decWastage
from sales_utils import fetch_sales_data

class MainWindow(QMainWindow):
    switch_to_login = pyqtSignal()
    def __init__(self, icon_path):
        super(MainWindow, self).__init__()
        self.setWindowTitle("Economystique")
        self.setWindowIcon(QIcon(icon_path))
        self.setFixedSize(1600, 900)
        self.setStyleSheet("""
            QMainWindow {
                background-image: url(img/3_lighter.png);
                background-repeat: no-repeat;
                background-position: center;5
            }
        """)
        # Create your stacked widget for Dashboard, Inventory, etc.
        self.widget = QtWidgets.QStackedWidget()
        self.setCentralWidget(self.widget)

        # Initialize pages
        self.dashboard = Dashboard()
        self.inventory = Inventory(self.widget)
        self.sales = SalesWindow(self.widget)
        self.salesForecast = SalesForecastWindow(self.widget)
        self.POS = POSWindow(self.widget)
        self.account = AccountWindow(self.widget)
        self.critical = CriticalWindow(self.widget)
        self.compare = ComPerformance(self.widget)


        # Update Listeners
        self.POS.inventory_update.connect(self.inventory.populate_products)
        self.POS.sales_update.connect(self.sales.load_sales_data)
        
        # Add widgets to stackedWidget
        self.widget.addWidget(self.dashboard)
        self.widget.addWidget(self.inventory)
        self.widget.addWidget(self.sales)
        self.widget.addWidget(self.salesForecast)
        self.widget.addWidget(self.POS)
        self.widget.addWidget(self.account)
        self.widget.addWidget(self.compare)

        # Connect widget signals to handlers
        self.dashboard.go_to_inventory.connect(self.show_inventory)
        self.dashboard.go_to_sales.connect(self.show_sales)
        self.dashboard.go_to_pos.connect(self.show_pos)
        self.dashboard.go_to_account.connect(self.show_account)
        self.dashboard.go_to_compare.connect(self.show_compare)
        self.dashboard.go_to_wastage.connect(self.show_wastage)
        self.dashboard.critical_item_selected.connect(self.focus_critical_item)
        self.critical.critical_item_selected.connect(self.focus_critical_item)
        
        self.compare.go_to_dashboard.connect(self.show_dashboard)
        self.compare.go_to_inventory.connect(self.show_inventory)
        self.compare.go_to_sales.connect(self.show_sales)
        self.compare.go_to_pos.connect(self.show_pos)
        self.compare.go_to_account.connect(self.show_account)
        
        self.inventory.go_to_dashboard.connect(self.show_dashboard)
        self.inventory.go_to_sales.connect(self.show_sales)
        self.inventory.go_to_pos.connect(self.show_pos)
        self.inventory.go_to_account.connect(self.show_account)
        self.inventory.expiredCheckRequested.connect(self.dashboard.load_expired_products)
        
        self.sales.go_to_inventory.connect(self.show_inventory)
        self.sales.go_to_dashboard.connect(self.show_dashboard)
        self.sales.go_to_pos.connect(self.show_pos)
        self.sales.go_to_account.connect(self.show_account)
        self.sales.go_to_salesForecast.connect(self.show_salesForecast)
        
        self.salesForecast.go_to_dashboard.connect(self.show_dashboard)
        self.salesForecast.go_to_inventory.connect(self.show_inventory)
        self.salesForecast.go_to_sales.connect(self.show_sales)
        self.salesForecast.go_to_pos.connect(self.show_pos)
        self.salesForecast.go_to_account.connect(self.show_account)
        
        self.POS.go_to_inventory.connect(self.show_inventory)
        self.POS.go_to_sales.connect(self.show_sales)
        self.POS.go_to_dashboard.connect(self.show_dashboard)
        self.POS.go_to_account.connect(self.show_account)
        
        self.account.go_to_inventory.connect(self.show_inventory)
        self.account.go_to_sales.connect(self.show_sales)
        self.account.go_to_pos.connect(self.show_pos)
        self.account.go_to_dashboard.connect(self.show_dashboard)
        self.account.switch_to_login.connect(self.logout_to_login)

        # Landing Page
        self.widget.setCurrentWidget(self.dashboard)

    def show_dashboard(self):
        self.widget.setCurrentWidget(self.dashboard)
    def show_compare(self):
        self.widget.setCurrentWidget(self.compare)
    def show_inventory(self):
        self.widget.setCurrentWidget(self.inventory)
    def show_sales(self):
        self.widget.setCurrentWidget(self.sales)
    def show_salesForecast(self):
        self.widget.setCurrentWidget(self.salesForecast)
    def show_pos(self):
        self.POS.load_product_buttons()
        self.widget.setCurrentWidget(self.POS)
    def show_account(self):
        self.widget.setCurrentWidget(self.account)
    def show_wastage(self):
        wastage_window = DecWastage()
        wastage_window.exec_()
    def focus_critical_item(self, description):
        self.widget.setCurrentWidget(self.inventory)
        self.inventory.focus_on_item(description)
    def logout_to_login(self):
        self.switch_to_login.emit()
        self.close()
class Login(QMainWindow):
    switch_to_signup = pyqtSignal()
    switch_to_main = pyqtSignal()

    def __init__(self):
        super(Login, self).__init__()
        self.setWindowTitle("Login")
        self.setFixedSize(800, 600)
        self.ui = Ui_Login()
        self.ui.setupUi(self)

        self.ui.pushButton.clicked.connect(self.loginfunction)
        self.ui.signUpButton.clicked.connect(self.open_signUp)

    def open_signUp(self):
        self.switch_to_signup.emit()
        self.close()

    def loginfunction(self):
        db_path = os.path.join("db", "users_db.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get input values
        userInName = self.ui.leUser.text()
        userInPW = self.ui.lePW.text().encode('utf-8') 

        # Check if user exists
        cursor.execute("SELECT pw_hash FROM user_data WHERE user_name = ?", (userInName,))
        result = cursor.fetchone()

        if result:
            stored_hash = result[0].encode('utf-8')

            # Check password
            if bcrypt.checkpw(userInPW, stored_hash):
                self.switch_to_main.emit()
                self.close()
            else:
                QMessageBox.warning(self, "Login Failed", "Incorrect password")
        else:
            QMessageBox.warning(self, "Login Failed", "Please enter your username")

        conn.close()    
class SignUp(QMainWindow):
    switch_to_login = pyqtSignal()
    switch_to_main = pyqtSignal()

    def __init__(self):
        super(SignUp, self).__init__()
        self.setWindowTitle("Sign Up")
        self.setFixedSize(800, 600)
        self.ui = Ui_signUp()
        self.ui.setupUi(self)

        self.ui.loginButton.clicked.connect(self.open_Login)
        self.ui.pushButton.clicked.connect(self.signinfunction)

    def open_Login(self):
        self.switch_to_login.emit()
        self.close()

    def signinfunction(self):
        self.switch_to_main.emit()
        self.close()
class Dashboard(QMainWindow):
    go_to_inventory = pyqtSignal()
    go_to_sales = pyqtSignal()
    go_to_pos = pyqtSignal()
    go_to_account = pyqtSignal()
    go_to_compare = pyqtSignal()
    go_to_wastage = pyqtSignal()
    go_to_critical = pyqtSignal()
    critical_item_selected = pyqtSignal(str)
    def __init__(self):
        super(Dashboard, self).__init__()
        self.ui = Ui_Dashboard()
        self.ui.setupUi(self)
        
        self.sales_canvas = FigureCanvas(plt.figure())
        layout = QVBoxLayout()
        layout.addWidget(self.sales_canvas)
        
        # Notifications
        self.load_expired_products()
        self.ui.lsExpProducts.hide()
        
        self.ui.gpPerformance.setLayout(layout)
        self.display_sales_performance()
        
        # Connect Buttons
        self.ui.btnIngredients.clicked.connect(self.go_to_inventory.emit)
        self.ui.btnProducts.clicked.connect(self.go_to_inventory.emit)
        self.ui.btnWastage.clicked.connect(self.go_to_wastage.emit)
        self.ui.btnSales.clicked.connect(self.go_to_sales.emit)
        self.ui.btnPOS.clicked.connect(self.go_to_pos.emit)
        self.ui.btnAccount.clicked.connect(self.go_to_account.emit)
        self.ui.btnCritical.clicked.connect(self.go_to_critical)
        self.ui.btnCompare.clicked.connect(self.go_to_compare.emit)
        self.ui.btnNotif.clicked.connect(self.show_exp_products)
        
    def show_exp_products(self):
        if self.ui.lsExpProducts.isVisible():
            self.ui.lsExpProducts.hide()
        else:
            self.ui.lsExpProducts.show()
            self.ui.lblBadge.hide()
            
    def load_expired_products(self):
        self.ui.lsExpProducts.clear()
        today = QDate.currentDate().toString("dd/MM/yy")
        today_obj = QDate.fromString(today, "dd/MM/yy")

        db_path = os.path.join("db", "product_db.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT product_name, on_hand, exp_date FROM products_on_hand")
        expired_products = []

        for product_name, on_hand, exp_date in cursor.fetchall():
            if exp_date and exp_date.lower() != "n/a":
                exp_date_obj = QDate.fromString(exp_date, "dd/MM/yy")
                if exp_date_obj.isValid() and exp_date_obj <= today_obj:
                    expired_products.append(f"{on_hand} units of {product_name} expired at {exp_date}")

        conn.close()
        self.ui.lsExpProducts.addItems(expired_products)
        self.ui.lblBadge.show()
        if expired_products:
            self.ui.lblBadge.setText(str(len(expired_products)))
            self.ui.lblBadge.show()
        else:
            self.ui.lblBadge.hide()

        # --- Dynamically resize the QListWidget ---
        item_count = self.ui.lsExpProducts.count()
        if item_count > 0:
            item_height = self.ui.lsExpProducts.sizeHintForRow(0)
            total_height = item_count * item_height + 2  # +2 for borders/padding
            max_height = 91  
            self.ui.lsExpProducts.setMaximumHeight(max_height)
            self.ui.lsExpProducts.setMinimumHeight(min(total_height, max_height))
            
    def go_to_critical(self):
        crit_window = CriticalWindow()
        crit_window.critical_item_selected.connect(self.critical_item_selected.emit)
        crit_window.exec_()

    def display_sales_performance(self):
        """ Fetch sales data and display it as a linear graph """
        sales_data = fetch_sales_data()  
        self.plot_sales_graph(sales_data)  
        performance_message = self.compare_sales_performance(sales_data) 
        self.ui.lblPerformance.setText(performance_message)  
        self.display_best_selling_product() 
        
    def plot_sales_graph(self, sales_data):
        """ Plot a linear sales graph using Matplotlib """
        self.sales_canvas.figure.clear()
        
        # Extract fresh data
        x_values = list(range(len(sales_data)))
        y_values = sales_data["TotalSales"].tolist()

        # Define the month labels
        months = ["Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar", "Apr"]

        # Create new plot
        ax = self.sales_canvas.figure.add_subplot(111)
        self.sales_canvas.figure.patch.set_facecolor((1,1,1,0.75))
        ax.set_facecolor((1,1,1,0))
        ax.plot(x_values, y_values, marker="o", linestyle="-", color="b", label="Total Sales")
        
        ax.set_ylabel("Total Sales")
        ax.grid(True)
        ax.legend()

        ax.set_xticks(range(len(months)))
        ax.set_xticklabels(months)

        # Explicitly trigger re-rendering
        self.sales_canvas.figure.tight_layout()
        # Add labels to each point
        for i, value in enumerate(y_values):
            ax.text(i, value + (max(y_values) * 0.01), f"{value:,.0f}", 
                    ha='center', va='bottom', fontsize=9)
        self.sales_canvas.draw()

    def compare_sales_performance(self, sales_data):
        months = list(sales_data["Month"])

        if len(months) >= 2:
            last_month_key = months[-1]  
            second_last_month_key = months[-2]  
            
            # Fetch the sales data for these months, and ensure they are treated as float values
            last_month_sales = float(sales_data[sales_data["Month"] == last_month_key]["TotalSales"].iloc[0])
            second_last_month_sales = float(sales_data[sales_data["Month"] == second_last_month_key]["TotalSales"].iloc[0])

            # Calculate percentage change
            if second_last_month_sales > 0:
                change_percentage = ((last_month_sales - second_last_month_sales) / second_last_month_sales) * 100
            else:
                change_percentage = 100 if last_month_sales > 0 else 0 

            # Generate message
            if change_percentage > 0:
                message = f"This month's sales <span style='color: #7ff58d;'>improved</span> by {change_percentage:.2f}% compared to last month."
            elif change_percentage < 0:
                message = f"This month's sales <span style='color: #f5737c;'>declined</span> by {abs(change_percentage):.2f}% compared to last month."
            else:
                message = "Sales remained the same compared to the previous month."

            return message
        else:
            return "Insufficient data to compare sales."
        
    def display_best_selling_product(self):
        db_path = os.path.join("db", "sales_2025.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT product_name, price * quantity_sold AS total_value 
            FROM apr 
            ORDER BY total_value DESC 
            LIMIT 1
        """)
        result = cursor.fetchone()
        conn.close()

        if result:
            product_name, total_value = result
            self.ui.lblBestProduct.setText(f"{product_name} - with  <span style='color: #7ff58d;'>{total_value:,.2f}</span> in sales!")
        else:
            self.ui.lblBestProduct.setText("No sales data for this month yet.")
class ComPerformance(QMainWindow):
    go_to_inventory = pyqtSignal()
    go_to_sales = pyqtSignal()
    go_to_pos = pyqtSignal()
    go_to_account = pyqtSignal()
    go_to_dashboard = pyqtSignal()
    def __init__(self, widget=None):
        super(ComPerformance, self).__init__()
        self.ui = Ui_Comparison()
        self.ui.setupUi(self)
        self.widget = widget
        
        self.ui.cbMonth.addItems(["January","February","March","April","May",
                                  "June","July","August","September","October",
                                  "November","December"])
        self.ui.cbYear.addItems(["2025","2024","2023", "2022"])
        self.ui.cbYYear.addItems(["2025","2024","2023", "2022"])
        # Set up the Tables
        self.setupGraphTables()
        # Set layout
        if self.ui.gpPerformance.layout() is None:
            self.ui.gpPerformance.setLayout(QVBoxLayout())
        if self.ui.gpYPerformance.layout() is None:
            self.ui.gpYPerformance.setLayout(QVBoxLayout())

        self.years_plotted = []
        self.yearly_data = []

        self.ui.btnYAdd.clicked.connect(self.add_year_to_graph)
        self.ui.btnYClrGraph.clicked.connect(self.clear_year_graph)
        self.ui.btnAdd.clicked.connect(self.add_to_graph)
        self.ui.btnClrGraph.clicked.connect(self.clear_graph)
        self.ui.btnDashboard.clicked.connect(self.go_to_dashboard.emit)
        self.ui.btnInventory.clicked.connect(self.go_to_inventory.emit)
        self.ui.btnSales.clicked.connect(self.go_to_sales.emit)
        self.ui.btnPOS.clicked.connect(self.go_to_pos.emit)
        self.ui.btnAccount.clicked.connect(self.go_to_account.emit)
        
        self.colors = ['#a8c4f4', '#b8d4ac', '#b8a4d4', '#f09c9c', '#ffe49c']
        self.color_index = 0
        self.graph_data = []
        self.graph_labels = []
        
    def setupGraphTables(self):
        for table, header_text in [(self.ui.monthTable, "Months"), (self.ui.yearTable, "Years")]:
            table.setColumnCount(1)
            table.setHorizontalHeaderLabels([header_text])
            table.setRowCount(0)
            table.verticalHeader().hide()
            table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

            header = table.horizontalHeader()
            header.setStyleSheet("QHeaderView::section { background-color: #365b6d; color: white; font-size: 20px; font-weight: bold;}")
            header.setSectionResizeMode(QHeaderView.Stretch)

            # Center content by default
            table.setStyleSheet(""" QTableWidget {
                                        background-color: rgba(255, 255, 255, 50);
                                        selection-background-color: #087cd4;
                                        selection-color: white;
                                        border: none;
                                    }
                                    QHeaderView::section {
                                        background-color: rgba(255, 255, 255, 50);
                                    }
                                    QTableWidget::item {
                                        background-color: rgba(255, 255, 255, 50);
                                        text-align: center;
                                    }
                                QTableWidget::item:selected { 
                                        background-color: #087cd4;
                                        color: white;
                                    }
                                """)

            # Connect double-click signal
            if table == self.ui.monthTable:
                table.itemDoubleClicked.connect(self.removeMonthGraph)
            else:
                table.itemDoubleClicked.connect(self.removeYearGraph)
                
    def addToMonthTable(self, month: str, year: int):
        row_position = self.ui.monthTable.rowCount()
        self.ui.monthTable.insertRow(row_position)
        item = QTableWidgetItem(f"{year} {month}")
        item.setTextAlignment(Qt.AlignCenter)
        self.ui.monthTable.setItem(row_position, 0, item)

    def addToYearTable(self, year: int):
        text = str(year)
        if not self._isDuplicate(self.ui.yearTable, text):
            row = self.ui.yearTable.rowCount()
            self.ui.yearTable.insertRow(row)
            item = QTableWidgetItem(text)
            item.setTextAlignment(Qt.AlignCenter)
            self.ui.yearTable.setItem(row, 0, item)
    
    def _isDuplicate(self, table: QTableWidget, text: str) -> bool:
        for row in range(table.rowCount()):
            if table.item(row, 0).text() == text:
                return True
        return False
    def removeMonthGraph(self, item: QTableWidgetItem):
        month_year = item.text()
        row = item.row()
        self.ui.monthTable.removeRow(row)
        # Without parsing
        self.remove_from_graph(month_year)

    def removeYearGraph(self, item: QTableWidgetItem):
        year = item.text()
        row = item.row()
        self.ui.yearTable.removeRow(row)
        self.remove_year_from_graph(year)
        
    def add_to_graph(self):
        selected_month = self.ui.cbMonth.currentText()
        selected_year = self.ui.cbYear.currentText()
        label = f"{selected_year} {selected_month}" 

        # Prevent invalid months
        if selected_year == "2025":
            valid_months_2025 = ["January", "February", "March", "April"]
            if selected_month not in valid_months_2025:
                QMessageBox.warning(self, "Invalid Selection",
                                    f"Sales data for {selected_month} 2025 is not available.")
                return
            
        total_sales = self.get_total_sales(selected_year, selected_month)

        # Exists??
        if label in self.graph_labels:
            QMessageBox.warning(self, "Duplicate Entry", f"{label} is already in the graph!")
            return

        self.graph_labels.append(label)
        self.addToMonthTable(selected_month, selected_year)
        self.update_graph(label, total_sales)
        
    def calculate_total_sales(self, database, month_table):
        """Calculate total sales for the given month in the database"""
        try:
            conn = sqlite3.connect(database)
            cursor = conn.cursor()
            query = f"SELECT SUM(price * quantity_sold) FROM {month_table}"
            cursor.execute(query)
            result = cursor.fetchone()
            
            conn.close()
            
            # Return total sales value
            return result[0] if result[0] else 0 
        except sqlite3.Error as e:
            QMessageBox.warning(self, "Database Error", f"Error querying the database: {e}")
            return None
    def get_total_sales(self, year, month):
        """Calculate the total sales for a specific year and month"""
        conn = sqlite3.connect(f"db/sales_{year}.db")
        cursor = conn.cursor()

        # Month to Table
        month_table = month.lower()[:3]  

        cursor.execute(f"SELECT SUM(price * quantity_sold) FROM {month_table}")
        result = cursor.fetchone()
        total_sales = result[0] if result[0] else 0

        conn.close()
        return total_sales
    
    def update_graph(self, label, total_sales):
        if not hasattr(self, 'fig') or self.fig is None:
            self.fig, self.ax = plt.subplots()
            self.fig.tight_layout()
            self.canvas = FigureCanvas(self.fig)
            self.ui.gpPerformance.layout().addWidget(self.canvas)
            self.ax.set_xlabel("Month")
            self.ax.set_ylabel("Total Sales")
            self.ax.set_title("Monthly Sales Comparison")

        current_color = self.colors[self.color_index % len(self.colors)]
        self.color_index += 1

        self.graph_data.append((label, total_sales, current_color))

        # Clear and Redraw
        self.ax.clear()
        self.fig.patch.set_facecolor((1, 1, 1, 0))
        self.ax.set_facecolor((1, 1, 1, 0))
        labels = [label for label, _, _ in self.graph_data]
        values = [value for _, value, _ in self.graph_data]
        colors = [color for _, _, color in self.graph_data]
        self.ax.bar(labels, values, color=colors)

        # Values for Each
        bars = self.ax.bar(labels, values, color=colors)
        for bar, value in zip(bars, values):
            height = bar.get_height()
            self.ax.text(
                bar.get_x() + bar.get_width() / 2, 
                height / 2,                        
                f'{value:,.2f}',                    
                ha='center', va='center',          
                color='black', fontsize=12       
            )
        
        self.ax.set_xlabel("Month")
        self.ax.set_ylabel("Total Sales")
        self.ax.set_title("Monthly Sales Comparison")
        self.canvas.draw()

    def remove_from_graph(self, month_year: str):
        index_to_remove = None
        for i, (label, _, _) in enumerate(self.graph_data):
            if label == month_year:  # Match the exact format "2025 January"
                index_to_remove = i
                break
        if index_to_remove is not None:
            # Remove the data from graph
            self.graph_data.pop(index_to_remove)
            self.graph_labels.remove(month_year)
            self.redraw_graph()  # Redraw the graph
        else:
            print(f"No graph found for: {month_year}")
    def redraw_graph(self):
        """Redraw the graph after removing an entry"""
        self.ax.clear()  # Clear existing graph

        # Redraw bars for remaining data
        labels = [label for label, _, _ in self.graph_data]
        values = [value for _, value, _ in self.graph_data]
        colors = [color for _, _, color in self.graph_data]
        bars = self.ax.bar(labels, values, color=colors)

        # Add the value labels inside each bar
        for bar, value in zip(bars, values):
            height = bar.get_height()
            self.ax.text(
                bar.get_x() + bar.get_width() / 2,  # X position: center of the bar
                height / 2,                         # Y position: middle of the bar
                f'{value:,.2f}',                     # Format the value
                ha='center', va='center',          # Center align horizontally and vertically
                color='black', fontsize=12         # Style
            )

        self.ax.set_xlabel("Month")
        self.ax.set_ylabel("Total Sales")
        self.ax.set_title("Monthly Sales Comparison")
        self.canvas.draw()
    def clear_graph(self):
        """Clear the graph and the list view"""
        if hasattr(self, 'ax'):
            self.ax.clear()
            self.canvas.draw()

        self.graph_data.clear()
        self.graph_labels.clear()

        # Clear the table
        self.ui.monthTable.setRowCount(0)
        
    def add_year_to_graph(self):
        year = self.ui.cbYYear.currentText()
        if year in self.years_plotted:
            QMessageBox.warning(self, "Duplicate Year", f"{year} is already added to the graph!")
            return
        db_path = f"db/sales_{year}.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        valid_months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun',
                        'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
        sales = []
        available_months = []
        for short_month in valid_months:
            try:
                cursor.execute(f"SELECT SUM(price * quantity_sold) FROM {short_month}")
                result = cursor.fetchone()
                total = result[0] if result[0] else 0
                sales.append(total)
                available_months.append(short_month.capitalize())  # 'Jan', 'Feb', etc.
            except sqlite3.OperationalError:
                # This table doesn't exist (e.g., only jan to apr in 2025)
                break
        conn.close()
        # Store both year and data
        self.years_plotted.append(year)
        self.addToYearTable(year)
        self.yearly_data.append((year, sales, available_months))
        self.update_year_graph()
        
    def update_year_graph(self):
        if not hasattr(self, 'y_fig') or self.y_fig is None:
            self.y_fig, self.y_ax = plt.subplots()
            self.y_fig.tight_layout()
            self.y_canvas = FigureCanvas(self.y_fig)
            self.ui.gpYPerformance.layout().addWidget(self.y_canvas)
            self.y_ax.set_title("Yearly Sales Comparison")
            self.y_ax.set_xlabel("Month")
            self.y_ax.set_ylabel("Total Sales")

        self.y_ax.clear()
        self.y_fig.patch.set_facecolor((1, 1, 1, 0))
        self.y_ax.set_facecolor((1, 1, 1, 0.75))
        
        for i, (year, sales, months) in enumerate(self.yearly_data):
            color = self.colors[i % len(self.colors)]
            self.y_ax.plot(months, sales, label=year, marker='o', color=color)
            for x, y in zip(months, sales):
                self.y_ax.text(x, y, f'{y:,.0f}', ha='center', va='bottom', fontsize=8)

        self.y_ax.set_title("Yearly Sales Comparison")
        self.y_ax.set_xlabel("Month")
        self.y_ax.set_ylabel("Total Sales")
        self.y_ax.legend()
        self.y_canvas.draw()
        
    def remove_year_from_graph(self, year: str):
        # Loop through yearly data and remove corresponding year data
        if year in self.years_plotted:
            index = self.years_plotted.index(year)
            self.years_plotted.pop(index)
            self.yearly_data.pop(index)
            self.update_year_graph()  # Redraw the year graph
        else:
            print(f"No year found in the graph: {year}")
        
    def clear_year_graph(self):
        if hasattr(self, 'y_ax'):
            self.y_ax.clear()  # Clear the year graph
            self.y_canvas.draw()

        # Clear the yearTable
        self.ui.yearTable.setRowCount(0)
        self.years_plotted.clear()
        self.yearly_data.clear()
class CriticalWindow(QDialog):     
    critical_item_selected = pyqtSignal(str)
    def __init__(self, widget=None): 
        super(CriticalWindow, self).__init__()
        self.ui = Ui_criticalItems()
        self.ui.setupUi(self)
        self.populate_crit_table()
        self.ui.btnClose.clicked.connect(self.close)
        self.ui.tabCritical.itemDoubleClicked.connect(self.on_critical_item_clicked)
        
    def populate_crit_table(self):
        # Get DB Connection
        db_path = os.path.join("db", "inventory_db.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT description, unit, on_hand FROM inventory WHERE on_hand <= rop
            """)
        critItems = cursor.fetchall()
        self.ui.tabCritical.clear()
        
        # Set up the table
        self.ui.tabCritical.setRowCount(len(critItems)) 
        self.ui.tabCritical.setColumnCount(3)
        self.ui.tabCritical.verticalHeader().hide()
        
        # Set headers for the table
        headers = ["Critical Items", "Unit", "On Hand"]
        self.ui.tabCritical.setHorizontalHeaderLabels(headers)
        header = self.ui.tabCritical.horizontalHeader()
        header.setStyleSheet("QHeaderView::section { background-color: #365b6d; color: white; font-size: 20px; font-weight: bold;}")
        header.setSectionResizeMode(QHeaderView.Stretch)
        self.ui.tabCritical.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # Populate the table with the data
        for row, item in enumerate(critItems):
            description, unit, on_hand = item

            desc_item = QTableWidgetItem(str(description))
            desc_item.setTextAlignment(Qt.AlignCenter)

            unit_item = QTableWidgetItem(str(unit))
            unit_item.setTextAlignment(Qt.AlignCenter)

            on_hand_item = QTableWidgetItem(str(on_hand))
            on_hand_item.setTextAlignment(Qt.AlignCenter)

            self.ui.tabCritical.setItem(row, 0, desc_item)
            self.ui.tabCritical.setItem(row, 1, unit_item)
            self.ui.tabCritical.setItem(row, 2, on_hand_item)    
                 
        self.ui.tabCritical.resizeRowsToContents()
        conn.close()
    def on_critical_item_clicked(self, item):
        row = item.row()
        description_item = self.ui.tabCritical.item(row, 0)
        if description_item:
            description = description_item.text()
            self.critical_item_selected.emit(description)
            self.close()  # Close the CriticalWindow
class Inventory(QMainWindow):
    go_to_dashboard = pyqtSignal()
    go_to_sales = pyqtSignal()
    go_to_pos = pyqtSignal()
    go_to_account = pyqtSignal()
    expiredCheckRequested = pyqtSignal()
    def __init__(self, widget=None):
        super(Inventory, self).__init__()
        self.ui = Ui_inventoryManagement()
        self.ui.setupUi(self)
        self.widget = widget
        self.populate_ingredients()
        self.populate_products()
        self.ui.tabWidget.setCurrentIndex(0)
        self.ui.tabIngredientTable.itemDoubleClicked.connect(self.restock_ROP)
   
        self.ui.btnRestock.clicked.connect(self.restock)
        self.ui.btnWastage.clicked.connect(self.declare_wastage)
        self.ui.btnAddProduct.clicked.connect(self.addProduct)
        self.ui.btnDashboard.clicked.connect(self.go_to_dashboard.emit)
        self.ui.btnSales.clicked.connect(self.go_to_sales.emit)
        self.ui.btnPOS.clicked.connect(self.go_to_pos.emit)
        self.ui.btnAccount.clicked.connect(self.go_to_account.emit)
    
    def populate_ingredients(self):
        db_path = os.path.join("db", "inventory_db.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
 
        cursor.execute("""
            SELECT inventory_id, description, brand, unit, on_hand, rop
            FROM inventory
        """)
        inventory_items = cursor.fetchall()
        # Set Table
        self.ui.tabIngredientTable.setRowCount(len(inventory_items)) 
        self.ui.tabIngredientTable.setColumnCount(6)
        self.ui.tabIngredientTable.verticalHeader().hide()
        # Set Headers
        headers = ["Inventory ID", "Description", "Brand", "Unit", "On Hand", "ROP"]
        self.ui.tabIngredientTable.setHorizontalHeaderLabels(headers)
        header = self.ui.tabIngredientTable.horizontalHeader()
        header.setStyleSheet("QHeaderView::section { background-color: #365b6d; color: white; font-size: 20px; font-weight: bold;}")
        header.setSectionResizeMode(QHeaderView.Stretch)
        # Set Table to Read-Only
        self.ui.tabIngredientTable.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.ui.tabIngredientTable.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        # Populate the table with the data
        for row, item in enumerate(inventory_items):
            inventory_id, description, brand, unit, on_hand, rop = item
            # Safe type conversion
            on_hand = int(on_hand) if on_hand is not None else 0
            rop = int(rop) if rop is not None else 0
            # Prepare the row values (excluding rop from the table display)
            row_values = [inventory_id, description, brand, unit, on_hand, rop]
            # Loop through each column and insert items
            for col, value in enumerate(row_values):
                table_item = QTableWidgetItem(str(value))
                table_item.setTextAlignment(Qt.AlignCenter)
                # ROP Checker
                if on_hand <= rop:
                    table_item.setForeground(QColor("red"))
                    table_item.setBackground(QColor("#f4f4ec"))

                self.ui.tabIngredientTable.setItem(row, col, table_item)
        self.ui.tabIngredientTable.resizeRowsToContents()
        conn.close()
        
    def populate_products(self):
        db_path = os.path.join("db", "product_db.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT product_id, product_name, on_hand, exp_date FROM products_on_hand")
        products = cursor.fetchall()
        self.ui.tabProductTable.setRowCount(len(products)) 
        self.ui.tabProductTable.setColumnCount(4)
        self.ui.tabProductTable.verticalHeader().hide()
        headers = ["Product ID", "Name of Product", "On Hand", "Expiry Date (dd-mm-yy)"]
        self.ui.tabProductTable.setHorizontalHeaderLabels(headers)
        header = self.ui.tabProductTable.horizontalHeader()
        header.setStyleSheet("QHeaderView::section { background-color: #365b6d; color: white; font-size: 20px; font-weight: bold;}")
        header.setSectionResizeMode(QHeaderView.Stretch)
        self.ui.tabProductTable.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.ui.tabProductTable.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        for row, item in enumerate(products):
            for col, value in enumerate(item):
                table_item = QTableWidgetItem(str(value))
                table_item.setTextAlignment(Qt.AlignCenter)
                self.ui.tabProductTable.setItem(row, col, table_item)
        self.ui.tabProductTable.resizeRowsToContents()
        conn.close()    
    
    def focus_on_item(self, description):
        table = self.ui.tabIngredientTable

        # Clear any previous selection
        table.clearSelection()

        # Loop through all rows in the table
        for row in range(table.rowCount()):
            item = table.item(row, 1)
            
            if item and item.text() == description:
                table.selectRow(row)
                table.setStyleSheet("QTableWidget::item:selected { background-color: #087cd4; color: white; }")
                
                table.scrollToItem(item, QAbstractItemView.PositionAtCenter)
                break
    
    def restock_ROP(self, item):
        row = item.row()
        first_item = self.ui.tabIngredientTable.item(row, 0)

        if first_item and first_item.foreground().color() == QColor("red"):
            # Get inventory_id and description from the row
            inventory_id_item = self.ui.tabIngredientTable.item(row, 0)
            description_item = self.ui.tabIngredientTable.item(row, 1)
            unit_item = self.ui.tabIngredientTable.item(row, 3)

            inventory_id = inventory_id_item.text() if inventory_id_item else ""
            description = description_item.text() if description_item else ""
            unit = unit_item.text() if description_item else ""
            
            # Open the AddCritical dialog and pass inventory_id & description
            conn = sqlite3.connect(os.path.join("db", "inventory_db.db"))
            add_critical_window = AddCritical(conn, inventory_id, description, unit)
            
            # Connect the signal to refresh after restocking
            add_critical_window.restockConfirmed.connect(self.populate_ingredients)

            add_critical_window.exec_()
            conn.close()
    
    def restock(self):
        restock_window = Restock()
        restock_window.restockConfirmed.connect(self.populate_ingredients)
        restock_window.exec_()
        
    def declare_wastage(self):
        wastage_window = DecWastage()
        wastage_window.restockConfirmed.connect(self.populate_ingredients)
        wastage_window.exec_()
        
    def addProduct(self):
        addProduct_window = PrRestock()
        addProduct_window.restockConfirmed.connect(self.populate_products)
        addProduct_window.restockConfirmed.connect(self.populate_ingredients)
        addProduct_window.expiredCheckRequested.connect(self.expiredCheckRequested)
        addProduct_window.exec_()
class AddCritical(QDialog):
    restockConfirmed = pyqtSignal()
    def __init__(self, conn, inventory_id=None, description=None, unit=None):
        super(AddCritical, self).__init__()
        self.ui = Ui_AddCritical()
        self.ui.setupUi(self)
        self.db_connection = conn
        self.inventory_id = inventory_id 
        self.unit = unit
        self.ui.lblCriticalItem.setText(f"{inventory_id} - {description}")
        self.ui.lblAmount.setText(f"Amount to add (in {unit})")
        # Connect Buttons
        self.ui.buttonBox.accepted.connect(self.confirm)
        self.ui.buttonBox.rejected.connect(self.close)
        
        
    def confirm(self):
        try:
            amount_text = self.ui.teAmount.toPlainText()
            # Validate amount is provided
            if not amount_text.strip():
                QMessageBox.warning(self, "Input Error", "Amount cannot be empty.")
                return
            # Convert amount to float
            amount = float(amount_text)
            cursor = self.db_connection.cursor()
            # Fetch current on_hand
            cursor.execute("""
                SELECT on_hand FROM inventory WHERE inventory_id = ?
            """, (self.inventory_id,))
            result = cursor.fetchone()
            if result is None:
                QMessageBox.critical(self, "Error", "Item not found in inventory.")
                return
            current_on_hand = result[0] if result[0] is not None else 0
            # Calculate new on_hand
            new_on_hand = current_on_hand + amount
            # Update the on_hand in inventory table
            cursor.execute("""
                UPDATE inventory
                SET on_hand = ?
                WHERE inventory_id = ?
            """, (new_on_hand, self.inventory_id))
            self.db_connection.commit()
            QMessageBox.information(self, "Success", f"Stock updated! \nNew On Hand: {new_on_hand}")
            # Emit the signal to refresh the inventory table
            self.restockConfirmed.emit()

            # Close the dialog
            self.accept()

        except ValueError:
            QMessageBox.critical(self, "Input Error", "Please enter a valid numerical amount.")
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"An error occurred: {e}")    
class Restock(QDialog):
    restockConfirmed = pyqtSignal()     
    def __init__(self):
        super(Restock, self).__init__()
        self.ui = Ui_Restock()
        self.ui.setupUi(self)
        self.populate_restock_table()
        # Connect Buttons
        self.ui.btnAdd.clicked.connect(self.add)
        self.ui.btnAddNew.clicked.connect(self.addNew)
        self.ui.btnRemove.clicked.connect(self.removeItem)
        self.ui.btnConfirm.clicked.connect(self.confirmItems)
        self.ui.btnCancel.clicked.connect(self.close)
        self.add_shadow_effect()
    # GUI
    def add_shadow_effect(self):
        for entity in self.findChildren(QPushButton):
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(5)
            shadow.setOffset(1, 1)
            shadow.setColor(QColor(0, 0, 0, 160))
            entity.setGraphicsEffect(shadow)
    def connect_rsDB(self):
        db_path = os.path.join("db", "restock_db.db")
        return sqlite3.connect(db_path)
        
    def populate_restock_table(self):
        conn = self.connect_rsDB()
        cursor = conn.cursor()

        # Fetch Items
        cursor.execute("SELECT inventory_id, description, brand, unit, amount FROM restock")
        restock_items = cursor.fetchall()

        self.ui.tabRestockTable.setRowCount(len(restock_items)) 
        self.ui.tabRestockTable.setColumnCount(5)
        self.ui.tabRestockTable.verticalHeader().hide()
        headers = ["Inventory ID", "Description", "Brand", "Unit", "Amount"]
        self.ui.tabRestockTable.setHorizontalHeaderLabels(headers)
        header = self.ui.tabRestockTable.horizontalHeader()
        header.setStyleSheet("QHeaderView::section { background-color: #365b6d; color: white; font-size: 20px; font-weight: bold;}")
        header.setSectionResizeMode(QHeaderView.Stretch)

        # Populate the table with the data
        for row, item in enumerate(restock_items):
            for col, value in enumerate(item):
                table_item = QTableWidgetItem(str(value))
                table_item.setTextAlignment(Qt.AlignCenter)
                self.ui.tabRestockTable.setItem(row, col, table_item)
                                             
        # Adjust column widths to fit content
        self.ui.tabRestockTable.resizeRowsToContents()
        conn.close()
    
    def add(self):
        conn = self.connect_rsDB()
        add_existing_window = AddExisting(conn)
        add_existing_window.exec_()
        conn.close()
        self.populate_restock_table()
    
    def addNew(self):
        conn = self.connect_rsDB()
        add_item_window = AddItem(conn) 
        add_item_window.exec_()
        conn.close()
        self.populate_restock_table()
        
    def removeItem(self):
        # Get selected items
        selected_items = self.ui.tabRestockTable.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Selection Error", "No item selected. Please select a row to delete.")
            return

        # Identify Unique
        rows_to_delete = sorted(set(item.row() for item in selected_items), reverse=True)

        reply = QMessageBox.question(self, "Remove Item", "Are you sure you want to remove the selected items?",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.No:
            return

        conn = self.connect_rsDB()
        cursor = conn.cursor()

        try:
            for row in rows_to_delete:
                inventory_item = self.ui.tabRestockTable.item(row, 0) 
                if inventory_item:
                    inventory_id = inventory_item.text()
                    cursor.execute("DELETE FROM restock WHERE inventory_id = ?", (inventory_id,))
                    self.ui.tabRestockTable.removeRow(row)
                else:
                    QMessageBox.warning(self, "Missing Data", f"Could not find Inventory ID for row {row + 1}.")

            conn.commit()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to remove item(s): {e}")
        finally:
            conn.close()

        # Refresh Table
        self.populate_restock_table()
        
    def confirmItems(self):
        inv_path = os.path.join("db", "inventory_db.db")
        inv_conn = sqlite3.connect(inv_path)
        inv_cursor = inv_conn.cursor()
        res_conn = self.connect_rsDB()
        res_cursor = res_conn.cursor()
        # Fetch Entries
        res_cursor.execute("SELECT * FROM restock")
        restock_entries = res_cursor.fetchall()
        for restock_entry in restock_entries:
            inventory_id, description, brand, unit, amount, rop = restock_entry
            inv_cursor.execute("SELECT on_hand FROM inventory WHERE inventory_id = ?", (inventory_id,))
            existing_entry = inv_cursor.fetchone()
            # If Exists??
            if existing_entry:
                new_on_hand = existing_entry[0] + amount
                inv_cursor.execute("UPDATE inventory SET on_hand = ? WHERE inventory_id = ?", (new_on_hand, inventory_id))
            else:
                inv_cursor.execute("INSERT INTO inventory (inventory_id, description, brand, unit, on_hand, rop) VALUES (?, ?, ?, ?, ?, ?)", 
                            (inventory_id, description, brand, unit, amount, rop))
        inv_conn.commit()
        inv_conn.close()
        # Empty Restock      
        res_cursor.execute("DELETE FROM restock")
        res_conn.commit()
        res_conn.close()
        
        self.restockConfirmed.emit()
        self.close()
        QMessageBox.information(self, "Success", "Item(s) added successfully.")
class PrRestock(QDialog):
    restockConfirmed = pyqtSignal() 
    expiredCheckRequested = pyqtSignal()    
    def __init__(self):
        super(PrRestock, self).__init__()
        self.ui = Ui_PrRestock()
        self.ui.setupUi(self)
        self.populate_restock_table()
        # Connect Buttons
        self.ui.btnAdd.clicked.connect(self.add)
        self.ui.btnAddNew.clicked.connect(self.addNew)
        self.ui.btnRemove.clicked.connect(self.removeProduct)
        self.ui.btnConfirm.clicked.connect(self.confirmProducts)
        self.ui.btnCancel.clicked.connect(self.close)
        self.add_shadow_effect()
    # GUI
    def add_shadow_effect(self):
        for entity in self.findChildren(QPushButton):
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(5)
            shadow.setOffset(1, 1)
            shadow.setColor(QColor(0, 0, 0, 160))
            entity.setGraphicsEffect(shadow)
    def connect_rsDB(self):
        db_path = os.path.join("db", "prrestock_db.db")
        return sqlite3.connect(db_path)
        
    def populate_restock_table(self):
        conn = self.connect_rsDB()
        cursor = conn.cursor()
        cursor.execute("SELECT product_id, product_name, amount, exp_date FROM restock_product")
        restock_products = cursor.fetchall()
        self.ui.tabPrRestockTable.setRowCount(len(restock_products)) 
        self.ui.tabPrRestockTable.setColumnCount(4)
        self.ui.tabPrRestockTable.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.ui.tabPrRestockTable.verticalHeader().hide()
        headers = ["Product ID", "Product Name", "Amount", "Expiration Date"]
        self.ui.tabPrRestockTable.setHorizontalHeaderLabels(headers)
        header = self.ui.tabPrRestockTable.horizontalHeader()
        header.setStyleSheet("QHeaderView::section { background-color: #365b6d; color: white; font-size: 20px; font-weight: bold;}")
        header.setSectionResizeMode(QHeaderView.Stretch)
        for row, item in enumerate(restock_products):
            for col, value in enumerate(item):
                table_item = QTableWidgetItem(str(value))
                table_item.setTextAlignment(Qt.AlignCenter)
                self.ui.tabPrRestockTable.setItem(row, col, table_item)
        self.ui.tabPrRestockTable.resizeRowsToContents()
        conn.close()
    
    def add(self):
        conn = self.connect_rsDB()
        add_existing_window = AddPrExisting(conn)
        add_existing_window.exec_()
        conn.close()
        self.populate_restock_table()
        
    def addNew(self):
        conn = self.connect_rsDB()
        add_item_window = AddPrNew(conn) 
        add_item_window.exec_()
        conn.close()
        self.populate_restock_table()
    def removeProduct(self):
        # Get selected items
        selected_items = self.ui.tabPrRestockTable.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Selection Error", "No item selected. Please select a row to delete.")
            return
        # Identify Unique
        rows_to_delete = sorted(set(item.row() for item in selected_items), reverse=True)
        reply = QMessageBox.question(self, "Remove Item", "Are you sure you want to remove the selected items?",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.No:
            return
        conn = self.connect_rsDB()
        cursor = conn.cursor()
        try:
            for row in rows_to_delete:
                product_item = self.ui.tabPrRestockTable.item(row, 0) 
                if product_item:
                    product_id = product_item.text()
                    cursor.execute("DELETE FROM restock_product WHERE product_id = ?", (product_id,))

                    self.ui.tabPrRestockTable.removeRow(row)
                else:
                    QMessageBox.warning(self, "Missing Data", f"Could not find Product ID for row {row + 1}.")
            conn.commit()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to remove item(s): {e}")
        finally:
            conn.close()
        # Refresh Table
        self.populate_restock_table()
        
    def confirmProducts(self):
        pr_path = os.path.join("db", "product_db.db")
        pr_conn = sqlite3.connect(pr_path)
        pr_cursor = pr_conn.cursor()

        res_conn = self.connect_rsDB()
        res_cursor = res_conn.cursor()

        inv_path = os.path.join("db", "inventory_db.db")
        inv_conn = sqlite3.connect(inv_path)
        inv_cursor = inv_conn.cursor()

        ing_path = os.path.join("db", "ingredients_db.db")
        ing_conn = sqlite3.connect(ing_path)
        ing_cursor = ing_conn.cursor()

        # Fetch Entries
        res_cursor.execute("SELECT * FROM restock_product")
        restock_entries = res_cursor.fetchall()

        for restock_entry in restock_entries:
            product_id, product_name, amount, exp_date = restock_entry

            # Update
            pr_cursor.execute("SELECT on_hand FROM products_on_hand WHERE product_id = ?", (product_id,))
            existing_entry = pr_cursor.fetchone()

            if existing_entry:
                new_on_hand = existing_entry[0] + amount
                pr_cursor.execute("UPDATE products_on_hand SET on_hand = ? WHERE product_id = ?", (new_on_hand, product_id))
                pr_cursor.execute("UPDATE products_on_hand SET exp_date = ? WHERE product_id = ?", (exp_date, product_id))
            else:
                pr_cursor.execute("INSERT INTO products_on_hand (product_id, product_name, on_hand, exp_date) VALUES (?, ?, ?, ?)", 
                            (product_id, product_name, amount, exp_date))

            # Subtract ingredients from inventory
            ing_cursor.execute(f"SELECT inventory_id, {product_id} FROM ingredients WHERE {product_id} IS NOT NULL")
            ingredient_list = ing_cursor.fetchall()

            for inventory_id, required_amount_per_unit in ingredient_list:
                if required_amount_per_unit is not None:
                    total_required = required_amount_per_unit * amount
                    inv_cursor.execute("SELECT on_hand FROM inventory WHERE inventory_id = ?", (inventory_id,))
                    inventory_entry = inv_cursor.fetchone()

                    if inventory_entry and inventory_entry[0] >= total_required:
                        new_inventory = inventory_entry[0] - total_required
                        inv_cursor.execute("UPDATE inventory SET on_hand = ? WHERE inventory_id = ?", (new_inventory, inventory_id))
                    else:
                        QMessageBox.warning(self, "Stock Warning", f"Not enough stock for ingredient {inventory_id}")

        # Commit changes
        pr_conn.commit()
        res_conn.commit()
        inv_conn.commit()
        ing_conn.commit()

        # Close connections
        pr_conn.close()
        inv_conn.close()
        ing_conn.close()

        # Clear restock table
        res_cursor.execute("DELETE FROM restock_product")
        res_conn.commit()
        res_conn.close()
        
        self.restockConfirmed.emit()
        self.expiredCheckRequested.emit()
        self.close()
        QMessageBox.information(self, "Success", "Item(s) added successfully.")
class AddExisting(QDialog):     
    def __init__(self, conn): 
        super(AddExisting, self).__init__()
        self.ui = Ui_AddExisting()
        self.ui.setupUi(self)
        self.db_connection = conn 
        self.populate_combobox()
        self.ui.cbItems.currentIndexChanged.connect(self.update_unit_label)
        self.ui.buttonBox.accepted.connect(self.confirm)
        self.ui.teAmount.textChanged.connect(self.validate_input)
        self.apply_shadow_effects()
        # Set validator for input field
        float_validator = QDoubleValidator(0.01, 1e308, 5)  # Min, Max, Decimal Number
        self.ui.teAmount.setValidator(float_validator)
    
    # GUI
    def apply_shadow_effects(self):
        for entity in self.findChildren(QLineEdit):
            self.add_shadow_effect(entity)
        for entity in self.findChildren(QPushButton):
            self.add_shadow_effect(entity)
    
    def add_shadow_effect(self, entity):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(5)
        shadow.setOffset(1, 1)
        shadow.setColor(QColor(0, 0, 0, 160))
        entity.setGraphicsEffect(shadow)
        
    def validate_input(self):
        input_text = self.ui.teAmount.text().strip()
        validator = self.ui.teAmount.validator()
        state, _, _ = validator.validate(input_text, 0)

        # Check if the input is valid
        if state != QValidator.Acceptable:
            QToolTip.showText(self.ui.teAmount.mapToGlobal(self.ui.teAmount.rect().bottomLeft()),
                          "Please enter a positive number",
                          self.ui.teAmount)
            self.ui.teAmount.setStyleSheet("border: 1px solid red; border-radius: 5px; background: white;")
        else:
            self.ui.teAmount.setToolTip("")
            self.ui.teAmount.setStyleSheet("border: 1px solid black; border-radius: 5px; background: white;")
            QToolTip.hideText()
            
    def populate_combobox(self):
        inv_path = os.path.join("db", "inventory_db.db")
        inv_conn = sqlite3.connect(inv_path)
        inv_cursor = inv_conn.cursor()
        # Fetch inventory_id, description, and brand
        inv_cursor.execute("SELECT inventory_id, description, brand, unit FROM inventory")
        self.inventory_items = inv_cursor.fetchall()
        # Clear existing items in the combo box
        self.ui.cbItems.clear()
        # Populate the combo box with formatted entries
        for item in self.inventory_items:
            inventory_id, description, brand, unit = item
            display_text = f"{inventory_id} - {description} ({brand})"
            self.ui.cbItems.addItem(display_text, inventory_id)
        inv_cursor.close()
        # Set initial unit label if there's at least one item
        if self.inventory_items:
            self.update_unit_label()
    def update_unit_label(self):
        index = self.ui.cbItems.currentIndex()
        if index >= 0:
            unit = self.inventory_items[index][3]
            self.ui.lblUnit.setText(f"(in {unit})")
        else:
            self.ui.lblUnit.setText("Unit: N/A")
    def confirm(self):
        try:
            index = self.ui.cbItems.currentIndex()
            if index < 0:
                QMessageBox.warning(self, "Selection Error", "Please select an item.")
                return
            # Retrieve selected item details
            inventory_id, description, brand, unit = self.inventory_items[index]
            amount_text = self.ui.teAmount.text()
            if not amount_text.strip():
                QMessageBox.warning(self, "Input Error", "Amount cannot be empty.")
                return
            amount = float(amount_text)  # Convert to float
            # Insert into the restock database
            cursor = self.db_connection.cursor()
            cursor.execute("""
                INSERT INTO restock (inventory_id, description, brand, unit, amount)
                VALUES (?, ?, ?, ?, ?)
            """, (inventory_id, description, brand, unit, amount))
            self.db_connection.commit()
            self.accept()
        except ValueError:
            QMessageBox.critical(self, "Input Error", "Please enter a valid numerical amount.")
        except sqlite3.IntegrityError as e:
            QMessageBox.critical(self, "Database Error", f"Failed to add item: {e}")
class DecWastage(QDialog):   
    restockConfirmed = pyqtSignal()    
    def __init__(self): 
        super(DecWastage, self).__init__()
        self.ui = Ui_decWastage()
        self.ui.setupUi(self)
        self.db_connection = sqlite3.connect(os.path.join("db", "inventory_db.db"))
        self.populate_combobox()
        self.ui.cbItems.currentIndexChanged.connect(self.update_unit_label)
        self.ui.buttonBox.accepted.connect(self.confirm)
        self.ui.teAmount.textChanged.connect(self.validate_input)
        self.apply_shadow_effects()

        float_validator = QDoubleValidator(0.01, 1e308, 5)
        self.ui.teAmount.setValidator(float_validator)

    def apply_shadow_effects(self):
        for entity in self.findChildren(QLineEdit):
            self.add_shadow_effect(entity)
        for entity in self.findChildren(QPushButton):
            self.add_shadow_effect(entity)

    def add_shadow_effect(self, entity):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(5)
        shadow.setOffset(1, 1)
        shadow.setColor(QColor(0, 0, 0, 160))
        entity.setGraphicsEffect(shadow)

    def validate_input(self):
        input_text = self.ui.teAmount.text().strip()
        validator = self.ui.teAmount.validator()
        state, _, _ = validator.validate(input_text, 0)

        if state != QValidator.Acceptable:
            QToolTip.showText(self.ui.teAmount.mapToGlobal(self.ui.teAmount.rect().bottomLeft()),
                              "Please enter a positive number",
                              self.ui.teAmount)
            self.ui.teAmount.setStyleSheet("border: 1px solid red; border-radius: 5px; background: white;")
        else:
            self.ui.teAmount.setToolTip("")
            self.ui.teAmount.setStyleSheet("border: 1px solid black; border-radius: 5px; background: white;")
            QToolTip.hideText()

    def populate_combobox(self):
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT inventory_id, description, brand, unit, on_hand FROM inventory")
        self.inventory_items = cursor.fetchall()
        self.ui.cbItems.clear()
        for item in self.inventory_items:
            inventory_id, description, brand, _, _ = item
            display_text = f"{inventory_id} - {description} ({brand})"
            self.ui.cbItems.addItem(display_text, inventory_id)
        cursor.close()
        if self.inventory_items:
            self.update_unit_label()

    def update_unit_label(self):
        index = self.ui.cbItems.currentIndex()
        if index >= 0:
            unit = self.inventory_items[index][3]
            self.ui.lblUnit.setText(f"(in {unit})")
        else:
            self.ui.lblUnit.setText("Unit: N/A")

    def confirm(self):
        try:
            index = self.ui.cbItems.currentIndex()
            if index < 0:
                QMessageBox.warning(self, "Selection Error", "Please select an item.")
                return

            inventory_id, description, brand, unit, on_hand = self.inventory_items[index]
            amount_text = self.ui.teAmount.text()
            if not amount_text.strip():
                QMessageBox.warning(self, "Input Error", "Amount cannot be empty.")
                return

            amount = float(amount_text)
            if amount > on_hand:
                QMessageBox.critical(self, "Insufficient Stock", f"Cannot declare {amount} — only {on_hand} on hand.")
                return

            cursor = self.db_connection.cursor()
            cursor.execute("""
                UPDATE inventory
                SET on_hand = on_hand - ?
                WHERE inventory_id = ?
            """, (amount, inventory_id))

            self.db_connection.commit()
            self.restockConfirmed.emit()
            QMessageBox.information(self, "Wastage Declared", f"{amount} {unit} of {description} has been subtracted.")
            self.accept()

        except ValueError:
            QMessageBox.critical(self, "Input Error", "Please enter a valid numerical amount.")
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Error: {e}")
class AddPrExisting(QDialog):     
    def __init__(self, conn): 
        super(AddPrExisting, self).__init__()
        self.ui = Ui_AddPrExisting()
        self.ui.setupUi(self)
        self.db_connection = conn 
        self.populate_combobox()
        self.ui.buttonBox.accepted.connect(self.confirm)
        self.ui.buttonBox.rejected.connect(self.reject)
        self.ui.teAmount.textChanged.connect(self.validate_input)
        self.apply_shadow_effects()
        
        self.ui.deExpDate.setDate(QDate.currentDate())
        calendar = self.ui.deExpDate.calendarWidget()
        calendar.setMinimumSize(400, 300)
        self.ui.deExpDate.setStyleSheet("""QDateEdit {
                                            background: white;
                                            border: 1px solid black;
                                            border-radius: 5px;
                                            }
                                        QCalendarWidget QToolButton {
                                                color: black;
                                                background-color: #f0f0f0;
                                                font-size: 20px;
                                            }
                                        """)
        # Set validator for the amount input field (teAmount)
        int_validator = QIntValidator(1, 2147483647)  # Min, Max
        self.ui.teAmount.setValidator(int_validator)
    
    # GUI
    def apply_shadow_effects(self):
        for entity in self.findChildren(QLineEdit):
            self.add_shadow_effect(entity)
        for entity in self.findChildren(QPushButton):
            self.add_shadow_effect(entity)
    
    def add_shadow_effect(self, entity):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(5)
        shadow.setOffset(1, 1)
        shadow.setColor(QColor(0, 0, 0, 160))
        entity.setGraphicsEffect(shadow)
        
    def validate_input(self):
        input_text = self.ui.teAmount.text().strip()
        validator = self.ui.teAmount.validator()
        state, _, _ = validator.validate(input_text, 0)

        # Check if the input is valid
        if state != QValidator.Acceptable:
            QToolTip.showText(self.ui.teAmount.mapToGlobal(self.ui.teAmount.rect().bottomLeft()),
                          "Please enter a positive, whole number",
                          self.ui.teAmount)
            self.ui.teAmount.setStyleSheet("border: 1px solid red; border-radius: 5px; background: white;")
        else:
            self.ui.teAmount.setToolTip("")
            self.ui.teAmount.setStyleSheet("border: 1px solid black; border-radius: 5px; background: white;")
            QToolTip.hideText()
            
    def populate_combobox(self):
        pr_path = os.path.join("db", "product_db.db")
        pr_conn = sqlite3.connect(pr_path)
        pr_cursor = pr_conn.cursor()
        # Fetch product_id, product_name
        pr_cursor.execute("SELECT product_id, product_name FROM products_on_hand")
        self.product_items = pr_cursor.fetchall()
        # Clear existing items in the combo box
        self.ui.cbProducts.clear()
        # Populate the combo box with formatted entries
        for item in self.product_items:
            product_id, product_name = item
            display_text = f"{product_id} - {product_name}"
            self.ui.cbProducts.addItem(display_text, product_id)
        pr_cursor.close()
    def confirm(self):
        try:
            index = self.ui.cbProducts.currentIndex()
            if index < 0:
                QMessageBox.warning(self, "Selection Error", "Please select an item.")
                return

            product_id, product_name = self.product_items[index]
            amount_text = self.ui.teAmount.text()
            if not amount_text.strip():
                QMessageBox.warning(self, "Input Error", "Amount cannot be empty.")
                return
            amount = int(amount_text)
            newExpDate = self.ui.deExpDate.date().toString("dd-MM-yy")

            # Get ingredients required for this product
            ingredients_path = os.path.join("db", "ingredients_db.db")
            inventory_path = os.path.join("db", "inventory_db.db")
            ing_conn = sqlite3.connect(ingredients_path)
            inv_conn = sqlite3.connect(inventory_path)

            ing_cursor = ing_conn.cursor()
            inv_cursor = inv_conn.cursor()

            ing_cursor.execute("SELECT inventory_id, description, [{}] FROM ingredients WHERE [{}] > 0".format(product_id, product_id))
            ingredients_needed = ing_cursor.fetchall()

            insufficient = []
            critical_after = []

            for inv_id, name, needed_per_unit in ingredients_needed:
                total_needed = needed_per_unit * amount
                inv_cursor.execute("SELECT on_hand, rop FROM inventory WHERE inventory_id = ?", (inv_id,))
                row = inv_cursor.fetchone()
                if not row:
                    continue
                on_hand, rop = row

                if on_hand < total_needed:
                    insufficient.append((inv_id, name, on_hand, total_needed))
                elif (on_hand - total_needed) <= rop:
                    critical_after.append((inv_id, name, on_hand, rop, on_hand - total_needed))

            if insufficient:
                self.show_stock_warning("The above items are insufficient to produce {} units of {}".format(amount, product_name), insufficient, is_insufficient=True)
                return
            elif critical_after:
                self.show_stock_warning("The above items will reach critical point after your production", critical_after, is_insufficient=False)
                return

            # If no issues, proceed
            cursor = self.db_connection.cursor()
            cursor.execute("""
                INSERT INTO restock_product (product_id, product_name, amount, exp_date)
                VALUES (?, ?, ?, ?)
            """, (product_id, product_name, amount, newExpDate))
            self.db_connection.commit()
            self.accept()

        except ValueError:
            QMessageBox.critical(self, "Input Error", "Please enter a valid numerical amount.")
        except sqlite3.IntegrityError as e:
            QMessageBox.critical(self, "Database Error", f"Failed to add item: {e}")
            
    def show_stock_warning(self, message, items, is_insufficient=True):
        warning_type = "insufficient" if is_insufficient else "critical"
        dialog = StockWarning(warning_type)
        dialog.ui.lblWarning.setText(message)
        dialog.proceed_with_production.connect(self.confirm_add_to_prrestock)

        tab = dialog.ui.tabItems
        tab.setRowCount(len(items))
        tab.setEditTriggers(QAbstractItemView.NoEditTriggers)
        tab.verticalHeader().hide()
        if is_insufficient:
            headers = ["Inventory ID", "Name", "On Hand", "Needed"]
            tab.setColumnCount(4)
        else:
            headers = ["Inventory ID", "Name", "On Hand", "ROP", "Post Production"]
            tab.setColumnCount(5)

        tab.setHorizontalHeaderLabels(headers)
        header = tab.horizontalHeader()
        header.setStyleSheet("QHeaderView::section { background-color: #365b6d; color: white; font-size: 20px; font-weight: bold; }")
        header.setSectionResizeMode(QHeaderView.Stretch)

        for row, item in enumerate(items):
            for col, value in enumerate(item):
                cell = QTableWidgetItem(str(value))
                cell.setTextAlignment(Qt.AlignCenter)
                tab.setItem(row, col, cell)

            # Color highlighting
            if is_insufficient:
                for col in range(len(item)):
                    tab.item(row, col).setBackground(QColor("#ffcccc"))  # light red
            else:
                for col in range(len(item)):
                    tab.item(row, col).setBackground(QColor("#fff2cc"))  # light yellow

        tab.resizeRowsToContents()
        dialog.exec()
        
    def confirm_add_to_prrestock(self):
        try:
            index = self.ui.cbProducts.currentIndex()
            if index < 0:
                return
            product_id, product_name = self.product_items[index]
            amount = int(self.ui.teAmount.text())
            newExpDate = self.ui.deExpDate.date().toString("dd/MM/yy")

            cursor = self.db_connection.cursor()
            cursor.execute("""
                INSERT INTO restock_product (product_id, product_name, amount, exp_date)
                VALUES (?, ?, ?, ?)
            """, (product_id, product_name, amount, newExpDate))
            self.db_connection.commit()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add to restock: {e}")
class StockWarning(QDialog):     
    proceed_with_production = pyqtSignal()
    def __init__(self, warning_type):
        super(StockWarning, self).__init__()
        self.ui = Ui_stockWarning()
        self.ui.setupUi(self)
        self.warning_type = warning_type  # "insufficient" or "critical"

        self.ui.btnClose.clicked.connect(self.reject)
        self.ui.btnAccept.clicked.connect(self.handle_accept)

    def handle_accept(self):
        if self.warning_type == "critical":
            self.proceed_with_production.emit()
        self.accept()
class AddItem(QDialog):     
    def __init__(self, conn):
        super(AddItem, self).__init__()
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.db_connection = conn
        # Connect buttons
        self.ui.buttonBox.accepted.connect(self.confirm)
        self.ui.teAmount.textChanged.connect(self.validate_amount)
        self.ui.teROP.textChanged.connect(self.validate_rop)
        self.apply_shadow_effects()
        # Set validator for input fields
        self.ui.teAmount.setValidator(QDoubleValidator(0.00001,1e308, 5))
        self.ui.teROP.setValidator(QDoubleValidator(0,1e308, 5))
    
    # GUI
    def apply_shadow_effects(self):
        for entity in self.findChildren(QLineEdit):
            self.add_shadow_effect(entity)
        for entity in self.findChildren(QPushButton):
            self.add_shadow_effect(entity)
    
    def add_shadow_effect(self, entity):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(5)
        shadow.setOffset(1, 1)
        shadow.setColor(QColor(0, 0, 0, 160))
        entity.setGraphicsEffect(shadow)
        
    def validate_amount(self):
        input_text = self.ui.teAmount.text().strip()
        validator = self.ui.teAmount.validator()
        state, _, _ = validator.validate(input_text, 0)

        # Check if the input is valid
        if state != QValidator.Acceptable:
            QToolTip.showText(self.ui.teAmount.mapToGlobal(self.ui.teAmount.rect().bottomLeft()),
                          "Please enter a positive number, your initial qauntity to add",
                          self.ui.teAmount)
            self.ui.teAmount.setStyleSheet("border: 1px solid red; border-radius: 5px; background: white;")
        else:
            self.ui.teAmount.setToolTip("")
            self.ui.teAmount.setStyleSheet("border: 1px solid black; border-radius: 5px; background: white;")
            QToolTip.hideText()
        
    def validate_rop(self):
        input_text = self.ui.teROP.text().strip()
        validator = self.ui.teROP.validator()
        state, _, _ = validator.validate(input_text, 0)

        # Check if the input is valid
        if state != QValidator.Acceptable:
            QToolTip.showText(self.ui.teROP.mapToGlobal(self.ui.teROP.rect().bottomLeft()),
                          "Please enter a positive number, the amount the item is considered \"Critical\"",
                          self.ui.teROP)
            self.ui.teROP.setStyleSheet("border: 1px solid red; border-radius: 5px; background: white;")
        else:
            self.ui.teROP.setToolTip("")
            self.ui.teROP.setStyleSheet("border: 1px solid black; border-radius: 5px; background: white;")
            QToolTip.hideText()
    def confirm(self):
        try:
            inventory_id = self.ui.teInvID.text()
            description = self.ui.teDescription.text()
            brand = self.ui.teBrand.text()
            unit = self.ui.teUnit.text()
            amount = float(self.ui.teAmount.text())
            rop = float(self.ui.teROP.text())

            # Ensure Inventory ID is provided or unique
            if not inventory_id:
                QMessageBox.warning(self, "Input Error", "Inventory ID is required.")
                return

            # Insert into database
            cursor = self.db_connection.cursor()
            cursor.execute("""
            INSERT INTO restock (inventory_id, description, brand, unit, amount, rop)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (inventory_id, description, brand, unit, amount, rop))
            self.db_connection.commit()
            self.accept() 
            
        except ValueError:
            QMessageBox.critical(self, "Input Error", "Please ensure all numerical fields have valid numbers.")
        except sqlite3.IntegrityError as e:
            QMessageBox.critical(self, "Database Error", f"Failed to add item: {e}")
class AddPrNew(QDialog):     
    def __init__(self, conn):
        super(AddPrNew, self).__init__()
        self.ui = Ui_addPrNew()
        self.ui.setupUi(self)
        self.db_connection = conn
        self.populate_combobox()
        self.populate_table()
        # Connect buttons
        self.ui.btnCancel.clicked.connect(self.close)
        self.ui.btnAdd.clicked.connect(self.add)
        self.ui.btnImage.clicked.connect(self.add_image)
        self.ui.btnConfirm.clicked.connect(self.confirm)
        self.ui.btnRemove.clicked.connect(self.remove)
    def populate_combobox(self):
        inv_path = os.path.join("db", "inventory_db.db")
        inv_conn = sqlite3.connect(inv_path)
        inv_cursor = inv_conn.cursor()
        inv_cursor.execute("SELECT inventory_id, description, unit FROM inventory")
        self.inventory_items = inv_cursor.fetchall()
        self.ui.cbItems.clear()
        for item in self.inventory_items:
            inventory_id, description, unit = item
            display_text = f"{inventory_id} - {description} (in {unit})"
            self.ui.cbItems.addItem(display_text, inventory_id) 
        inv_cursor.close()
    def populate_table(self):
        data_path = os.path.join("db", "prrestock_db.db")
        data_conn = sqlite3.connect(data_path)
        data_cursor = data_conn.cursor()
        # Fetch inventory_id, description, and amount
        data_cursor.execute("""
            SELECT inventory_id, description, amount
            FROM new_product_data
        """)
        prData = data_cursor.fetchall()
        # Set up the table
        self.ui.tabPrIngredients.setRowCount(len(prData)) 
        self.ui.tabPrIngredients.setColumnCount(3)
        self.ui.tabPrIngredients.verticalHeader().hide()
        # Set headers for the table
        headers = ["Inventory ID", "Description", "Amount"]
        self.ui.tabPrIngredients.setHorizontalHeaderLabels(headers)
        header = self.ui.tabPrIngredients.horizontalHeader()
        header.setStyleSheet("QHeaderView::section { background-color: #365b6d; color: white; }")
        header.setSectionResizeMode(QHeaderView.Stretch)
        # Set Table to Read-Only
        self.ui.tabPrIngredients.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.ui.tabPrIngredients.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        # Populate the table with the data
        for row, item in enumerate(prData):
            inventory_id, description, amount = item
            row_values = [inventory_id, description, amount]
            # Loop through each column and insert items
            for col, value in enumerate(row_values):
                table_item = QTableWidgetItem(str(value))
                table_item.setTextAlignment(Qt.AlignCenter)

                self.ui.tabPrIngredients.setItem(row, col, table_item)
        self.ui.tabPrIngredients.resizeRowsToContents()
        data_cursor.close()
        
    def add_image(self):
        # Open a file dialog to select an image
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Select Image", 
            "", 
            "Image Files (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        self.image_path = file_path
        # If a file was selected, set it to lblImage
        if file_path:
            pixmap = QPixmap(file_path)
            scaled_pixmap = pixmap.scaled(self.ui.lblImage.size(), aspectRatioMode=1)
            self.ui.lblImage.setPixmap(scaled_pixmap)
    def add(self):
        inventory_id = self.ui.cbItems.currentData()  
        amount = self.ui.leAmount.text().strip() 

        if not inventory_id or not amount:
            QMessageBox.warning(self, "Input Error", "Please select an ingredient and enter an amount.")
            return

        try:
            amount = float(amount)  
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Amount must be a number.")
            return

        # Fetch the description from inventory
        description = next((desc for inv_id, desc, _ in self.inventory_items if inv_id == inventory_id), None)

        if not description:
            QMessageBox.warning(self, "Database Error", "Failed to fetch ingredient description.")
            return

        # Insert into prrestock_db.db
        prrestock_path = os.path.join("db", "prrestock_db.db")
        pr_conn = sqlite3.connect(prrestock_path)
        pr_cursor = pr_conn.cursor()

        try:
            pr_cursor.execute(
                "INSERT INTO new_product_data (inventory_id, description, amount) VALUES (?, ?, ?)",
                (inventory_id, description, amount)
            )
            pr_conn.commit()
            self.populate_table()
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Error", "This ingredient is already added.")
        finally:
            pr_cursor.close()
            pr_conn.close()
    def remove(self):
        # Get selected items
        selected_items = self.ui.tabPrIngredients.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Selection Error", "No item selected. Please select an ingredient to delete.")
            return

        # Identify unique rows from selected cells
        rows_to_delete = sorted(set(item.row() for item in selected_items), reverse=True)

        # Connect to the database
        prrestock_path = os.path.join("db", "prrestock_db.db")
        pr_conn = sqlite3.connect(prrestock_path)
        pr_cursor = pr_conn.cursor()

        try:
            for row in rows_to_delete:
                # Retrieve the inventory_id from the first column
                inventory_item = self.ui.tabPrIngredients.item(row, 0) 
                if inventory_item:
                    inventory_id = inventory_item.text()

                    # Delete the item from the database
                    pr_cursor.execute("DELETE FROM new_product_data WHERE inventory_id = ?", (inventory_id,))

                    # Remove the row from the table widget
                    self.ui.tabPrIngredients.removeRow(row)
                else:
                    QMessageBox.warning(self, "Missing Data", f"Could not find Inventory ID for row {row + 1}.")

            # Commit changes to the database
            pr_conn.commit()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to remove item(s): {e}")
        finally:
            pr_conn.close()

        self.populate_table()
    def confirm(self):
        prrestock_path = os.path.join("db", "prrestock_db.db")
        product_path = os.path.join("db", "product_db.db")
        ingredients_path = os.path.join("db", "ingredients_db.db")
        sales_path = os.path.join("db","sales_db.db")

        product_id = self.ui.lePrID.text().strip()
        product_name = self.ui.lePrName.text().strip()
        price_text = self.ui.lePrice.text().strip()

        if not product_id or not product_name or not price_text:
            QMessageBox.warning(self, "Input Error", "Please fill in all required fields, including price.")
            return

        try:
            price = float(price_text)
        except ValueError:
            QMessageBox.warning(self, "Invalid Price", "Please enter a valid number for the price.")
            return

        # Convert the pixmap in lblImage to BLOB
        pixmap = self.ui.lblImage.pixmap()
        if pixmap is None:
            QMessageBox.warning(self, "Image Error", "No image found in label.")
            return

        buffer = QBuffer()
        buffer.open(QIODevice.WriteOnly)
        pixmap.save(buffer, "PNG")
        image_blob = buffer.data()

        pr_conn = sqlite3.connect(prrestock_path)
        pr_cursor = pr_conn.cursor()

        product_conn = sqlite3.connect(product_path)
        product_cursor = product_conn.cursor()

        # Check for duplicate product_id before proceeding
        product_cursor.execute("SELECT 1 FROM products_on_hand WHERE product_id = ?", (product_id,))
        if product_cursor.fetchone():
            QMessageBox.warning(self, "Duplicate Product ID", "This is a duplicate Product ID.")
            product_cursor.close()
            product_conn.close()
            pr_cursor.close()
            pr_conn.close()
            return

        ingredients_conn = sqlite3.connect(ingredients_path)
        ingredients_cursor = ingredients_conn.cursor()

        sales_conn = sqlite3.connect(sales_path)
        sales_cursor = sales_conn.cursor()

        try:
            # Insert new product
            product_cursor.execute("""
                INSERT INTO products_on_hand (product_id, product_name, on_hand, exp_date, price, image) 
                VALUES (?, ?, 0, 'N/A', ?, ?)
            """, (product_id, product_name, price, image_blob))
            product_conn.commit()

            # Insert into sales table
            sales_cursor.execute("""
                INSERT INTO sales (product_id, product_name, price, quantity_sold)
                VALUES (?, ?, ?, 0)
            """, (product_id, product_name, price))
            sales_conn.commit()

            # Ingredient processing
            pr_cursor.execute("SELECT inventory_id, description, amount FROM new_product_data")
            new_ingredients = pr_cursor.fetchall()

            if not new_ingredients:
                QMessageBox.warning(self, "Data Error", "You have no new ingredients for the new product!")
                return

            ingredients_cursor.execute("PRAGMA table_info(ingredients)")
            existing_columns = [col[1] for col in ingredients_cursor.fetchall()]

            if product_id not in existing_columns:
                ingredients_cursor.execute(f"ALTER TABLE ingredients ADD COLUMN '{product_id}' REAL DEFAULT 0")
                ingredients_conn.commit()

            for inventory_id, description, amount in new_ingredients:
                ingredients_cursor.execute("SELECT inventory_id FROM ingredients WHERE inventory_id = ?", (inventory_id,))
                existing_ingredient = ingredients_cursor.fetchone()

                if existing_ingredient:
                    ingredients_cursor.execute(f"""
                        UPDATE ingredients SET '{product_id}' = ? WHERE inventory_id = ?
                    """, (amount, inventory_id))
                else:
                    other_columns = ", ".join([f"'{col}'" for col in existing_columns if col not in ("inventory_id", "description")])
                    default_values = ", ".join(["0"] * (len(existing_columns) - 2))
                    ingredients_cursor.execute(f"""
                        INSERT INTO ingredients (inventory_id, description, {other_columns}, '{product_id}')
                        VALUES (?, ?, {default_values}, ?)
                    """, (inventory_id, description, amount))

            ingredients_conn.commit()
            pr_cursor.execute("DELETE FROM new_product_data")
            pr_conn.commit()

            QMessageBox.information(self, "Success", "Product and ingredients updated successfully!")
            self.close()

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to confirm: {e}")
        finally:
            pr_cursor.close()
            pr_conn.close()
            product_cursor.close()
            product_conn.close()
            ingredients_cursor.close()
            ingredients_conn.close()
            sales_cursor.close()
            sales_conn.close()
class SalesWindow(QMainWindow):
    go_to_dashboard = pyqtSignal()
    go_to_inventory = pyqtSignal()
    go_to_pos = pyqtSignal()
    go_to_account = pyqtSignal()
    go_to_salesForecast = pyqtSignal()
    def __init__(self, widget=None):
        super(SalesWindow, self).__init__()
        self.ui = Ui_Sales()
        self.ui.setupUi(self)
        self.widget = widget
        self.ui.cbMonth.addItems(["January","February","March","April","May",
                                  "June","July","August","September","October",
                                  "November","December"])
        self.ui.cbMonth.setCurrentIndex(0)
        self.ui.cbMYear.addItems(["2025","2024","2023","2022"])
        self.ui.cbYear.addItems(["2025","2024","2023", "2022"])
        self.ui.cbYear.setCurrentIndex(0)
        self.load_sales_data()
        self.load_monthly_data()
        self.load_yearly_data()
        # Connect buttons
        self.ui.cbMonth.currentIndexChanged.connect(self.load_monthly_data)
        self.ui.cbMYear.currentIndexChanged.connect(self.update_month_selection)
        self.ui.cbYear.currentIndexChanged.connect(self.load_yearly_data)
        self.ui.btnDashboard.clicked.connect(self.go_to_dashboard)
        self.ui.btnInventory.clicked.connect(self.go_to_inventory)
        self.ui.btnPOS.clicked.connect(self.go_to_pos)
        self.ui.btnAccount.clicked.connect(self.go_to_account)
        self.ui.btnForecast.clicked.connect(self.go_to_salesForecast)
        
    def update_month_selection(self):
        selected_year = self.ui.cbMYear.currentText()
        db_name = f"sales_{selected_year}.db"
        sales_path = os.path.join("db", db_name)

        if not os.path.exists(sales_path):
            print(f"Database {db_name} not found.")  # Debug message
            self.ui.cbMonth.clear()
            return

        sales_conn = sqlite3.connect(sales_path)
        sales_cursor = sales_conn.cursor()

        try:
            # Fetch the list of tables in the selected year's database
            sales_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = {row[0] for row in sales_cursor.fetchall()}  # Convert to set for easy lookup

            # Month mappings (database table names vs. UI names)
            month_map = {
                "jan": "January", "feb": "February", "mar": "March", "apr": "April",
                "may": "May", "jun": "June", "jul": "July", "aug": "August",
                "sep": "September", "oct": "October", "nov": "November", "dec": "December"
            }

            # Filter available months based on existing tables
            available_months = [month_map[m] for m in month_map if m in tables]

            # Update cbMonth with available months
            self.ui.cbMonth.clear()
            self.ui.cbMonth.addItems(available_months)
            self.ui.cbMonth.setCurrentIndex(0)  # Reset to first available month

            # Load data for the first available month
            self.load_monthly_data()

        except sqlite3.Error as e:
            print(f"Error checking tables: {e}")

        finally:
            sales_conn.close()
    def load_yearly_data(self):
        selected_year = self.ui.cbYear.currentText()  # Get selected year
        db_name = f"sales_{selected_year}.db"  # Construct database filename
        year_table = "year_total"  # Yearly summary table
        
        sales_path = os.path.join("db", db_name)
        
        if not os.path.exists(sales_path):
            print(f"Database {db_name} not found.")
            self.ui.yProductTable.setRowCount(0)
            self.ui.lblYTotal.setText("0.00")
            return  
        
        sales_conn = sqlite3.connect(sales_path)
        sales_cursor = sales_conn.cursor()

        try:
            # Fetch yearly data
            sales_cursor.execute(f"SELECT product_id, product_name, price, quantity_sold FROM {year_table}")
            products = sales_cursor.fetchall()

            # Set up the table
            self.ui.yProductTable.setRowCount(len(products))
            self.ui.yProductTable.setColumnCount(4)
            self.ui.yProductTable.verticalHeader().hide()

            headers = ["Product ID", "Product Name", "Price", "Quantity Sold"]
            self.ui.yProductTable.setHorizontalHeaderLabels(headers)
            header = self.ui.yProductTable.horizontalHeader()
            header.setStyleSheet("QHeaderView::section { background-color: #365b6d; color: white; font-size: 20px; font-weight: bold;}")
            header.setSectionResizeMode(QHeaderView.Stretch)

            # Populate the table
            for row, item in enumerate(products):
                for col, value in enumerate(item):
                    table_item = QTableWidgetItem(str(value))
                    table_item.setTextAlignment(Qt.AlignCenter)
                    self.ui.yProductTable.setItem(row, col, table_item)

            # Compute & Display Total Sales
            total = sum(item[2] * item[3] for item in products)  # price * quantity_sold
            self.ui.lblYTotal.setText(f"{total:,.2f}")  # Add thousands separator

        except sqlite3.OperationalError as e:
            print(f"Error loading yearly data: {e}")
            self.ui.yProductTable.setRowCount(0)  # Clear table if query fails
            self.ui.lblYTotal.setText("0.00")  # Reset total

        finally:
            sales_conn.close()
    def load_monthly_data(self):
        selected_month = self.ui.cbMonth.currentText().lower()[:3]  # Convert to short form (e.g., "January" → "jan")
        selected_year = self.ui.cbMYear.currentText()
        db_name = f"sales_{selected_year}.db"
        sales_path = os.path.join("db", db_name)

        if not os.path.exists(sales_path):
            print(f"Database {db_name} not found.")  # Debug message
            self.ui.mProductTable.setRowCount(0)  # Clear table
            self.ui.lblMTotal.setText("0.00")  # Reset total
            return

        sales_conn = sqlite3.connect(sales_path)
        sales_cursor = sales_conn.cursor()

        try:
            query = f"SELECT product_id, product_name, price, quantity_sold FROM {selected_month}"
            sales_cursor.execute(query)
            products = sales_cursor.fetchall()

            # Set up the table
            self.ui.mProductTable.setRowCount(len(products))
            self.ui.mProductTable.setColumnCount(4)
            self.ui.mProductTable.verticalHeader().hide()

            headers = ["Product ID", "Product Name", "Price", "Quantity Sold"]
            self.ui.mProductTable.setHorizontalHeaderLabels(headers)
            header = self.ui.mProductTable.horizontalHeader()
            header.setStyleSheet("QHeaderView::section { background-color: #365b6d; color: white; font-size: 20px; font-weight: bold;}")
            header.setSectionResizeMode(QHeaderView.Stretch)

            # Populate the table
            for row, item in enumerate(products):
                for col, value in enumerate(item):
                    table_item = QTableWidgetItem(str(value))
                    table_item.setTextAlignment(Qt.AlignCenter)
                    self.ui.mProductTable.setItem(row, col, table_item)

            # Compute & Display Total Sales
            total = sum(item[2] * item[3] for item in products)
            self.ui.lblMTotal.setText(f"{total:,.2f}")

        except sqlite3.OperationalError as e:
            print(f"Error loading data: {e}")
            self.ui.mProductTable.setRowCount(0)  # Clear table if query fails
            self.ui.lblMTotal.setText("0.00")  # Reset total

        finally:
            sales_conn.close()
    def load_sales_data(self):
        sales_path = os.path.join("db", "sales_db.db")
        sales_conn = sqlite3.connect(sales_path)
        sales_cursor = sales_conn.cursor()
        # Fetch all items from the inventory table
        sales_cursor.execute("SELECT product_id, product_name, price, quantity_sold FROM sales")
        products = sales_cursor.fetchall()

        # Set up the table
        self.ui.productTable.setRowCount(len(products)) 
        self.ui.productTable.setColumnCount(4)
        self.ui.productTable.verticalHeader().hide()
        # Set headers for the table
        headers = ["Product ID", "Product Name", "Price", "Quantity Sold"]
        self.ui.productTable.setHorizontalHeaderLabels(headers)
        header = self.ui.productTable.horizontalHeader()
        header.setStyleSheet("QHeaderView::section { background-color: #365b6d; color: white; font-size: 20px; font-weight: bold;}")
        header.setSectionResizeMode(QHeaderView.Stretch)

        # Populate the table with the data
        for row, item in enumerate(products):
            for col, value in enumerate(item):
                table_item = QTableWidgetItem(str(value))
                table_item.setTextAlignment(Qt.AlignCenter)
                self.ui.productTable.setItem(row, col, table_item)
        
        # Compute & Display Total Sales
        total = sum(item[2] * item[3] for item in products)
        self.ui.lblTotal.setText(f"{total:.2f}")
class SalesForecastWindow(QMainWindow):
    go_to_dashboard = pyqtSignal()
    go_to_sales = pyqtSignal()
    go_to_pos = pyqtSignal()
    go_to_inventory = pyqtSignal()
    go_to_account = pyqtSignal()
    def __init__(self, widget=None):
        super(SalesForecastWindow, self).__init__()
        self.ui = Ui_SalesForecast()
        self.ui.setupUi(self)
        self.setWindowTitle("Sales Forecast")
        self.widget = widget
        self.populate_products()
        self.update_forecast()
        
        # Connect buttons to functions
        self.ui.btnDashboard.clicked.connect(self.go_to_dashboard)
        self.ui.btnInventory.clicked.connect(self.go_to_inventory)
        self.ui.btnSales.clicked.connect(self.go_to_sales)
        self.ui.btnPOS.clicked.connect(self.go_to_pos)
        self.ui.btnAccount.clicked.connect(self.go_to_account)
        self.ui.cbProduct.currentIndexChanged.connect(self.update_forecast)
    
    def populate_products(self):
        db_path = os.path.join("db", "product_db.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT product_id, product_name FROM products_on_hand")
        products = cursor.fetchall()
        
        self.ui.cbProduct.clear()
        for product in products:
            self.ui.cbProduct.addItem(f"{product[0]} - {product[1]}")

        conn.close()
        
    def get_sales_data(self, product_id):
        months_2024 = ["may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
        months_2025 = ["jan", "feb", "mar", "apr"]
        
        sales_data = []
        
        sales_2024_path = os.path.join("db", "sales_2024.db")
        if os.path.exists(sales_2024_path):
            conn = sqlite3.connect(sales_2024_path)
            cursor = conn.cursor()

            for month in months_2024:
                cursor.execute(f"SELECT quantity_sold FROM {month} WHERE product_id = ?", (product_id,))
                result = cursor.fetchone()
                sales_data.append(result[0] if result else 0)

            conn.close()
        else:
            print("sales_2024.db not found.")
        
        sales_2025_path = os.path.join("db", "sales_2025.db")
        if os.path.exists(sales_2025_path):
            conn = sqlite3.connect(sales_2025_path)
            cursor = conn.cursor()

            for month in months_2025:
                cursor.execute(f"SELECT quantity_sold FROM {month} WHERE product_id = ?", (product_id,))
                result = cursor.fetchone()
                sales_data.append(result[0] if result else 0)

            conn.close()
        else:
            print("sales_2025.db not found.")
        
        return sales_data
    
    def forecast_sales(self, product_id):
        sales_2022_path = os.path.join("db", "sales_2022.db")
        sales_2023_path = os.path.join("db", "sales_2023.db")
        sales_2024_path = os.path.join("db", "sales_2024.db")
        
        past_sales = []
        
        for db_path in [sales_2022_path,sales_2023_path, sales_2024_path]:
            if not os.path.exists(db_path):
                continue

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            try:
                cursor.execute("SELECT quantity_sold FROM apr WHERE product_id = ?", (product_id,))
                result = cursor.fetchone()
                if result:
                    past_sales.append(result[0])
            except sqlite3.OperationalError:
                pass

            conn.close()

        if not past_sales:
            return None

        forecasted_value = self.use_gpt_neo_forecast(past_sales)
        return forecasted_value
    
    def use_gpt_neo_forecast(self, past_data):
        from statsmodels.tsa.holtwinters import Holt
        from statsmodels.tsa import arima_model
        from statsmodels.tsa import vector_ar
        

        if len(past_data) < 2 or all(x == past_data[0] for x in past_data):
            return past_data[-1] if past_data else 0  # Avoid division errors

        data = np.array(past_data, dtype=float)

        model = Holt(data).fit()
        forecasted_value = model.forecast(1)[0]
        return round(forecasted_value)
    
    def generate_comment(self, forecast):
        if forecast is None:
            return "No historical data available to forecast."

        # Get the May sales (the last value in past_sales list)
        may_sales = self.past_sales[-1] if len(self.past_sales) > 0 else 0

        # Calculate the percentage change from March sales to forecasted sales
        if may_sales > 0:  # Avoid division by zero
            change_percentage = ((forecast - may_sales) / may_sales) * 100
        else:
            change_percentage = 0  # No change if April sales were 0

        # Generate comment based on the change
        if forecast > may_sales:
            return f"Sales are expected to <span style='color: #7ff58d;'>INCREASE</span> in May by <span style='color: #7ff58d;'>{round(change_percentage, 2)}%</span>."
        elif forecast < may_sales:
            return f"Sales are expected to <span style='color: #f5737c;'>DECREASE</span> in May by <span style='color: #f5737c;'>{round(abs(change_percentage), 2)}%</span>."
        else:
            return "Sales are predicted to remain stable in May."
        
    def plot_forecast(self, past_sales, forecasted_value):
        # Ensure gpPerformance has a layout
        if self.ui.gpPerformance.layout() is None:
            self.ui.gpPerformance.setLayout(QVBoxLayout())

        layout = self.ui.gpPerformance.layout()

        # Remove old plots
        while layout.count() > 0:
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Create a new figure
        fig, ax = plt.subplots(figsize=(6, 4))
        fig.patch.set_facecolor((1, 1, 1, 0.75))
        months = [ "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar", "Apr", "May (Forecast)"]

        # Combine past sales data with forecasted value for April 2025
        values = past_sales + [forecasted_value]

        # Plot historical data (Apr-Dec 2024 and Jan-Mar 2025)
        ax.plot(months[:-1], values[:-1], marker="o", linestyle="-", color="blue", label="Past Sales")

        # Highlight the forecasted value for April 2025 (this should be the last point)
        ax.plot(months[-1], forecasted_value, marker="o", color="red", markersize=8, label="Forecasted Value")

        # Connect the forecasted point to the last point (March 2025)
        ax.plot([months[-2], months[-1]], [values[-2], forecasted_value], linestyle="--", color="red")
        # Add labels to each past sales point
        for i, value in enumerate(values[:-1]):
            ax.text(i + 0.1, value + -2, f"{value:.0f}", ha='center', va='bottom', fontsize=9)

        # Add label to the forecasted point
        ax.text(len(values) - 0.8, forecasted_value, f"{forecasted_value:.0f}", 
                ha='center', va='bottom', fontsize=9, color='red')

        # Show grid lines
        ax.grid(True)

        # Labels and title
        ax.set_xlabel("Month")
        ax.set_ylabel("Quantity Sold")
        ax.set_title("Sales Forecast for May 2025")
        ax.set_facecolor((1, 1, 1, 0))
        ax.legend()

        # Embed the plot into the QWidget
        canvas = FigureCanvas(fig)
        layout.addWidget(canvas)
        
    def update_forecast(self):
        selected_product = self.ui.cbProduct.currentText()
        if not selected_product:
            return

        product_id = selected_product.split(" - ")[0]  # Extract product_id

        # Fetch past sales data
        self.past_sales = self.get_sales_data(product_id)
        forecasted_value = self.forecast_sales(product_id)

        # Update Graph
        self.plot_forecast(self.past_sales, forecasted_value)

        # Update lblComment
        self.ui.lblComment.setText(self.generate_comment(forecasted_value))
class ForecastWorker(QThread):
    forecast_generated = pyqtSignal(str)

    def __init__(self, sales_prompt):
        super().__init__()
        self.sales_prompt = sales_prompt

    def run(self):
        try:
            tokenizer = GPT2Tokenizer.from_pretrained("EleutherAI/gpt-neo-1.3B")
            model = GPTNeoForCausalLM.from_pretrained("EleutherAI/gpt-neo-1.3B")
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            model.to(device)

            inputs = tokenizer(self.sales_prompt, return_tensors="pt", truncation=True, max_length=512)
            inputs = {key: value.to(device) for key, value in inputs.items()}

            outputs = model.generate(inputs["input_ids"], max_new_tokens=50, num_beams=1, pad_token_id=tokenizer.eos_token_id)
            forecast = tokenizer.decode(outputs[0], skip_special_tokens=True)

            self.forecast_generated.emit(forecast)

        except Exception as e:
            self.forecast_generated.emit(f"Error: {str(e)}")
class POSWindow(QMainWindow):
    inventory_update = pyqtSignal()
    sales_update = pyqtSignal()
    go_to_dashboard = pyqtSignal()
    go_to_sales = pyqtSignal()
    go_to_inventory = pyqtSignal()
    go_to_account = pyqtSignal()
    def __init__(self, widget=None):
        super(POSWindow, self).__init__()
        self.ui = Ui_pos()
        self.ui.setupUi(self)
        self.setWindowTitle("POS")
        self.widget = widget

        self.load_product_buttons()
        
        # Create a model for the QListView
        self.cart_model = QStandardItemModel()
        self.ui.cartList.setModel(self.cart_model)
        
        self.total_price = 0.0
        self.update_total_label()

        # Connect buttons to functions
        self.ui.btnDashboard.clicked.connect(self.go_to_dashboard)
        self.ui.btnInventory.clicked.connect(self.go_to_inventory)
        self.ui.btnSales.clicked.connect(self.go_to_sales)
        self.ui.btnAccount.clicked.connect(self.go_to_account)
        self.ui.btnClear.clicked.connect(self.clear_cart)
        self.ui.btnCheckout.clicked.connect(self.checkout)
    
    def load_product_buttons(self):
        product_path = os.path.join("db", "product_db.db")
        conn = sqlite3.connect(product_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT product_id, product_name, on_hand, price, image FROM products_on_hand")
        products = cursor.fetchall()
        conn.close()

        row = col = 0
        max_columns = 4  # Adjust depending on your desired layout

        for product_id, product_name, on_hand, price, image_blob in products:
            button = QToolButton()
            button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            button.setIconSize(QSize(150, 150))
            button.setFixedSize(261, 251)

            # Convert image blob to pixmap
            if image_blob:
                pixmap = QPixmap()
                pixmap.loadFromData(image_blob)
                button.setIcon(QIcon(pixmap))
            else:
                button.setIcon(QIcon("img/cake_default.png"))  

            # Format button text
            button.setText(f"{product_id} {product_name}\n{price:.2f}\nOn Stock: {on_hand}")
            button.setStyleSheet("font-size: 10pt; background-color: rgba(255, 255, 255, 160); border-radius: 5px;")
            
            # Set product_id as a custom property
            button.setProperty("product_id", product_id)
            button.clicked.connect(lambda _, pid=product_id: self.add_to_cart(pid))

            # Add to grid layout
            self.ui.gridProducts.addWidget(button, row, col)
            col += 1
            if col >= max_columns:
                col = 0
                row += 1
                
    def clear_product_buttons(self):
        # Remove all widgets from the gridProducts layout
        layout = self.ui.gridProducts
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                
    def add_to_cart(self, product_id):
        sales_path = os.path.join("db", "sales_db.db")
        product_path = os.path.join("db", "product_db.db")

        # Check product availability
        product_conn = sqlite3.connect(product_path)
        product_cursor = product_conn.cursor()
        product_cursor.execute("SELECT on_hand FROM products_on_hand WHERE product_id = ?", (product_id,))
        result = product_cursor.fetchone()
        product_conn.close()

        if not result or result[0] <= 0:
            QMessageBox.warning(self, "Out of Stock", f"Product {product_id} is out of stock!")
            return

        available_stock = result[0]  # Get the available stock

        # Fetch product details from sales database
        sales_conn = sqlite3.connect(sales_path)
        sales_cursor = sales_conn.cursor()
        sales_cursor.execute("SELECT product_name, price FROM sales WHERE product_id = ?", (product_id,))
        product_data = sales_cursor.fetchone()
        sales_conn.close()

        if not product_data:
            QMessageBox.warning(self, "Error", f"Product {product_id} not found in sales database!")
            return

        product_name, price = product_data

        # Check if item already exists in cart
        for i in range(self.cart_model.rowCount()):
            item = self.cart_model.item(i)
            if item.text().startswith(f"{product_id} - {product_name} @ {price}"):
                # Extract current quantity
                parts = item.text().split(" x")
                current_qty = int(parts[1]) if len(parts) > 1 else 1

                # Prevent exceeding available stock
                if current_qty + 1 > available_stock:
                    QMessageBox.warning(self, "Stock Limit Reached",
                                        f"Only {available_stock} units of {product_name} are available!")
                    return

                # Update quantity
                new_qty = current_qty + 1
                item.setText(f"{product_id} - {product_name} @ {price} x{new_qty}")
                self.total_price += price
                self.update_total_label()
                return

        # If product is not in the cart, add a new entry (only if stock allows)
        if available_stock > 0:
            new_item = QStandardItem(f"{product_id} - {product_name} @ {price} x1")
            self.cart_model.appendRow(new_item)
            self.total_price += price
            self.update_total_label()
    def clear_cart(self):
        self.cart_model.clear()
        self.total_price = 0.0
        self.update_total_label()
    def update_total_label(self):
        # Update the lblTotal label with the total price
        self.ui.lblTotal.setText(f"Total: {self.total_price:.2f}")
    def checkout(self):
        if self.cart_model.rowCount() == 0:
            QMessageBox.warning(self, "Empty Cart", "Your cart is empty. Add items before checkout.")
            return

        product_path = os.path.join("db", "product_db.db")
        sales_path = os.path.join("db", "sales_db.db")

        product_conn = sqlite3.connect(product_path)
        product_cursor = product_conn.cursor()
        sales_conn = sqlite3.connect(sales_path)
        sales_cursor = sales_conn.cursor()

        try:
            # Process each item in the cart
            for i in range(self.cart_model.rowCount()):
                item_text = self.cart_model.item(i).text()
                parts = item_text.split(" x")
                if len(parts) != 2:
                    continue  # Skip malformed entries

                product_info, quantity = parts[0], int(parts[1])
                product_id = product_info.split(" - ")[0]

                # Get current stock
                product_cursor.execute("SELECT on_hand FROM products_on_hand WHERE product_id = ?", (product_id,))
                result = product_cursor.fetchone()
                if not result:
                    QMessageBox.warning(self, "Error", f"Product {product_id} not found in products_on_hand!")
                    continue

                current_stock = result[0]
                new_stock = max(0, current_stock - quantity)

                # Update product stock
                product_cursor.execute("UPDATE products_on_hand SET on_hand = ? WHERE product_id = ?", (new_stock, product_id))

                # Update quantity_sold in sales database
                sales_cursor.execute("SELECT quantity_sold FROM sales WHERE product_id = ?", (product_id,))
                result = sales_cursor.fetchone()
                if result:
                    new_quantity_sold = result[0] + quantity
                    sales_cursor.execute("UPDATE sales SET quantity_sold = ? WHERE product_id = ?", (new_quantity_sold, product_id))

            # Commit changes
            product_conn.commit()
            sales_conn.commit()

            QMessageBox.information(self, "Success", "Transaction completed successfully!")
            self.clear_cart()
            
            # Refresh product buttons to reflect new stock levels
            self.clear_product_buttons()
            self.load_product_buttons()
            
            # Update Other Tables
            self.inventory_update.emit()
            self.sales_update.emit()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"An error occurred: {e}")
            product_conn.rollback()
            sales_conn.rollback()

        finally:
            product_conn.close()
            sales_conn.close()
class AccountWindow(QMainWindow):
    go_to_dashboard = pyqtSignal()
    go_to_sales = pyqtSignal()
    go_to_pos = pyqtSignal()
    go_to_inventory = pyqtSignal()
    switch_to_login = pyqtSignal()
    def __init__(self, widget=None):
        super(AccountWindow, self).__init__()
        self.ui = Ui_account()
        self.ui.setupUi(self)
        self.setWindowTitle("Account")
        self.widget = widget
        
        # Connect buttons
        self.ui.btnDashboard.clicked.connect(self.go_to_dashboard)
        self.ui.btnInventory.clicked.connect(self.go_to_inventory)
        self.ui.btnSales.clicked.connect(self.go_to_sales)
        self.ui.btnPOS.clicked.connect(self.go_to_pos)
        self.ui.btnLogOut.clicked.connect(self.switch_to_login)
class AppController:
    def __init__(self):
        self.basedir = os.path.dirname(os.path.abspath(__file__))
        self.icon_path = os.path.join(self.basedir, "img", "econologo_transparent_cropped.png")

        self.login_window = Login()
        self.signup_window = None
        self.main_window = None

        # Connect signals
        self.login_window.switch_to_signup.connect(self.show_signup)
        self.login_window.switch_to_main.connect(self.show_main)

        # Start the app
        self.login_window.show()

    def show_signup(self):
        self.signup_window = SignUp()
        self.signup_window.switch_to_login.connect(self.show_login)
        self.signup_window.switch_to_main.connect(self.show_main)
        self.signup_window.show()

    def show_login(self):
        self.login_window = Login()
        self.login_window.switch_to_signup.connect(self.show_signup)
        self.login_window.switch_to_main.connect(self.show_main)
        self.login_window.show()

    def show_main(self):
        self.main_window = MainWindow(self.icon_path)
        self.main_window.switch_to_login.connect(self.show_login)
        self.main_window.show()
        self.login_window.close()
if __name__ == "__main__":
    app = QApplication(sys.argv)

    controller = AppController()

    try:
        sys.exit(app.exec_())
    except Exception as e:
        print(f"Exiting: {e}")