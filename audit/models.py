
from django.db import models
from django.conf import settings
class AuditLog(models.Model):
    user=models.ForeignKey(settings.AUTH_USER_MODEL,null=True,on_delete=models.SET_NULL)
    action=models.CharField(max_length=255)
    timestamp=models.DateTimeField(auto_now_add=True)
    object_repr=models.TextField()
    activity_id=models.IntegerField(null=True,blank=True)
    change_description=models.TextField(blank=True)

    def __str__(self):
        return f'{self.action} by {self.user} at {self.timestamp}'
    
    class Meta:
        ordering = ['-timestamp']