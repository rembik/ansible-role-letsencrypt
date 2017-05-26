# Ansible Role: Let's Encrypt private networks
**Setup** [Let's Encrypt](https://letsencrypt.org/) ACME client [dehydrated](https://github.com/lukas2511/dehydrated) with a bunch of [dns-01 hooks](https://github.com/lukas2511/dehydrated/wiki/Examples-for-DNS-01-hooks) on Debian/Ubuntu Linux servers, **automatically** sign/renew **certificate**s and **deploy** them to other Linux or Windows proxy-/webservers.

* [supported dns providers](#dns-providers)
* [supported proxy-/webservers](#proxy--or-webservers)

## Requirements
* `git` for setup Let's Encrypt ACME client on Debian/Ubuntu Linux servers
* optionally, `cron` for automatic certification and deployment on the Ansible Control Machine (Linux server)
* optionally, `logrotate` for rotating the playbook logs on the Ansible Control Machine (Linux server)

## Role Variables
Important variables are listed below, along with default values (see `vars/main.yml`). For all other default variables see `default/main.yml`.
Recommended, **declare this variables** in `host_vars` and `group_vars` inventory files!

* [Setup](#setup)
* [Certification](#certification)
* [Deployment](#deployment)
* [Automation](#automation)

### Setup
Following variables are associated with the setup process of the Let's Encrypt ACME client on Debian/Ubuntu Linux servers.

#### dehydrated
```
le_dehydrated_ca: "https://acme-staging.api.letsencrypt.org/directory"
le_dehydrated_ca_terms: "https://acme-staging.api.letsencrypt.org/terms"
```
***Overwrite!*** Switch certificate authority variables for production inventory from default *acme-staging* servers to *acme-v01* servers.

```
le_dehydrated_hook: "{{ le_dehydrated_hooks_dir }}/lexicon/{{ le_dns_lexicon_hook_file }}"
```
The default hook script for your dns-01 challenge.

```
le_dehydrated_contact_email:
```
***Overwrite!*** default contact email.

```
le_dehydrated_pkcs12_password: ''
```
Declare a secure password for generating and decrypting PKCS12 (.pfx) certificate files.

#### DNS Providers
```
le_dns_providers:
  - "lexicon"
  - "hetzner"
le_dns_lexicon_providers:
  - "cloudflare"
  - "cloudxns"
  - "digitalocean"
  - "dnsimple"
  - "dnsmadeeasy"
  - "dnspark"
  - "dnspod"
  - "easydns"
  - "luadns"
  - "namesilo"
  - "nsone"
  - "pointhq"
  - "rage4"
  - "route53"
  - "vultr"
  - "yandex"
  - "zonomi"
```
Supported dns providers are those provided by Lexicon (see [list]( https://github.com/AnalogJ/lexicon#providers)) and [Hetzner Robot](https://www.hetzner.de/us/hosting/domain/registrationrobot).

```
le_dns_provider: "cloudflare"
```
Choose default dns provider for dns-01 challenges. *Note:* use same name as listed in `le_dns_providers`, *lexicon* excluded.
Instead of *lexicon* use same name as in `le_dns_lexicon_providers`.

```
# Hetzner Robot
le_dns_hetzner_auth_username:
le_dns_hetzner_auth_password:

# Lexicon
le_dns_lexicon_auth_username:
le_dns_lexicon_auth_password:
le_dns_lexicon_auth_token:
```
***Overwrite!*** Default credentials for chosen default dns provider (see [lexicon](https://github.com/AnalogJ/lexicon#authentication) and [dehydrated-hetzner-hook](https://github.com/rembik/dehydrated-hetzner-hook#configuration) docs).

##### Hetzner Robot
```
le_dns_hetzner_language: "de"
le_dns_hetzner_dns_servers: "\"213.239.242.238\", \"213.133.105.6\", \"193.47.99.3\""
```
If used, make sure to set your default Hetzner Robot user-interface language and customize your Hetzner Nameservers ([doc](https://github.com/rembik/dehydrated-hetzner-hook#configuration)).

### Certification
Following dictionaries are required for the certification process and should be declared in the `host_vars` inventory file of Debian/Ubuntu Linux servers which will run the Let's Encrypt ACME client.
```
le_certificate:
    example_com:
        domain: "example.com"                   # required
        altnames: "www.test.com dev.test.com"   # optional
        challenge:                              # optional, overwrites default for specific domain
        webserver:                              # optional, currently not supported!
        dns_provider:                           # optional, overwrites default for specific domain
        auth_username:                          # optional, overwrites default for specific domain
        auth_password:                          # optional, overwrites default for specific domain
        auth_token:                             # optional, overwrites default for specific domain
        dns_provider:                           # optional, overwrites default for specific domain
le_certificates:                                # required dictionary list for certification process in role  
    - "{{ le_certificate.example_com }}"
```

### Deployment
```
le_deploy: false
```
Use the deployment flag [`false`,`true`,`'force'`] in playbooks to switch between setup/certificate `false` and deploy `true` tasks in this role
Note: When you optionally wish to force all certificates to be deployed to all webservers use `'force'`. Otherwise, when `true` only signed/renewed certificates will be deployed.

```
le_deploy2_webserver: "nginx"
```
Declare to which webserver signed/renewed certificates should be deployed to by default.
*Note:* use same name as listed in `le_deploy2_webservers`

```
le_deploy_certificate:
    example_com:
        domain: "example.com"                   # required
        webserver:                              # optional, overwrites default for specific domain
        force:                                  # optional, set true to always deploy certificate 
le_deploy_certificates:                         # required dictionary list for deployment process in role  
    - "{{ le_deploy_certificate.example_com }}"
```
These dictionaries are required for the deployment process and should be declared in the `host_vars` inventory file of proxy-/webservers where the certificates will be deployed to.
Proxy-/webserver specific variables for this deployment dictionaries are shown under the specific proxy-/webserver in this section. 

#### Proxy- or Webservers
```
le_deploy2_webservers:
  - "nginx"
  - "ms_iis"
  - "ms_exchange"
  - "sophos_utm"
```
Supported Proxy-/Webserver the certificates will be deployed to, are currently nginx (Linux), Microsoft IIS, Microsoft Exchange and Sophos UTM.

##### nginx
```
le_deploy2_nginx_certs_dir: "/etc/nginx/certs"
le_deploy2_nginx_reload_cmd: "/etc/init.d/nginx reload"
```
```
le_deploy_certificate:
    example_com:
        domain: "example.com"                   # required
        certs_dir:                              # optional, overwrites default for specific domain
```

##### Microsoft IIS
```
le_deploy2_ms_iis_site_name: "Default Web Site"
le_deploy2_ms_iis_ip: "*"
le_deploy2_ms_iis_port: 443
le_deploy2_ms_iis_host_header: ""
le_deploy2_ms_iis_sni: false
```
```
le_deploy_certificate:
    example_com:
        domain: "example.com"                   # required
        site_name:                              # optional, overwrites default for specific domain
        ip:                                     # optional, overwrites default for specific domain
        host_header:                            # optional, overwrites default for specific domain
        port:                                   # optional, overwrites default for specific domain
        sni:                                    # optional, overwrites default for specific domain
```
For more information about what happen during deployment and what this variables mean see [update-iis-certificate](https://github.com/rembik/update-iis-certificate#update-ms-iis-certificate).

##### Microsoft Exchange
None specific variables. For more information about what happen during deployment see [update-exchange-certificate](https://github.com/rembik/update-exchange-certificate#update-ms-exchange-certificate).

##### Sophos UTM
```
[ssh_connection]
transfer_method = scp
```
Sophos UTM doesn't support the default Ansible transfer method `sftp`, so change the transfer method in the Ansible Config `ansible.cfg` to `scp` instead.
```
le_deploy_certificate:
    example_com:
        domain: "example.com"                   # required
        ref:                                    # required
        ref_ca:                                 # required
```
For more information about what happen during deployment see [utm-update-certificate](https://github.com/mbunkus/utm-update-certificate). For detail instructions about how to get required certificate references `ref` and `ref_ca` see [ansible-letsencrypt-example Wiki](https://github.com/rembik/ansible-letsencrypt-example/wiki/Configure-Sophos-UTM#4-get-certificate-references)

### Automation
This role provided one optionally automation solution. For scheduled plays it creates cronjobs with `cron` and for rotating log files of the plays it uses `logrotate`.

```
le_cron_playbook_filename: "letsencrypt.yml"
le_cron_vault_password_file: "{{ playbook_dir }}/.vault"
le_cron_inventory_groups:
```
Therefore cron need the location of your [vault password file](http://docs.ansible.com/ansible/playbooks_vault.html#running-a-playbook-with-vault), the filename of the letsencrypt playbook which should be automated and a list of inventory groups the cronjobs should be differentiated by.
The cronjobs should be created during the setup process of the role (see example playbook).

#### Ansible Callbacks
This role comes with customized `mail_error` and `log_plays_rotatable` callback plugins. The `log_plays_rotatable` callback logs all playbooks per host and enable rotating the log files with `logrotate`.
`mail_error` mails to interested parties when the automated playbook fails. These parties can be differentiated per inventory group. 
Edit the Ansible Config `ansible.cfg` to enable the callbacks and config `mail_error` in `group_vars` inventory files as followed.
```
[default]
callback_whitelist = log_plays_rotatable, mail_error
```
```
err_mail_host: ''           #default: localhost
err_mail_port: ''           #default: '25'
err_mail_username: ''       #optional
err_mail_password: ''       #optional
err_mail_from: ''           #optional
err_mail_to: ''             #required
err_mail_cc: ''             #optional
err_mail_bcc: ''            #optional
```

## Dependencies
None.

## Usage
This role provides `setup`,`certificate` and `deploy` Ansible Tags to split the roll in three processes: **Setup**, **Certification** and **Deployment**.  

#### Example Playbook `letsencrypt.yml`
```
- hosts: letsencrypt
  vars:
    le_cron_inventory_groups:
      - "your_inventory_group"
  roles:
    - letsencrypt
  post_tasks:
    - block:
        - name: "letsencrypt : SETUP : config letsencrypt cronjobs (incl. mail_error) for inventory groups"
          include: "roles/letsencrypt/tasks/setup_cron.yml"
          with_items:
            - "{{ le_cron_inventory_groups }}"
          loop_control:
            loop_var: le_setup_cron_loop
        - name: "Ansible Playbook : SETUP : logrotate - config rotation"
          copy:
            src: roles/letsencrypt/files/setup/localhost/logrotate
            dest: /etc/logrotate.d/ansible_log_plays
            owner: root
            group: root
            mode: 0644
          delegate_to: 127.0.0.1
          run_once: true
      tags:
        - setup

- hosts: all
  roles:
    - { role: letsencrypt, le_deploy: true }
```
For a deeper understanding how to setup this role in an specific inventory environment and what configuration possibilities this role has, see [ansible-letsencrypt-example](https://github.com/rembik/ansible-letsencrypt-example).

```
$ sudo su 
$ cd /path/to/playbook
$ ansible-playbook letsencrypt.yml --vault-password-file .vault
```
After an initial manuel play the automated certificate cycle for your private network is finished. Note: When deploying to **[Sophos UTM](#sophos-utm)** better split the initial play with `-t setup,certificate` and `-t deploy` (see [Wiki](https://github.com/rembik/ansible-letsencrypt-example/wiki/Configure-Sophos-UTM)).

## License
MIT / BSD

## Author Information
This role was created in 2017 by Brian Rimek.
