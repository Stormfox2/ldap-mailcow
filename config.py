import configparser

with create_config(r'/db/config.yaml') as file:
    config = configparser.ConfigParser()
    config['Host']
    config['Host']['Hostname'] = 'ldap://ldap.example.com'
    config['Host']['BaseDN'] = 'OU=people,dc=example,dc=com'
    config['Host']['DisplayName'] = 'Active Directory'
    config['Bind']
    config['Bind']['User'] = 'CN=admin,dc=example,dc=eu'
    config['Bind']['Password'] = 'CN=admin,dc=example,dc=eu'
    config['LDAP params']
    config['LDAP params']['Username'] = 'userPrincipalName'
    config['LDAP params']['Fullname'] = 'cn'
    config['LDAP params']['Mail Address'] = 'mail'
    config['LDAP params']['Active User'] = 'userAccountControl'
    config['MailCow']
    config['MailCow']['Hostname'] = 'https://mail.example.com'
    config['MailCow']['API-Key'] = 'XXXXXX-XXXXXX-XXXXXX-XXXXXX-XXXXXX'
    config['MailCow']['Sync-Interval'] = 300
    if not Path('/db/config.ini').is_file():
        with open('/db/config.ini', 'w') as configfile:
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
    config.read('/db/config.ini')

    result = {}

    result['HostName'] = config['Host']['Hostname']
    result['BaseDN'] = config['Host']['BaseDN']
    result['DisplayName'] = config['Host']['DisplayName']
    result['BindUser'] = config['Bind']['User']
    result['BindPassword'] = config['Bind']['Password']
    result['Username'] = config['LDAP param']['Username']
    result['Fullname'] = config['LDAP param']['Fullname']
    result['Mail Address'] = config['LDAP param']['Mail Address']
    result['Active User'] = config['LDAP params']['Active User']
    result['MailHostName'] = config['MailCow']['Hostname']
    result['API-Key'] = config['MailCow']['API-Key']
    result['Sync-Interval'] = config['MailCow']['Sync-Interval']

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