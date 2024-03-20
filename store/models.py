from django.db import models
from django.urls import reverse
from category.models import Category

# Create your models here.
# Products table
class Product(models.Model):
    product_name  = models.CharField(max_length = 100, unique = True)
    slug          = models.SlugField(max_length = 100, unique = True)
    description   = models.TextField(max_length = 350, blank = True)
    price         = models.IntegerField()
    images        = models.ImageField(upload_to='photos/products')
    stock         = models.IntegerField()
    is_available  = models.BooleanField(default = True)
    category      = models.ForeignKey(Category, on_delete = models.CASCADE)
    created_date  = models.DateTimeField(auto_now_add = True)
    modified_date = models.DateTimeField(auto_now = True)

    # single product details links
    def get_url(self):
        return reverse('product_detail', args = [self.category.slug, self.slug])

    def __str__(self):
        return self.product_name
