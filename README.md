# fn_download

A small script that downloads the daily news paper "Freiburger Nachrichten"

The script gets the credential information from a second shell script exporting the needed information as env variables


## config file
The config file has the following structure:
```bash
[FN-Credentials]
username = donaldduck
password = xyz

[Nextcloud-Credentials]
username = donaldduck
password = xyz

[SMTP]
server = <smtp server>
username = <sender mail account>
password = your secret....
port = 587

[RECEPIENT]
send = 1
addr = <recepient email address>
```
