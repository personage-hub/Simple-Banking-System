from dataclasses import dataclass
import sqlite3
import random


@dataclass
class BankAccount:
    bank_id: int
    card_number: str
    pin: str
    balance: int


class SQLRequest:
    def __init__(self, cur, conn):
        self.cur = cur
        self.conn = conn

    @classmethod
    def connection(cls):
        conn = sqlite3.connect('./card.s3db')
        cur = conn.cursor()
        return cls(cur, conn)

    def is_uniq(self, uniq_type: str, uniq_object):
        self.cur.execute(f"SELECT {uniq_type} FROM card;")
        object_lst = []
        object_tuple_lst = self.cur.fetchall()
        for i in object_tuple_lst:
            object_lst.append(i[0])
        return uniq_object not in object_lst

    def create_table(self, table: str):
        self.cur.execute(f"CREATE TABLE IF NOT EXISTS card {table};")
        self.conn.commit()

    def insert_data(self, bank_account: BankAccount):
        data_to_insert = (bank_account.bank_id, bank_account.card_number, bank_account.pin, bank_account.balance)
        self.cur.execute(f"INSERT INTO card (id, number, pin, balance) VALUES {data_to_insert}")
        self.conn.commit()

    def delete_data(self, account_to_delete: BankAccount):
        self.cur.execute(f"DELETE FROM card WHERE id = {account_to_delete.bank_id}")
        self.conn.commit()

    def update_balance(self, bank_account: BankAccount):
        self.cur.execute(f"UPDATE card SET balance = {bank_account.balance} WHERE id={bank_account.bank_id}")
        self.conn.commit()

    def get_data(self, card_number):
        self.cur.execute(f"SELECT * FROM card WHERE number = {card_number};")
        bank_account = self.cur.fetchone()
        result = BankAccount(bank_account[0], bank_account[1], bank_account[2], bank_account[3])
        return result


class Bank:
    def __init__(self, db: SQLRequest):
        self.active_account = None
        self.main_menu = "1. Create an account\n2.Log into account\n0. Exit"
        self.logged_in_menu = "1. Balance\n2. Add income\n3. Do transfer\n4. Close account\n5.Log out\n0. Exit"
        self.db = db

    @staticmethod
    def __generate_card_number():
        account_number = list(map(int, list("400000"))) + [random.randint(0, 9) for _ in range(9)]
        control_sum_digit = Bank.__control_sum_digit_func(account_number)
        card_number = "".join(list(map(str, account_number))) + str(control_sum_digit)
        return card_number

    @staticmethod
    def __control_sum_digit_func(account_number: list):
        account_number_interim = []
        for i in range(1, 16):
            if i % 2 == 0:
                account_number_interim.append(account_number[i - 1])
            else:
                if account_number[i - 1] * 2 > 9:
                    account_number_interim.append(account_number[i - 1] * 2 - 9)
                else:
                    account_number_interim.append(account_number[i - 1] * 2)
        sum_account_number_interim = sum(account_number_interim)
        if sum_account_number_interim % 10 == 0:
            digit = 0
        else:
            digit = 10 - sum_account_number_interim % 10
        return digit

    @staticmethod
    def is_correct_card_number(number: str):
        number_list_of_int = list(map(int, number))
        last_number = number_list_of_int.pop()
        return Bank.__control_sum_digit_func(number_list_of_int) == last_number

    @staticmethod
    def __generate_pin():
        pin = "".join([str(random.randint(0, 9)) for _ in range(4)])
        return pin

    @staticmethod
    def __generate_id():
        return random.randint(1, 9999)

    def create_account(self):
        card_generated = False
        id_generated = False
        account_id = None
        card_number = None
        while not card_generated:
            card_number = self.__generate_card_number()
            card_generated = self.db.is_uniq(uniq_type="number", uniq_object=card_number)
        while not id_generated:
            account_id = self.__generate_id()
            id_generated = self.db.is_uniq(uniq_type="id", uniq_object=account_id)
        pin = self.__generate_pin()
        return BankAccount(account_id, card_number, pin, 0)

    def login_handler(self):
        print(f"\nEnter your card number:")
        user_card_number = input()
        print(f"\nEnter your PIN:")
        pin_login = input()
        login_account = None
        wrong_card_number = (len(user_card_number) < 16 or not self.is_correct_card_number(user_card_number) or self.db.is_uniq(uniq_type="number", uniq_object=user_card_number))
        if not wrong_card_number:
            login_account = self.db.get_data(user_card_number)
        if wrong_card_number or login_account.pin != pin_login:
            return "Wrong card number or PIN!"
        elif login_account.pin == pin_login:
            self.active_account = login_account
            return "You have successfully logged in!"

    def check_balance(self):
        self.active_account = self.db.get_data(self.active_account.card_number)
        return self.active_account.balance

    def add_income(self):
        print(f"\nEnter income")
        income = int(input())
        self.active_account.balance += income
        self.db.update_balance(self.active_account)
        return "Income was added!"

    def do_transfer(self):
        print(f"\nEnter card number")
        transfer_card_number = input()
        if not self.is_correct_card_number(transfer_card_number):
            return "Probably you made a mistake in the card number. Please try again!"
        elif self.db.is_uniq(uniq_type="number", uniq_object=transfer_card_number):
            return "Such a card does not exist."
        else:
            transfer_account = self.db.get_data(transfer_card_number)
            print("Enter how much money you want to transfer:")
            sum_to_transfer = int(input())
        if self.active_account.balance < sum_to_transfer:
            return "Not enough money!"
        elif self.active_account.balance >= sum_to_transfer:
            self.active_account.balance -= sum_to_transfer
            transfer_account.balance += sum_to_transfer
            self.db.update_balance(self.active_account)
            self.db.update_balance(transfer_account)
            return "Success!"

    def close_account(self):
        self.db.delete_data(self.active_account)
        self.active_account = None
        return "The account has been closed!"

    def print_menu(self):
        if self.active_account is None:
            menu = self.main_menu
        else:
            menu = self.logged_in_menu
        print(menu)

    def menu(self, user_choice):
        if self.active_account is None:
            if user_choice == "1":
                created_account = self.create_account()
                self.db.insert_data(created_account)
                print(f"Your card has been created\nYour card number:\n{created_account.card_number}")
                print(f"Your card PIN:\n{created_account.pin}")
                self.print_menu()
            elif user_choice == "2":
                print(self.login_handler())
                self.print_menu()
        else:
            if user_choice == "1":
                print(self.check_balance())
                self.print_menu()
            elif user_choice == "2":
                print(self.add_income())
                self.print_menu()
            elif user_choice == "3":
                print(self.do_transfer())
                self.print_menu()
            elif user_choice == "4":
                print(self.close_account())
                self.print_menu()
            elif user_choice == "5":
                self.active_account = None
                print("You have successfully logged out!")
                self.print_menu()


bank_table = """(id INTEGER,
number TEXT,
pin TEXT,
balance INTEGER DEFAULT 0)"""
bank_db = SQLRequest.connection()
bank_db.create_table(bank_table)
bank = Bank(bank_db)

bank.print_menu()
user_choice = input()
while user_choice != "0":
    bank.menu(user_choice)
    user_choice = input()
print("Bye!")
