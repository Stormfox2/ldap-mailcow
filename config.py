import configparser
import logging
import os
import syncer
from pathlib import Path
from string import Template



def create_config():
    config = open("db/config.ini", "w")
    config.add_section('Host')
    config.set('Host', 'Hostname', 'ldap://ldap.example.com')
    config.write()
    config.close()

def apply_config(config_file, config_data):
    if os.path.isfile(config_file):
        with open(config_file) as f:
            old_data = f.read()

        if old_data.strip() == config_data.strip():
            logging.info(f"Config file {config_file} unchanged")
            return False

        backup_index = 1
        backup_file = f"{config_file}.ldap_mailcow_bak"
        while os.path.exists(backup_file):
            backup_file = f"{config_file}.ldap_mailcow_bak.{backup_index}"
            backup_index += 1

        os.rename(config_file, backup_file)
        logging.info(f"Backed up {config_file} to {backup_file}")

    Path(os.path.dirname(config_file)).mkdir(parents=True, exist_ok=True)

    print(config_data, file=open(config_file, 'w'))

    logging.info(f"Saved generated config file to {config_file}")
    return True

def read_config():
    config = configparser.ConfigParser()
    config.read('db/config.ini')

    logging.info(config.sections())

    result = {}

    result['HostName'] = config.get('Host', 'Hostname')
    result['BaseDN'] = config.get('Host', 'BaseDN')
    result['DisplayName'] = config.get('Host', 'DisplayName')
    result['BindUser'] = config.get('Bind', 'User')
    result['BindPassword'] = config.get('Bind', 'Password')
    result['Username'] = config.get('LDAP param', 'Username')
    result['Fullname'] = config.get('LDAP param', 'Fullname')
    result['Mail Address'] = config.get('LDAP param', 'Mail Address')
    result['Active User'] = config.get('LDAP param', 'Active User')
    result['MailHostName'] = config.get('MailCow', 'Hostname')
    result['API-Key'] = config.get('MailCow', 'API-Key')
    result['Sync-Interval'] = config.get('MailCow', 'Sync-Interval')

    return result

def read_dovecot_passdb_conf_template():
    with open('templates/dovecot/ldap/passdb.conf') as f:
        data = Template(f.read())

    return data.substitute(
        ldap_host=config['Hostname'],
        ldap_base_dn=config['BaseDN']
        )

def read_sogo_plist_ldap_template():
    with open('templates/sogo/plist_ldap') as f:
        data = Template(f.read())

    config = syncer.getConfig()

    return data.substitute(
        ldap_host=config['Hostname'],
        ldap_base_dn=config['BaseDN'],
        ldap_uid_field=config['Username'],
        full_name_field=config['Fullname'],
        ldap_bind_dn=config['BindUser'],
        ldap_bind_dn_password=config['BindPassword'],
        display_name=config['DisplayName']
        )

def read_dovecot_extra_conf():
    with open('templates/dovecot/extra.conf') as f:
        data = f.read()

    return data