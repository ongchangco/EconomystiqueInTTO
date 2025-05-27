import sys
import os
from PyQt5.uic import loadUi
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QFileDialog, QListView
from PyQt5.QtCore import QStringListModel
from PyQt5.QtGui import QPixmap

#additional imports for each page
from login_ui import Ui_Login
from signIn_ui import Ui_signUp
from landingPage_ui import Ui_MainWindow
from salesForecast_ui import Ui_SalesForecast
from calendar_ui import Ui_Calendar
from account_ui import Ui_account
from sales_ui import Ui_Sales
#import sqlite3

class Login(QMainWindow):
    def __init__(self):
        super(Login, self).__init__()

        self.ui = Ui_Login()
        self.ui.setupUi(self)
        # Connect sign up button
        self.ui.signUpButton.clicked.connect(self.open_signUp)
        #for login button on login == go to landingPage
        self.ui.pushButton.clicked.connect(self.loginfunction)
        
    def open_signUp(self):
        sign_up = SignUp()
        widget.addWidget(sign_up)
        widget.setCurrentIndex(widget.currentIndex()+1)
                
    def loginfunction(self):
        landing_page = LandingPage()
        widget.addWidget(landing_page)
        widget.setCurrentIndex(widget.currentIndex()+1)
        
class SignUp(QMainWindow):
    def __init__(self):
        super(SignUp, self).__init__()
        
        self.ui = Ui_signUp()
        self.ui.setupUi(self)
        
        # Connect login button
        self.ui.loginButton.clicked.connect(self.open_Login)
        #for signin button on signup == go to landingPage
        self.ui.pushButton.clicked.connect(self.signinfunction)
        
    def open_Login(self):
        login = Login()
        widget.addWidget(login)
        widget.setCurrentIndex(widget.currentIndex()+1)
        
    def signinfunction(self):
        landing_page = LandingPage()
        widget.addWidget(landing_page)
        widget.setCurrentIndex(widget.currentIndex()+1)
        
class LandingPage(QMainWindow):
    def __init__(self):
        super(LandingPage, self).__init__()
        
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowTitle("Inventory Status")
        
        # Connect buttons
        self.ui.recommendationButton.clicked.connect(self.open_forecast)
        self.ui.btnSales.clicked.connect(self.open_sales)
        self.ui.btnCalendar.clicked.connect(self.open_calendar)
        self.ui.btnAccount.clicked.connect(self.open_account)
        
    # Button Functions
    def open_sales(self):
        sales_window = SalesWindow()
        widget.addWidget(sales_window)
        widget.setCurrentIndex(widget.currentIndex()+1)
        
    def open_calendar(self):
        calendar_window = CalendarWindow()
        widget.addWidget(calendar_window)
        widget.setCurrentIndex(widget.currentIndex()+1)
    
    def open_account(self):
        account_window = AccountWindow()
        widget.addWidget(account_window)
        widget.setCurrentIndex(widget.currentIndex()+1)
        
    def open_forecast(self):
        from salesForecast import SalesForecastWindow
        self.sales_forecast_window = SalesForecastWindow()
        self.sales_forecast_window.show()
        
class SalesWindow(QMainWindow):
    def __init__(self):
        super(SalesWindow, self).__init__()
        
        # Instantiate UI class instance
        self.ui = Ui_SalesForecast()

        # Wrap setupUi logic safely
        self._setup_ui()
        self.setWindowTitle("Sales")

        # Connect buttons
        self.ui.btnInventory.clicked.connect(self.open_inventory)
        self.ui.btnCalendar.clicked.connect(self.open_calendar)
        self.ui.btnAccount.clicked.connect(self.open_account)
    
    def _setup_ui(self):
        try:
            self.ui.setupUi(self)
        except RecursionError as e:
            print("Recursion error detected during UI setup:", e)
    
    # Button Functions  
    def open_inventory(self):
        inventory_window = LandingPage()
        widget.addWidget(inventory_window)
        widget.setCurrentIndex(widget.currentIndex()+1)
        
    def open_calendar(self):
        calendar_window = CalendarWindow()
        widget.addWidget(calendar_window)
        widget.setCurrentIndex(widget.currentIndex()+1)
    
    def open_account(self):
        account_window = AccountWindow()
        widget.addWidget(account_window)
        widget.setCurrentIndex(widget.currentIndex()+1)
        
class CalendarWindow(QMainWindow):
    def __init__(self):
        super(CalendarWindow, self).__init__()
        self.ui = Ui_Calendar()

        # Wrap setupUi logic safely
        self._setup_ui()
        self.setWindowTitle("Events Calendar")
        
        # Connect buttons
        self.ui.btnInventory.clicked.connect(self.open_inventory)
        self.ui.btnSales.clicked.connect(self.open_sales)
        self.ui.btnAccount.clicked.connect(self.open_account)

    def _setup_ui(self):
        try:
            self.ui.setupUi(self)
        except RecursionError as e:
            print("Recursion error detected during UI setup:", e)
            
    # Button Functions
    def open_inventory(self):
        inventory_window = LandingPage()
        widget.addWidget(inventory_window)
        widget.setCurrentIndex(widget.currentIndex()+1)
        
    def open_sales(self):
        sales_window = SalesWindow()
        widget.addWidget(sales_window)
        widget.setCurrentIndex(widget.currentIndex()+1)
    
    def open_account(self):
        account_window = AccountWindow()
        widget.addWidget(account_window)
        widget.setCurrentIndex(widget.currentIndex()+1)
        
class AccountWindow(QMainWindow):
    def __init__(self):
        super(AccountWindow, self).__init__()

        # Instantiate UI class instance
        self.ui = Ui_account()

        # Wrap setupUi logic safely
        self._setup_ui()
        self.setWindowTitle("Account")

        # Set up the model for QListView
        self.file_model = QStringListModel()
        self.ui.fileListView.setModel(self.file_model)
        self.file_list = [] # Stores file paths
        self.ui.fileListView_2.setModel(self.file_model)
        self.file_list_2 = []

        # Load files from storage
        self.load_files()

        # Connect buttons
        self.ui.btnInventory.clicked.connect(self.open_inventory)
        self.ui.btnSales.clicked.connect(self.open_sales)
        self.ui.btnCalendar.clicked.connect(self.open_calendar)
        self.ui.btnLogOut.clicked.connect(self.open_login)
        #inventory files buttons
        self.ui.btnOpenFile.clicked.connect(self.open_file)
        self.ui.btnDeleteFile.clicked.connect(self.delete_file)
        self.ui.btnAddFile.clicked.connect(self.add_file)
        #sales files buttons
        self.ui.btnOpenFile_2.clicked.connect(self.open_file_2)
        self.ui.btnDeleteFile_2.clicked.connect(self.delete_file_2)
        self.ui.btnAddFile_2.clicked.connect(self.add_file_2)

    def _setup_ui(self):
        try:
            self.ui.setupUi(self)
        except RecursionError as e:
            print("Recursion error detected during UI setup:", e)

    def open_inventory(self):
        inventory_window = LandingPage()
        widget.addWidget(inventory_window)
        widget.setCurrentIndex(widget.currentIndex()+1)

    def open_sales(self):
        sales_window = SalesWindow()
        widget.addWidget(sales_window)
        widget.setCurrentIndex(widget.currentIndex()+1)

    def open_calendar(self):
        account_window = CalendarWindow()
        widget.addWidget(account_window)
        widget.setCurrentIndex(widget.currentIndex()+1)
        
    def open_login(self):
        account_login = Login()
        widget.addWidget(account_login)
        widget.setCurrentIndex(widget.currentIndex()+1)
        
    #for Inventory Files Buttons
    def delete_file(self):
        """Delete the selected file from the list."""
        selected_indexes = self.ui.fileListView.selectedIndexes()
        if not selected_indexes:
            QMessageBox.warning(self, "Warning", "Please select a file to delete.")
            return

        selected_index = selected_indexes[0] # Only allow single selection
        file_path = self.file_list[selected_index.row()]

        # Confirm deletion
        reply = QMessageBox.question(
            self, "Confirm Deletion",
            f"Are you sure you want to delete:\n{file_path}?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.file_list.pop(selected_index.row())
            self.file_model.setStringList(self.file_list)
            self.save_files()

    def open_file(self):
        """Open the selected file."""
        selected_indexes = self.ui.fileListView.selectedIndexes()
        if not selected_indexes:
            QMessageBox.warning(self, "Warning", "Please select a file to open.")
            return

        selected_index = selected_indexes[0] # Only allow single selection
        file_path = self.file_list[selected_index.row()]

        # Open the file (use an appropriate library for Excel files if needed)
        try:
            os.startfile(file_path) # Windows-specific; use subprocess for other platforms
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open file:\n{str(e)}")

    def add_file(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select an Excel File", "",
            "Excel Files (*.xls *.xlsx);;All Files (*)",
            options=options
        )
        if file_path:
            self.file_list.append(file_path)
            self.file_model.setStringList(self.file_list)
            self.save_files()

    def save_files(self):
        """Save the file list to a local file."""
        try:
            with open('file_list.txt', 'w') as f:
                for file_path in self.file_list:
                    f.write(file_path + '\n')
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save files:\n{str(e)}")

    def load_files(self):
        """Load the file list from a local file."""
        if os.path.exists('file_list.txt'):
            try:
                with open('file_list.txt', 'r') as f:
                    self.file_list = [line.strip() for line in f.readlines()]
                self.file_model.setStringList(self.file_list)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load files:\n{str(e)}")
                
    #for Sales Files Buttons
    def delete_file_2(self):
        """Delete the selected file from the list."""
        selected_indexes = self.ui.fileListView_2.selectedIndexes()
        if not selected_indexes:
            QMessageBox.warning(self, "Warning", "Please select a file to delete.")
            return

        selected_index = selected_indexes[0] # Only allow single selection
        file_path = self.file_list_2[selected_index.row()]

        # Confirm deletion
        reply = QMessageBox.question(
            self, "Confirm Deletion",
            f"Are you sure you want to delete:\n{file_path}?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.file_list_2.pop(selected_index.row())
            self.file_model.setStringList(self.file_list_2)
            self.save_files()

    def open_file_2(self):
        """Open the selected file."""
        selected_indexes = self.ui.fileListView_2.selectedIndexes()
        if not selected_indexes:
            QMessageBox.warning(self, "Warning", "Please select a file to open.")
            return

        selected_index = selected_indexes[0] # Only allow single selection
        file_path = self.file_list_2[selected_index.row()]

        # Open the file (use an appropriate library for Excel files if needed)
        try:
            os.startfile(file_path) # Windows-specific; use subprocess for other platforms
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open file:\n{str(e)}")

    def add_file_2(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select an Excel File", "",
            "Excel Files (*.xls *.xlsx);;All Files (*)",
            options=options
        )
        if file_path:
            self.file_list_2.append(file_path)
            self.file_model.setStringList(self.file_list_2)
            self.save_files()

    def save_files_2(self):
        """Save the file list to a local file."""
        try:
            with open('file_list_2.txt', 'w') as f:
                for file_path in self.file_list_2:
                    f.write(file_path + '\n')
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save files:\n{str(e)}")

    def load_files(self):
        """Load the file list from a local file."""
        if os.path.exists('file_list_2.txt'):
            try:
                with open('file_list_2.txt', 'r') as f:
                    self.file_list = [line.strip() for line in f.readlines()]
                self.file_model.setStringList(self.file_list_2)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load files:\n{str(e)}")
        
        
# main
app = QApplication(sys.argv)
login = Login()
widget = QtWidgets.QStackedWidget()
widget.addWidget(login)
widget.setFixedHeight(600)
widget.setFixedWidth(800)
widget.show()
try:
    sys.exit(app.exec_())
except:
    print("Exiting")