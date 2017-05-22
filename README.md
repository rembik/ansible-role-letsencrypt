# Ansible Role: Let's Encrypt private networks

**Setup** [Let's Encrypt](https://letsencrypt.org/) ACME client [dehydrated](https://github.com/lukas2511/dehydrated) with a bunch of [dns-01 hooks](https://github.com/lukas2511/dehydrated/wiki/Examples-for-DNS-01-hooks) on Debian/Ubuntu Linux servers, **automatically sign/renew** certificates and **deploy** them to other Linux or Windows proxy-/webservers.

* [supported dns providers](#dns-providers)
* [supported proxy-/webservers](#proxy--webservers)

## Requirements

* `git` for setup Let's Encrypt ACME client on Debian/Ubuntu Linux servers
* optionally, `cron` for automated playbooks on the Ansible management server (Linux server) for automatic certification and deployment
* optionally, `logrotate` for rotating the playbook logs on the Ansible management server (Linux server)

## Role Variables

Important variables are listed below, along with default values (see `vars/main.yml`). For all other default variables see `default/main.yml`.
Recommended, **declare this variables** in `host_vars` and `group_vars` inventory files!

### Setup
#### dehydrated

```
le_dehydrated_ca: "https://acme-staging.api.letsencrypt.org/directory"
le_dehydrated_ca_terms: "https://acme-staging.api.letsencrypt.org/terms"
```
**Overwrite!** Switch certificate authority variables for production inventory from default *acme-staging* servers to *acme-v01* servers.

```
le_dehydrated_hook: "{{ le_dehydrated_hooks_dir }}/lexicon/{{ le_dns_lexicon_hook_file }}"
```
The default hook script for your dns-01 challenge.

```
le_dehydrated_contact_email:
```
**Overwrite!** default contact email.

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
**Overwrite!** Default credentials for chosen default dns provider (see [lexicon](https://github.com/AnalogJ/lexicon#authentication) and [dehydrated-hetzner-hook](https://github.com/rembik/dehydrated-hetzner-hook#configuration) docs).

##### Hetzner Robot
```
le_dns_hetzner_language: "de"
le_dns_hetzner_dns_servers: "\"213.239.242.238\", \"213.133.105.6\", \"193.47.99.3\""
```
Make sure to set your default Hetzner Robot user-interface language and customize your Hetzner Nameservers ([doc](https://github.com/rembik/dehydrated-hetzner-hook#configuration)).

### Certificate
```

```

### Deployment
```
le_deploy: false
```
Use the deployment flag [`false`,`true`,`'force'`] in playbooks to switch between setup/certificate `false` and deploy `true` tasks in this role
Note: When you optionally wish to force all certificates to be deployed to all webservers use `'force'`. Otherwise, when `true` only signed/renewed certificates will deploy.

```
le_deploy2_webserver: "nginx"
```
Declare to which webserver signed/renewed certificates should be deployed to by default.
*Note:* use same name as listed in `le_deploy2.webservers`

#### Proxy-/Webservers

### Ansible Callbacks
This role comes with two customized `mail_error` and `log_plays_rotatable` callback plugins. The `log_plays_rotatable` callback logs all playbooks per host and enable rotating the log files.
`mail_error` mails to interested party when the automated playbook fails. These parties can be differentiated per inventory group. 
Edit the Ansible Config `ansible.cfg` to enable the callbacks and config `mail_error` in `group_vars` inventory files as followed.
```
[default]
callback_whitelist = log_plays_rotatable, mail_error
```
```
err_mail_host: ''           #default: localhost
err_mail_port: ''           #default: 25
err_mail_username: ''       #optional
err_mail_password: ''       #optional
err_mail_to: ''             #required
```

## Dependencies
None.

## Usage

#### Example Playbook
```
- hosts: letsencrypt
  vars:
    le_cron_inventory_groups:
      - "rimek_info"
  roles:
    - letsencrypt
  post_tasks:
    - block:
        - name: "letsencrypt : SETUP : config letsencrypt cronjobs (including mail_error) for inventory groups"
          include: "roles/letsencrypt/tasks/setup_cron.yml"
          with_items:
            - "{{ le_cron_inventory_groups }}"
          loop_control:
            loop_var: le_setup_cron_loop
        - name: "Ansible Playbook : logrotate - config rotation"
          copy:
            src: roles/letsencrypt/files/localhost/logrotate
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
### Initial Plays

```

```



## License
MIT / BSD

## Author Information
This role was created in 2017 by Brian Rimek.