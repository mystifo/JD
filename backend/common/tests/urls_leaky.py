from django.urls import path

from .views_leaky import LeakyListView

urlpatterns = [path("leaky/", LeakyListView.as_view())]
