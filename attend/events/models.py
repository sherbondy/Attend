from django.db import models

# Create your models here.
class FacebookEvent(models.Model):
    facebook_event_id = models.CharField(max_length=20)
    facebook_user_id = models.CharField(max_length=20)
    def __unicode__(self):
        return self.facebook_event_id+" by "+self.facebook_user_id
    class Meta:
        ordering = ["facebook_event_id"]

