import requests
import sys, os
from datetime import datetime
import configparser
import smtplib
from email.message import EmailMessage


def sendMail(cfg, to_addr, msg):
    from_addr = "michael.maeder@hefr.ch"

    server = smtplib.SMTP(host=cfg['SMTP']['server'],
                          port=cfg['SMTP']['port'])
    server.set_debuglevel(1)

    # create the message
    email_message = EmailMessage()
    email_message.set_content(msg)
    email_message['Subject'] = "Freiburger Nachrichten"
    email_message['From'] = from_addr
    email_message['To'] = to_addr

    server.send_message(email_message)
#    server.sendmail(from_addr, to_addr, msg.encode('ascii', 'ignore'))
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

    # write the file to the filesystem... this is for debugging
    # f = open('./out.pdf', 'wb')
    # f.write(r.content)
    # f.close()

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