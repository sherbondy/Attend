from django.db import models

# Create your models here.
class FacebookEvent(models.Model):
    facebook_event_id = models.CharField(max_length=20)
    def __unicode__(self):
        return self.facebook_event_id
    class Meta:
        ordering = ["facebook_event_id"]

