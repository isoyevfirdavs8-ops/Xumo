from django.db import models


class AboutItem(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    position = models.PositiveIntegerField(default=0, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('position', 'id')

    def __str__(self):
        return self.title