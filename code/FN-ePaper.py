import requests
import sys, os
from datetime import datetime
import configparser
import smtplib
import ssl
from email.message import EmailMessage
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders


def sendMail(cfg, to_addr, msg, atta):
    from_addr = "no-reply@moik.org"

    context = ssl.create_default_context()
    server = smtplib.SMTP(host=cfg['SMTP_server'],
                          port=cfg['SMTP_port'])
    # server.set_debuglevel(1)
    server.ehlo()
    server.starttls(context=context)
    server.ehlo()
    server.login(cfg['SMTP_user'], cfg['SMTP_pw'])

    # create the message
    message = MIMEMultipart()
    message['Subject'] = "Freiburger Nachrichten"
    message['From'] = from_addr
    message['To'] = to_addr
    message.attach(MIMEText(msg, 'plain'))

    attachement = MIMEBase("application", "octet-stream")
    attachement.set_payload(atta)
    encoders.encode_base64(attachement)
    pdfFilename = "FN_" + datetime.now().strftime('%Y%m%d') + ".pdf"
    attachement.add_header("Content-Disposition", f"attachement; filename={pdfFilename}")
    message.attach(attachement)
    text = message.as_string()
    server.sendmail(from_addr, to_addr, text)

    server.quit()




def getConfig():
    config = configparser.ConfigParser()
    # try to get the config file in the docker root first
    if not config.read('/code/config.rc'):
        if not config.read('./code/config.rc'):
            return None

    credentials = {
        'fn_user':config['FN-Credentials']['username'],
        'fn_pass':config['FN-Credentials']['password'],
        'nc_user': config['Nextcloud-Credentials']['username'],
        'nc_pass': config['Nextcloud-Credentials']['password'],
        'SMTP_server': config['SMTP']['server'],
        'SMTP_port': config['SMTP']['port'],
        'SMTP_user': config['SMTP']['username'],
        'SMTP_pw': config['SMTP']['password'],
        'recepient': config['RECEPIENT']['addr']
    }
    return credentials


def main():
    credentials = getConfig()
    if not credentials:
        print("ERROR: could not find the config file in the current directory: ", os.getcwd())
        return 1

    payload = {'name':credentials['fn_user'],
               'pass':credentials['fn_pass'],
               'form_id':'user_login',
               'op':'Anmelden'}

#    proxyDict = {
#        "http": '127.0.0.1:8080',
#        "https": '127.0.0.1:8080'
#    }

    try:
        r = requests.post('https://www.freiburger-nachrichten.ch/user/login', data=payload, allow_redirects=False)

    except requests.exceptions.ConnectionError as err:
        print(err)
        return 1

    # isolate the session id
    FNcookies=r.cookies

    try:
        r = requests.get('https://www.freiburger-nachrichten.ch/epaper/download_new', cookies=FNcookies)

    except requests.exceptions.ConnectionError as err:
        print(err)
        return 1

    if r.status_code != 200:
        return 1

    # # write the file to the filesystem... this is for debugging
    # f = open('./out.pdf', 'wb')
    # f.write(r.content)
    # f.close()

    mailMsg = "Hallo, hier die FN von heute. Gruss"
    addr = credentials['recepient']
    sendMail(credentials, addr, mailMsg, r.content)

    # write the document to nextcloud
    try:
        request_str = "https://nc.moik.org/remote.php/dav/files/mike/Documents-Reading/fn_" +\
                      datetime.now().strftime('%Y%m%d') + ".pdf"
        r = requests.put(request_str, data=r.content,
                         auth=(credentials['nc_user'], credentials['nc_pass']))
    except requests.exceptions.ConnectionError as err:
        print(err)
        return 1

    return 0



# this is the standard boilerplate that calls the main() function
if __name__ == '__main__':
    # sys.exit(main(sys.argv)) # used to give a better look to exists
    rtcode = main()
    sys.exit(rtcode)