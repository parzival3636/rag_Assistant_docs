from django.db import models

class Document(models.Model):
    STATUS_CHOICES = [
        ('P', 'Pending'),
        ('C', 'Completed'),
        ('F', 'Failed'),
    ]
    
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='documents/')
    file_size = models.IntegerField()
    file_type = models.CharField(max_length=10)
    page_count = models.IntegerField(default=0)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='P')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title