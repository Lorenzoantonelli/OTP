#! /usr/bin/env python3

import keyring
from os import listdir, remove, makedirs, path, environ
import subprocess
from pathlib import Path
import sys
import json
import argparse
from getpass import getpass
from datetime import datetime
import pyotp
from binascii import Error as binascii_error
import random
import string

SERVICE_ID = None
DATA_FOLDER = "~/.otp_data/OTP"
MAIN_FOLDER = "~/.otp_data"


def init_service_id():

    global SERVICE_ID
    service_id_json_path = path.join(MAIN_FOLDER, "service_id.json")

    if not path.isfile(service_id_json_path):
        SERVICE_ID = generate_service_id()

        with open(service_id_json_path, "w") as f:
            json.dump(SERVICE_ID, f)

    else:
        with open(service_id_json_path, "r") as f:
            SERVICE_ID = json.load(f)


def generate_service_id():
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(16))


def init_folders():
    global DATA_FOLDER
    global MAIN_FOLDER
    DATA_FOLDER = path.expanduser(DATA_FOLDER)
    MAIN_FOLDER = path.expanduser(MAIN_FOLDER)
    if not path.isdir(DATA_FOLDER):
        makedirs(DATA_FOLDER)


def get_password():
    password = keyring.get_password(SERVICE_ID, "password")
    if not password:
        password = getpass("Insert the password: ")
    return password


# TODO provide an option for the user to store the password in the keychain
def store_password_to_keychain(password):
    keyring.set_password(SERVICE_ID, "password", password)


def encrypt_string(string, password):
    result = subprocess.check_output(['openssl', 'enc', '-aes-256-cbc', '-a',
                                     '-salt', '-pbkdf2', '-pass', 'pass:' + password], input=string.encode('utf-8'))
    return result.decode('utf-8')


def decrypt_string(string, password):
    try:
        result = subprocess.check_output(['openssl', 'enc', '-aes-256-cbc', '-a', '-d', '-salt', '-pbkdf2',
                                         '-pass', 'pass:' + password], input=string.encode('utf-8'), stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        print("ERROR: Wrong password, please try again", file=sys.stderr)
        exit(1)
    return result.decode('utf-8')


def check_service_exists(service_name):
    return path.isfile(get_service_path(service_name))


def get_service_path(service_name):
    return path.join(DATA_FOLDER, service_name + ".json")


def save_new_otp(service_name, otp_digit=6, otp_period=30):
    password = get_password(double_check=True)

    otp_secret = input("OTP secret: ")
    if check_service_exists(service_name):
        print(f"{service_name} already exists")
        exit(1)

    # this will check is string is base32 encoded and correctly padded
    try:
        pyotp.TOTP(otp_secret).now()
    except binascii_error:
        print("ERROR: Secret is not base32 encoded", file=sys.stderr)
        exit(1)

    data = dict()
    data['service_name'] = service_name
    data['otp_secret'] = encrypt_string(otp_secret, password)
    data['otp_digit'] = otp_digit
    data['otp_period'] = otp_period

    with open(get_service_path(service_name), "w") as f:
        json.dump(data, f)

    print(f"Item {service_name} saved successfully")


def generate_otp(service_name, copy_to_clipboard=False):
    password = get_password()

    if not check_service_exists(service_name):
        print(f"ERROR: {service_name} does not exist", file=sys.stderr)
        exit(1)

    with open(get_service_path(service_name), "r") as f:
        data = json.load(f)

    otp_secret = decrypt_string(data['otp_secret'], password)

    otp_digit = data['otp_digit']
    otp_period = data['otp_period']

    totp = pyotp.TOTP(otp_secret, digits=otp_digit, interval=otp_period)
    result = totp.now()

    if copy_to_clipboard:
        text_to_clipboard(result.encode('utf-8'))

    return result


def text_to_clipboard(text):
    if sys.platform.startswith('linux'):
        if 'WAYLAND_DISPLAY' in environ:
            try:
                subprocess.run(['wl-copy'], input=text, check=True)
            except FileNotFoundError:
                print("wl-copy not found, is it installed?", file=sys.stderr)
                exit(0)
        elif 'DISPLAY' in environ:
            try:
                p = subprocess.Popen(['xsel', '-bi'], stdin=subprocess.PIPE)
                p.communicate(input=text)
            except FileNotFoundError:
                print("xsel not found, is it installed?", file=sys.stderr)
                exit(0)
    elif sys.platform.startswith('darwin'):
        subprocess.run(['pbcopy'], input=text, check=True)


def delete_otp(service_name):
    if not check_service_exists(service_name):
        print(f"ERROR: {service_name} does not exist", file=sys.stderr)
        exit(1)

    choice = input(f"Are you sure you want to delete {service_name}? [y/N] ")
    if choice.lower() == "y":
        remove(get_service_path(service_name))
        print(f"Item {service_name} deleted successfully")


def list_otp():
    if path.isdir(DATA_FOLDER):
        files = sorted(listdir(DATA_FOLDER))
        for f in files:
            if f.endswith(".json"):
                print(f[:-5])
        if not files:
            print("No OTP found", file=sys.stderr)


def export_all_otp(file_name):
    password = get_password()

    if path.isdir(DATA_FOLDER):
        files = sorted(listdir(DATA_FOLDER))
        data = dict()

        file_name = file_name[:-5] if file_name.endswith(
            ".json") else file_name
        file_name += "_" + datetime.now().strftime("%Y%m%d%H%M%S") + ".json"

        for otp_file in files:
            if otp_file.endswith(".json"):
                with open(path.join(DATA_FOLDER, otp_file), "r") as f:
                    temp_data = json.load(f)
                    temp_data['otp_secret'] = decrypt_string(
                        temp_data['otp_secret'], password)
                    data[temp_data['service_name']] = temp_data

        with open(file_name, "w") as f:
            json.dump(data, f)
        print(f"Exported {len(files)} items")


def export_all_encrypted_otp(file_name):
    if path.isdir(DATA_FOLDER):
        files = sorted(listdir(DATA_FOLDER))
        data = dict()
        file_name = file_name[:-5] if file_name.endswith(
            ".json") else file_name
        file_name += "_encrypted_" + datetime.now().strftime("%Y%m%d%H%M%S") + ".json"
        for otp_file in files:
            if otp_file.endswith(".json"):
                with open(path.join(DATA_FOLDER, otp_file), "r") as f:
                    temp_data = json.load(f)
                    data[temp_data['service_name']] = temp_data

        with open(file_name, "w") as f:
            json.dump(data, f)
        print(f"Exported {len(files)} items")


def import_all_otp(file_name):
    if not path.isfile(file_name):
        print(f"ERROR: {file_name} does not exist", file=sys.stderr)
        exit(1)

    with open(file_name, "r") as f:
        data = json.load(f)

    for service_name, otp_data in data.items():
        otp_data['otp_secret'] = encrypt_string(
            otp_data['otp_secret'], get_password())
        with open(get_service_path(service_name), "w") as f:
            json.dump(otp_data, f)

    print(f"Imported {len(data)} items")


def import_all_encrypted_otp(file_name):
    if not path.isfile(file_name):
        print(f"ERROR: {file_name} does not exist", file=sys.stderr)
        exit(1)

    with open(file_name, "r") as f:
        data = json.load(f)

    for service_name, otp_data in data.items():
        with open(get_service_path(service_name), "w") as f:
            json.dump(otp_data, f)

    print(f"Imported {len(data)} items")


def print_all_otp():
    if path.isdir(DATA_FOLDER):
        files = sorted(listdir(DATA_FOLDER))
        for f in files:
            if f.endswith(".json"):
                with open(path.join(DATA_FOLDER, f), "r") as f:
                    data = json.load(f)
                print(
                    f"{data['service_name']}: {generate_otp(data['service_name'])}")


def delete_password():
    choice = input(
        "Are you sure you want to delete the password from keyring? [y/N] ")
    if choice.lower() == "y":
        try:
            keyring.delete_password(SERVICE_ID, "password")
        except keyring.errors.PasswordDeleteError:
            print("Password not found", file=sys.stderr)
            exit(1)
        print("Password deleted successfully")


def generate_qr_code(service_name):
    if not check_service_exists(service_name):
        print(f"ERROR: {service_name} does not exist", file=sys.stderr)
        exit(1)

    with open(get_service_path(service_name), "r") as f:
        data = json.load(f)

    otp_secret = decrypt_string(data['otp_secret'], get_password())
    issuer = data['service_name']
    digits = data['otp_digit']
    period = data['otp_period']

    import segno
    qr = segno.make(
        f"otpauth://totp/{issuer}?secret={otp_secret}&issuer={issuer}&digits={digits}&period={period}")
    qr.terminal(compact=True)


def main():
    parser = argparse.ArgumentParser(description='OTP Manager')
    parser.add_argument('-a', '--add', metavar="service_name",
                        help='Add a new OTP', type=str)
    parser.add_argument('-g', '--generate',
                        metavar="service_name", help='Generate OTP', type=str)
    parser.add_argument('-d', '--delete', help='Delete OTP',
                        metavar="service_name", type=str)
    parser.add_argument('-l', '--list', help='List all OTP',
                        action='store_true')
    parser.add_argument('-e', '--export', help='Export all OTP',
                        metavar="export_file_path", type=str)
    parser.add_argument(
        '-i', '--import_otp', metavar="input_file_path", help='Import all OTP', type=str)
    parser.add_argument(
        '-p', '--print', help='Print all OTP', action='store_true')
    parser.add_argument(
        '-c', '--copy', help='Copy OTP to clipboard', action='store_true')
    parser.add_argument(
        '--duration', help='Duration of the OTP', type=int, default=30)
    parser.add_argument(
        '--digits', help='Number of digits of the OTP', type=int, default=6)
    parser.add_argument('-x', '--encrypted', help='Import/Export encrypted OTP instead of plain text',
                        action='store_true')
    parser.add_argument('--delete-password', help='Delete password from keyring',
                        action='store_true')
    parser.add_argument('--qr-code', help='Generate QR code for OTP',
                        metavar="service_name", type=str)
    args = parser.parse_args()

    init_folders()
    init_service_id()

    if args.add:
        save_new_otp(args.add, args.digits, args.duration)
    elif args.generate:
        print(generate_otp(args.generate, args.copy))
    elif args.delete:
        delete_otp(args.delete)
    elif args.list:
        list_otp()
    elif args.export:
        if args.encrypted:
            export_all_encrypted_otp(args.export)
        else:
            export_all_otp(args.export)
    elif args.import_otp:
        if args.encrypted:
            import_all_encrypted_otp(args.import_otp)
        else:
            import_all_otp(args.import_otp)
    elif args.qr_code:
        generate_qr_code(args.qr_code)
    elif args.print:
        print_all_otp()
    elif args.delete_password:
        delete_password()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
