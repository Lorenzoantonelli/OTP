# OTP Generator

This script is an OTP manager, it can store secret keys and generate OTP code based on the [RFC 6238](https://tools.ietf.org/html/rfc6238) standard.

The idea is based on [bash-otp](https://github.com/poolpog/bash-otp), but with a different approach.

## Requirements

- [pyotp](https://pypi.org/project/pyotp/)
- [segno](https://pypi.org/project/segno/)
- [keyring](https://pypi.org/project/keyring/)

You can use the **requirements.txt** file to install this dependencies:

```bash
pip3 install -r requirements.txt
```

## Examples
* Store a new OTP:
    ```bash
    ./otp.py -a github
    ```
* Generate an OTP for a given service:
    ```bash
    ./otp.py -g github
    ```

* To copy automatically the OTP to the clipboard:
    ```bash
    ./otp.py -g github -c
    ```

## Usage
```
usage: otp.py [-h] [-a service_name] [-s] [-g service_name] [-d service_name]
              [-l] [-e export_file_path] [-i input_file_path] [-p] [-c]
              [--duration DURATION] [--digits DIGITS] [-x] [--delete-password]
              [--qr-code service_name]

OTP Manager

options:
  -h, --help            show this help message and exit
  -a service_name, --add service_name
                        Add a new OTP
  -s, --store           Store password
  -g service_name, --generate service_name
                        Generate OTP
  -d service_name, --delete service_name
                        Delete OTP
  -l, --list            List all OTP
  -e export_file_path, --export export_file_path
                        Export all OTP
  -i input_file_path, --import_otp input_file_path
                        Import all OTP
  -p, --print           Print all OTP
  -c, --copy            Copy OTP to clipboard
  --duration DURATION   Duration of the OTP
  --digits DIGITS       Number of digits of the OTP
  -x, --encrypted       Import/Export encrypted OTP instead of plain text
  --delete-password     Delete password from keyring
  --qr-code service_name
                        Generate QR code for OTP
```
