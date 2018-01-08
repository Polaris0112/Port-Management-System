from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User


class MyUser(models.Model):
    user = models.OneToOneField(User)
    nickname = models.CharField(max_length=16)
    permission = models.IntegerField(default=2)

    def __unicode__(self):
        return self.user.username


class Port(models.Model):
    ipaddr = models.GenericIPAddressField(protocol='IPv4')
    port = models.IntegerField()
    acceptip = models.CharField(max_length=128,default="0.0.0.0")
    record_id = models.CharField(max_length=128,unique=True,default="record")
    usage = models.CharField(max_length=128)
    protocol = models.CharField(max_length=128)
    ssh_name = models.CharField(max_length=128)

    class META:
        ordering = ['ipaddr']

    def __unicode__(self):
        return self.name
    
class Host(models.Model):
    ipaddr = models.GenericIPAddressField(protocol='IPv4')
    hostname = models.CharField(max_length=128)
    ssh_name = models.CharField(max_length=128)

    class META:
        ordering = ['ipaddr']

    def __unicode__(self):
        return self.name

