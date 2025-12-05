from django.urls import path
from . import views

app_name = 'children'

urlpatterns = [
    # Admin/Staff URLs
    path('', views.child_list_view, name='child-list'),
    path('<int:pk>/', views.child_detail_view, name='child-detail'),
    
    # Parent URLs
    path('my-children/', views.my_children_view, name='my-children'),
]