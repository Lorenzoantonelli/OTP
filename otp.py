#! /usr/bin/env python3

from os import listdir, remove, mkdir, path, getenv
import subprocess
from pathlib import Path
from sys import exit, argv
import json
import argparse
from getpass import getpass

FOLDER_NAME = "OTP_DATA"
EXECUTABLE_DIR = Path(__file__).parent.absolute()
ABSOLUTE_FOLDER_PATH = path.join(EXECUTABLE_DIR, FOLDER_NAME)


def init_folder():
    if FOLDER_NAME not in listdir(EXECUTABLE_DIR):
        mkdir(ABSOLUTE_FOLDER_PATH)


def get_password():
    password = getenv("OTP_PASSWORD")
    if not password:
        password = getpass("Insert the password: ")
        password_confirm = getpass("Confirm the password: ")
        if password != password_confirm:
            print("Passwords do not match")
            return get_password()
    return password


def encrypt_string(string, password):
    result = subprocess.check_output(['openssl', 'enc', '-aes-256-cbc', '-a', '-salt', '-pass', 'pass:' + password], input=string.encode('utf-8'))
    return result.decode('utf-8')

def decrypt_string(string, password):
    try:
        result = subprocess.check_output(['openssl', 'enc', '-aes-256-cbc', '-a', '-d', '-salt', '-pass', 'pass:' + password], input=string.encode('utf-8'), stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        print("Wrong password, please try again")
        exit(1)
    return result.decode('utf-8')


def save_new_otp(service_name, otp_digit=6, otp_period=30):
    password = get_password()

    otp_secret = input("OTP secret: ")


    if path.isfile(path.join(ABSOLUTE_FOLDER_PATH, service_name + ".json")):
        print(f"{service_name} already exists")
        exit(1)

    data = dict()
    data['service_name'] = service_name
    data['otp_secret'] = encrypt_string(otp_secret, password)
    data['otp_digit'] = otp_digit
    data['otp_period'] = otp_period

    with open(path.join(ABSOLUTE_FOLDER_PATH, service_name + ".json"), "w") as f:
        json.dump(data, f)

    print(f"Item {service_name} saved successfully")


def generate_otp(service_name, copy_to_clipboard=False):
    password = get_password()

    if not path.isfile(path.join(ABSOLUTE_FOLDER_PATH, service_name + ".json")):
        print(f"{service_name} does not exist")
        exit(1)

    with open(path.join(ABSOLUTE_FOLDER_PATH, service_name + ".json"), "r") as f:
        data = json.load(f)

    otp_secret = decrypt_string(data['otp_secret'], password)

    otp_digit = data['otp_digit']
    otp_period = data['otp_period']

    result = subprocess.check_output(['oathtool', '--totp', '-b', '-d', str(otp_digit), '-s', str(otp_period), otp_secret])[:-1]
    if copy_to_clipboard:
        subprocess.run(['pbcopy'], input=result, check=True)
    return result.decode('utf-8')


def delete_otp(service_name):
    if not path.isfile(path.join(ABSOLUTE_FOLDER_PATH, service_name + ".json")):
        print(f"{service_name} does not exist")
        exit(1)

    remove(path.join(ABSOLUTE_FOLDER_PATH, service_name + ".json"))
    print(f"Item {service_name} deleted successfully")


def list_otp():
    if path.isdir(ABSOLUTE_FOLDER_PATH):
        files = sorted(listdir(ABSOLUTE_FOLDER_PATH))
        for f in files:
            if f.endswith(".json"):
                print(f[:-5])
        if not files:
            print("No OTP found")


def export_all_otp(file_name):
    if path.isdir(ABSOLUTE_FOLDER_PATH):
        files = sorted(listdir(ABSOLUTE_FOLDER_PATH))
        data = dict()
        file_name = file_name if file_name.endswith(".json") else file_name + ".json"
        for otp_file in files:
            if otp_file.endswith(".json"):
                with open(path.join(ABSOLUTE_FOLDER_PATH, otp_file), "r") as f:
                    temp_data = json.load(f)
                    temp_data['otp_secret'] = decrypt_string(temp_data['otp_secret'], get_password())
                    data[temp_data['service_name']] = temp_data

        with open(file_name, "w") as f:
            json.dump(data, f)
        print(f"Exported {len(files)} items")
    

def import_all_otp(file_name):
    if not path.isfile(file_name):
        print(f"{file_name} does not exist")
        exit(1)

    with open(file_name, "r") as f:
        data = json.load(f)

    for service_name, otp_data in data.items():
        otp_data['otp_secret'] = encrypt_string(otp_data['otp_secret'], get_password())
        with open(path.join(ABSOLUTE_FOLDER_PATH, service_name + ".json"), "w") as f:
            json.dump(otp_data, f)

    print(f"Imported {len(data)} items")


def print_all_otp():
    if path.isdir(ABSOLUTE_FOLDER_PATH):
        files = sorted(listdir(ABSOLUTE_FOLDER_PATH))
        for f in files:
            if f.endswith(".json"):
                with open(path.join(ABSOLUTE_FOLDER_PATH, f), "r") as f:
                    data = json.load(f)
                print(f"{data['service_name']}: {generate_otp(data['service_name'])}")


def main():
    parser = argparse.ArgumentParser(description='OTP Manager')
    parser.add_argument('-a', '--add', metavar="service_name", help='Add a new OTP', type=str)
    parser.add_argument('-g', '--generate', metavar="service_name", help='Generate OTP', type=str)
    parser.add_argument('-d', '--delete', help='Delete OTP', metavar="service_name", type=str)
    parser.add_argument('-l', '--list', help='List all OTP', action='store_true')
    parser.add_argument('-e', '--export', help='Export all OTP', metavar="export_file_path", type=str)
    parser.add_argument('-i', '--import_otp', metavar="input_file_path", help='Import all OTP', type=str)
    parser.add_argument('-p', '--print', help='Print all OTP', action='store_true')
    parser.add_argument('-c', '--copy', help='Copy OTP to clipboard', action='store_true')
    parser.add_argument('--duration', help='Duration of the OTP', type=int, default=30)
    parser.add_argument('--digits', help='Number of digits of the OTP', type=int, default=6)
    args = parser.parse_args()

    init_folder()

    if args.add:
        save_new_otp(args.add, args.digits, args.duration)
    elif args.generate:
        print(generate_otp(args.generate, args.copy))
    elif args.delete:
        delete_otp(args.delete)
    elif args.list:
        list_otp()
    elif args.export:
        export_all_otp(args.export)
    elif args.import_otp:
        import_all_otp(args.import_otp)
    elif args.print:
        print_all_otp()
    else:
        parser.print_help()

if __name__ == '__main__':
    main()