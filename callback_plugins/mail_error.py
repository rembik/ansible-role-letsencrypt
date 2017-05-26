# -*- coding: utf-8 -*-
# Copyright 2017 Dag Wieers <dag@wieers.com>, Brian Rimek <brian@rimek.info>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import json
import smtplib

from ansible.module_utils.six import string_types
from ansible.module_utils._text import to_bytes
from ansible.plugins.callback import CallbackBase
from ansible.utils.color import colorize, hostcolor


class CallbackModule(CallbackBase):
    """
    This Ansible callback plugin mails errors to interested parties.
    
    This plugin makes use of the following environment variables:
        ERR_MAIL_HOST           (optional): mail server Default: localhost
        ERR_MAIL_PORT           (optional): mail server port. Default: 25
        ERR_MAIL_USERNAME       (optional): mail server username
        ERR_MAIL_PASSWORD       (optional): mail server password
        ERR_MAIL_FROM           (optional): email-adress the mail is being sent from and
                                            which may contain address and phrase portions.
        ERR_MAIL_TO             (required): email-address(es) the mail is being sent to.
                                            This is a comma-separated list, which may contain 
                                            address and phrase portions.
        ERR_MAIL_CC             (optional): email-address(es) for cc                     
        ERR_MAIL_BCC            (optional): email-address(es) for bcc
    
    """
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'notification'
    CALLBACK_NAME = 'mail_error'
    CALLBACK_NEEDS_WHITELIST = True
    
    
    def __init__(self, display=None):

        self.disabled = False

        super(CallbackModule, self).__init__(display=display)

        self.callback_retry = 0
        self.playbook_failure = False

    def mail(self, sender=None, subject=None, body=None):
        
        host = os.getenv('ERR_MAIL_HOST', 'localhost')
        port = os.getenv('ERR_MAIL_PORT', 25)
        username = os.getenv('ERR_MAIL_USERNAME')
        password = os.getenv('ERR_MAIL_PASSWORD')
        sender = os.getenv('ERR_MAIL_FROM','Ansible Notification <error@localhost>')
        to = os.getenv('ERR_MAIL_TO')
        cc = os.getenv('ERR_MAIL_CC')
        bcc = os.getenv('ERR_MAIL_BCC')

        if to is None:
            self.callback_retry += 1
            self._display.warning('Email-address(es) the error-mail is being sent '
                                  'to was not provided. The Email-address(es) '
                                  'can be provided using the `ERR_MAIL_TO` '
                                  'environment variable. Optional variables are: '
                                  '`ERR_MAIL_HOST`, `ERR_MAIL_PORT`, `ERR_MAIL_USERNAME`, '
                                  '`ERR_MAIL_PASSWORD`, `ERR_MAIL_FROM`, `ERR_MAIL_CC`, '
                                  '`ERR_MAIL_BCC`.')
        
        if self.callback_retry > 3:
            self.disabled = True
            self._display.warning('Error-mail Callback disabled for this '
                                  'run! Check provided environment variables: '
                                  'Host = `%s`, Port = `%s`, Username = `%s`, '
                                  'Password = `%s`, From = `%s`, To = `%s`, Cc = `%s`, Bcc = `%s`'
                                  % (host,port,username,password,sender,to,cc,bcc)))
        
        else:
            if sender is not None:
                sender = sender.replace('_','.')
            if subject is None:
                subject = '[localhost][Undefined]'
            if body is None:
                body = 'An error occurred for an undefined host!'
            
            b_sender = to_bytes(sender)
            b_to = to_bytes(to)
            b_cc = to_bytes(cc)
            b_bcc = to_bytes(bcc)
            b_subject = to_bytes(subject)
            b_body = to_bytes(body)

            b_content = b'From: %s\n' % b_sender
            b_content += b'To: %s\n' % b_to
            if cc:
                b_content += b'Cc: %s\n' % b_cc
            b_content += b'Subject: %s\n\n' % b_subject
            b_content += b_body
            b_addresses = b_to.split(b',')
            if cc:
                b_addresses += b_cc.split(b',')
            if bcc:
                b_addresses += b_bcc.split(b',')
            
            try:
                if port == '465':
                    server = smtplib.SMTP_SSL(host,port)
                else:
                    server = smtplib.SMTP(host,port)
                server.ehlo()
                if port == '587':
                    server.starttls()
                if username is not None and password is not None:
                    try:
                        server.login(username,password)
                        server.ehlo()
                    except smtplib.SMTPAuthenticationError:
                        self._display.warning('SMTP authentication went wrong. Most probably '
                                              'the server did not accept the username/password '
                                              'combination provided.')
            except smtplib.SMTPException as e:
                self.callback_retry += 1
                self._display.warning('Error occurred during establishment of a '
                                      'connection with the mail server:  %s' % str(e))

            for b_address in b_addresses:
              try:
                  server.sendmail(b_sender, b_address, b_content)
              except smtplib.SMTPException as e:
                  self._display.warning('Could not submit error-mail from %s to %s:  '
                                        '%s' % (b_sender,b_address,str(e)))
         
            server.quit()

    def v2_runner_on_failed(self, res, ignore_errors=False):

        host = res._host.get_name()
        if ignore_errors:
            return
        
        sender = 'Ansible Notification <error@%s>' % host
        attach = res._task.action
        if 'invocation' in res._result:
            attach = "%s:  %s" % (res._task.action, json.dumps(res._result['invocation']['module_args']))
                    
        prefix = '[%s][Failed]' % host
        subject = '%s %s' % (prefix,attach)
        body = 'A task failed for host ' + host + '!\n\n____TASK__________________\n%s\n\n' % attach
        if 'stdout' in res._result and res._result['stdout']:
            subject = '%s %s' % (prefix,res._result['stdout'].strip('\r\n').split('\n')[-1])
            body += '____STANDARD OUTPUT_______\n' + res._result['stdout'] + '\n\n'
        if 'stderr' in res._result and res._result['stderr']:
            subject = '%s %s' % (prefix,res._result['stderr'].strip('\r\n').split('\n')[-1])
            body += '____STANDARD ERROR________\n' + res._result['stderr'] + '\n\n'
        if 'msg' in res._result and res._result['msg']:
            subject = '%s %s' % (prefix,res._result['msg'].strip('\r\n').split('\n')[0])
            body += '____MESSAGE_______________\n' + res._result['msg'] + '\n\n'
        body += '____ERROR DUMP____________\n' + self._dump_results(res._result)
        
        self.playbook_failure = True
        self.mail(sender=sender, subject=subject, body=body)

    def v2_runner_on_unreachable(self, result):

        host = result._host.get_name()
        res = result._result

        sender = 'Ansible Notification <error@%s>' % host
        
        prefix = '[%s][Unreachable]' % host
        if isinstance(res, string_types):
            subject = '%s %s' % (prefix,res.strip('\r\n').split('\n')[-1])
            body = 'An error occurred for host ' + host + '!\n\n____MESSAGE_______________\n' + res
        else:
            subject = '%s %s' % (prefix,res['msg'].strip('\r\n').split('\n')[0])
            body = 'An error occurred for host ' + host + '!\n\n____MESSAGE_______________\n' + \
                   res['msg'] + '\n\n____ERROR DUMP____________\n' + str(res)
        
        self.playbook_failure = True
        self.mail(sender=sender, subject=subject, body=body)

    def v2_runner_on_async_failed(self, result):

        host = result._host.get_name()
        res = result._result

        sender = 'Ansible Notification <error@%s>' % host
        
        prefix = '[%s][Async failure]' % host
        if isinstance(res, string_types):
            subject = '%s %s' % (prefix,res.strip('\r\n').split('\n')[-1])
            body = 'An error occurred for host ' + host + '!\n\n____MESSAGE_______________\n' + res
        else:
            subject = '%s %s' % (prefix,res['msg'].strip('\r\n').split('\n')[0])
            body = 'An error occurred for host ' + host + '!\n\n____MESSAGE_______________\n' + \
                   res['msg'] + '\n\n____ERROR DUMP____________\n' + str(res)
        
        self.playbook_failure = True
        self.mail(sender=sender, subject=subject, body=body)
        
    def v2_playbook_on_stats(self, stats):
        
        if self.playbook_failure:
            
            subject = '[Playbook failed] Post failure recap'
            body = 'Error(s) occurred for host(s) in playbook!\n\n____PLAY RECAP____________\n'
            hosts = sorted(stats.processed.keys())
            for h in hosts:
                t = stats.summarize(h)
            
                body += "%s : %s %s %s %s\n" % (
                    hostcolor(h, t, False),
                    colorize('ok', t['ok'], None),
                    colorize('changed', t['changed'], None),
                    colorize('unreachable', t['unreachable'], None),
                    colorize('failed', t['failures'], None))
              
            self.playbook_failure = False
            self.mail(subject=subject, body=body)

