import sys, os, string, time, datetime
import ldap

import filedb, api, config

from string import Template
from pathlib import Path

import logging
logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%d.%m.%y %H:%M:%S', level=logging.INFO)

config_file = {}

def main():
    global config_file
    configPath = Path("data/config.ini")
    logging.info(configPath.exists())
    if not configPath.is_file():
        config.create_config()
    config_file = config.read_config()

    passdb_conf = config.read_dovecot_passdb_conf_template()
    plist_ldap = config.read_sogo_plist_ldap_template()
    extra_conf = config.read_dovecot_extra_conf()

    passdb_conf_changed = config.apply_config('conf/dovecot/ldap/passdb.conf', config_data = passdb_conf)
    extra_conf_changed = config.apply_config('conf/dovecot/extra.conf', config_data = extra_conf)
    plist_ldap_changed = config.apply_config('conf/sogo/plist_ldap', config_data = plist_ldap)

    if passdb_conf_changed or extra_conf_changed or plist_ldap_changed:
        logging.info ("One or more config files have been changed, please make sure to restart dovecot-mailcow and sogo-mailcow!")

    api.api_host = config_file['MailHostName']
    api.api_key = config_file['API-Key']

    while (True):
        sync()
        interval = int(config_file['Sync-Interval'])
        logging.info(f"Sync finished, sleeping {interval} seconds before next cycle")
        time.sleep(interval)

def sync():
    logging.info(config_file.keys())
    ldap_connector = ldap.initialize(f"{config_file['HostName']}")
    ldap_connector.set_option(ldap.OPT_REFERRALS, 0)
    ldap_connector.simple_bind_s(config_file['BindUser'], config_file['BindPassword'])

    ldap_results = ldap_connector.search_s(config_file['BaseDN'], ldap.SCOPE_SUBTREE,
                '(&(objectClass=user)(objectCategory=person))', 
                [config['Username'], config['Full Name'], config['Active User']])

    ldap_results = map(lambda x: (
        x[1][config['Username']][0].decode(),
        x[1][config['Full Name']][0].decode(),
        False if int(x[1][config['Active User']][0].decode()) & 0b10 else True), ldap_results)

    filedb.session_time = datetime.datetime.now()

    for (email, ldap_name, ldap_active) in ldap_results:
        (db_user_exists, db_user_active) = filedb.check_user(email)
        (api_user_exists, api_user_active, api_name) = api.check_user(email)

        unchanged = True

        if not db_user_exists:
            filedb.add_user(email, ldap_active)
            (db_user_exists, db_user_active) = (True, ldap_active)
            logging.info (f"Added filedb user: {email} (Active: {ldap_active})")
            unchanged = False

        if not api_user_exists:
            api.add_user(email, ldap_name, ldap_active)
            (api_user_exists, api_user_active, api_name) = (True, ldap_active, ldap_name)
            logging.info (f"Added Mailcow user: {email} (Active: {ldap_active})")
            unchanged = False

        if db_user_active != ldap_active:
            filedb.user_set_active_to(email, ldap_active)
            logging.info (f"{'Activated' if ldap_active else 'Deactived'} {email} in filedb")
            unchanged = False

        if api_user_active != ldap_active:
            api.edit_user(email, active=ldap_active)
            logging.info (f"{'Activated' if ldap_active else 'Deactived'} {email} in Mailcow")
            unchanged = False

        if api_name != ldap_name:
            api.edit_user(email, name=ldap_name)
            logging.info (f"Changed name of {email} in Mailcow to {ldap_name}")
            unchanged = False

        if unchanged:
            logging.info (f"Checked user {email}, unchanged")

    for email in filedb.get_unchecked_active_users():
        (api_user_exists, api_user_active, _) = api.check_user(email)

        if (api_user_active and api_user_active):
            api.edit_user(email, active=False)
            logging.info (f"Deactivated user {email} in Mailcow, not found in LDAP")
        
        filedb.user_set_active_to(email, False)
        logging.info (f"Deactivated user {email} in filedb, not found in LDAP")

if __name__ == '__main__':
    main()
