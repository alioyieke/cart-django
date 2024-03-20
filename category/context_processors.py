from .models import Category

# category links
def menu_links(request):
    links = Category.objects.all()
    return dict(links = links)