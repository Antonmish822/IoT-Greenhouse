from django.db import models

class Telemetry(models.Model):
    title = models.CharField('№ измерения', max_length=50)
    task = models.TextField('измерение')

    def __str__(self):
        return self.title
