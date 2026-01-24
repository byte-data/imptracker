
from django.db import models
from django.conf import settings
class UploadBatch(models.Model):
    year=models.IntegerField()
    uploaded_by=models.ForeignKey(settings.AUTH_USER_MODEL,null=True,on_delete=models.SET_NULL)
    uploaded_at=models.DateTimeField(auto_now_add=True)
    file_name=models.CharField(max_length=255)
