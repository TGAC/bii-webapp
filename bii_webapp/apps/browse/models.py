# class B(models.Model):
#     b1=models.CharField(max_length=200)
#  
# class UserProfile(models.Model):
#     user = models.ForeignKey(User, unique=True)
#     url = models.URLField("Website", blank=True)
#     company = models.CharField(max_length=50, blank=True)

# class UserProfile(models.Model):
#     user = models.ForeignKey(User, unique=True)
#     website = models.CharField(max_length=30)
#     company = models.CharField(max_length=128)