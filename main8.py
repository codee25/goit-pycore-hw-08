import pickle
from collections import UserDict
from datetime import datetime, date, timedelta
import sys


def save_data(book, filename="addressbook.pkl"):
    """Зберігає AddressBook у файл"""
    with open(filename, "wb") as f:
        pickle.dump(book, f)


def load_data(filename="addressbook.pkl"):
    """Завантажує AddressBook з файлу або створює нову, якщо файл відсутній"""
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()


class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class Name(Field):
    pass


class Phone(Field):
    def __init__(self, value):
        if not self.validate(value):
            raise ValueError("Phone number must contain exactly 10 digits.")
        super().__init__(value)

    @staticmethod
    def validate(value):
        return isinstance(value, str) and value.isdigit() and len(value) == 10


class Birthday(Field):
    def __init__(self, value):
        # Store birthday as a string in format DD.MM.YYYY (requirement)
        if isinstance(value, str):
            try:
                datetime.strptime(value, "%d.%m.%Y")  # validate format
                self.value = value
            except Exception:
                raise ValueError("Invalid date format. Use DD.MM.YYYY")
        else:
            raise ValueError("Birthday must be a string in format DD.MM.YYYY")

    def __str__(self):
        return self.value


class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone_number):
        phone = Phone(phone_number)
        self.phones.append(phone)

    def remove_phone(self, phone_number):
        phone = self.find_phone(phone_number)
        if phone:
            self.phones.remove(phone)
        else:
            raise ValueError("Phone not found.")

    def edit_phone(self, old, new):
        phone = self.find_phone(old)
        if not phone:
            raise ValueError("Old phone not found.")
        idx = self.phones.index(phone)
        self.phones[idx] = Phone(new)

    def find_phone(self, number):
        for phone in self.phones:
            if phone.value == number:
                return phone
        return None

    def add_birthday(self, birthday_str):
        self.birthday = Birthday(birthday_str)

    def __str__(self):
        phones = ", ".join(p.value for p in self.phones) if self.phones else "No phones"
        bday = str(self.birthday) if self.birthday else "No birthday"
        return f"Contact name: {self.name.value}, phones: {phones}, birthday: {bday}"


class AddressBook(UserDict):
    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name)

    def delete(self, name):
        if name in self.data:
            del self.data[name]
        else:
            raise KeyError("Not found.")

    def get_upcoming_birthdays(self):
        today = date.today()
        limit = today + timedelta(days=6)
        result = []

        for rec in self.data.values():
            if not rec.birthday:
                continue

            # rec.birthday.value is string 'DD.MM.YYYY' — parse to date for math
            try:
                bday_date = datetime.strptime(rec.birthday.value, "%d.%m.%Y").date()
            except Exception:
                continue

            bday = bday_date.replace(year=today.year)

            if bday < today:
                bday = bday_date.replace(year=today.year + 1)

            if today <= bday <= limit:
                greeting = bday
                if greeting.weekday() == 5:
                    greeting += timedelta(days=2)
                elif greeting.weekday() == 6:
                    greeting += timedelta(days=1)

                result.append({"name": rec.name.value, "birthday": greeting})

        return sorted(result, key=lambda x: x["birthday"])


def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            msg = str(e)
            if (
                "not enough values to unpack" in msg
                or "too many values to unpack" in msg
            ):
                return "Not enough or too many arguments provided for this command."
            return f"Invalid value: {msg}"
        except IndexError:
            return "Not enough arguments provided for the command."
        except KeyError:
            return "Contact not found."
        except AttributeError:
            # e.g., when record is None and code accesses its attributes
            return "Contact not found."
        except Exception as e:
            return f"An unexpected error occurred: {e}"

    return inner


@input_error
def add_contact(args, book):
    name, phone = args[0], args[1]
    record = book.find(name)

    if not record:
        record = Record(name)
        book.add_record(record)
        msg = "Contact added."
    else:
        msg = "Contact updated."

    record.add_phone(phone)
    return msg


@input_error
def change_contact(args, book):
    name, old, new = args[0], args[1], args[2]
    record = book.find(name)
    record.edit_phone(old, new)
    return "Phone updated."


@input_error
def show_phone(args, book):
    name = args[0]
    record = book.find(name)
    if not record.phones:
        return "No phones."
    return ", ".join(p.value for p in record.phones)


def show_all(book):
    if not book.data:
        return "Address book is empty."
    return "\n".join(str(r) for r in book.data.values())


@input_error
def add_birthday(args, book):
    name, bday = args[0], args[1]
    record = book.find(name)
    if not record:
        record = Record(name)
        book.add_record(record)
    record.add_birthday(bday)
    return "Birthday added."


@input_error
def show_birthday(args, book):
    name = args[0]
    record = book.find(name)
    if not record.birthday:
        return "No birthday."
    return str(record.birthday)


def birthdays(args, book):
    lst = book.get_upcoming_birthdays()
    if not lst:
        return "No birthdays in upcoming 7 days."

    result = []
    for item in lst:
        result.append(f"{item['birthday'].strftime('%d.%m.%Y')}: {item['name']}")
    return "\n".join(result)


def parse_input(text):
    parts = text.strip().split()
    if not parts:
        return "", []
    return parts[0].lower(), parts[1:]


def main():
    book = load_data()  # ← завантаження з файлу

    print("Welcome to the assistant bot!")

    while True:
        command, args = parse_input(input("Enter command: "))

        if command in ("close", "exit"):
            save_data(book)  # ← збереження у файл
            print("Good bye!")
            sys.exit()

        elif command == "hello":
            print("How can I help you?")

        elif command == "add":
            print(add_contact(args, book))

        elif command == "change":
            print(change_contact(args, book))

        elif command == "phone":
            print(show_phone(args, book))

        elif command == "all":
            print(show_all(book))

        elif command == "add-birthday":
            print(add_birthday(args, book))

        elif command == "show-birthday":
            print(show_birthday(args, book))

        elif command == "birthdays":
            print(birthdays(args, book))

        else:
            print("Unknown command.")


if __name__ == "__main__":
    main()
