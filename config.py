import configparser
import logging
import os
import syncer
from pathlib import Path
from string import Template



def create_config():
    logging.info("Creating new configfile")

    config = configparser.ConfigParser()
    config.add_section('Host')
    config.set('Host', 'Hostname', 'ldap://ldap.example.com')
    config['Host']['BaseDN'] = 'OU=people,dc=example,dc=com'
    config['Host']['DisplayName'] = 'Active Directory'
    config['Bind'] = {}
    config['Bind']['User'] = 'CN=admin,dc=example,dc=eu'
    config['Bind']['Password'] = 'password'
    config['LDAP params'] = {}
    config['LDAP params']['ObjectClass'] = 'user'
    config['LDAP params']['ObjectCategory'] = 'person'
    config['LDAP params']['Username'] = 'userPrincipalName'
    config['LDAP params']['Fullname'] = 'cn'
    config['LDAP params']['Mail Address'] = 'mail'
    config['LDAP params']['Active User'] = 'userAccountControl'
    config['MailCow'] = {}
    config['MailCow']['Hostname'] = 'https://mail.example.com'
    config['MailCow']['API-Key'] = 'XXXXXX-XXXXXX-XXXXXX-XXXXXX-XXXXXX'
    config['MailCow']['Sync-Interval'] = '300'
    with open('db/config.ini', 'w') as configfile:
        config.write(configfile)

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
    result['Username'] = config.get('LDAP params', 'Username')
    result['Fullname'] = config.get('LDAP params', 'Fullname')
    result['Mail Address'] = config.get('LDAP params', 'Mail Address')
    result['Active User'] = config.get('LDAP params', 'Active User')
    result['MailHostName'] = config.get('MailCow', 'Hostname')
    result['API-Key'] = config.get('MailCow', 'API-Key')
    result['Sync-Interval'] = config.get('MailCow', 'Sync-Interval')

    return result

def read_dovecot_passdb_conf_template():
    with open('templates/dovecot/ldap/passdb.conf') as f:
        data = Template(f.read())

    logging.info(syncer.config_file())

    config_file = syncer.config_file()
    logging.info(config_file)
    return data.substitute(
        ldap_host= config_file['HostName'],
        ldap_base_dn= config_file['BaseDN']
        )

def read_sogo_plist_ldap_template():
    with open('templates/sogo/plist_ldap') as f:
        data = Template(f.read())

    config_file = syncer.config_file

    return data.substitute(
        ldap_host=config_file['HostName'],
        ldap_base_dn=config_file['BaseDN'],
        ldap_uid_field=config_file['Username'],
        full_name_field=config_file['Fullname'],
        ldap_bind_dn=config_file['BindUser'],
        ldap_bind_dn_password=config_file['BindPassword'],
        display_name=config_file['Description']
        )

def read_dovecot_extra_conf():
    with open('templates/dovecot/extra.conf') as f:
        data = f.read()

    return data