# OTP Generator

This script generates a one-time password for a given secret key. It is based on the [RFC 6238](https://tools.ietf.org/html/rfc6238) standard.

It's basically a wrapper around the [oathtool](https://www.nongnu.org/oath-toolkit/) command line tool, providing a simple interface to store and retrieve the secret key for multiple accounts.

The idea is based on (bash-otp)[https://github.com/poolpog/bash-otp], but with a different approach.

## Requirements

- [oathtool](https://www.nongnu.org/oath-toolkit/)
- [keyring](https://pypi.org/project/keyring/)

On MacOS, you can install these dependencies using [Homebrew](https://brew.sh/) and **pip3**:

```bash
brew install oath-toolkit
pip3 install keyring
```

You can also use the requirements.txt file to install the dependencies:

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
usage: otp.py [-h] [-a service_name] [-g service_name] [-d service_name] [-l] [-e export_file_path]
              [-i input_file_path] [-p] [-c] [--duration DURATION] [--digits DIGITS] [-x]
              [--delete-password]

OTP Manager

options:
  -h, --help            show this help message and exit
  -a service_name, --add service_name
                        Add a new OTP
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
```


