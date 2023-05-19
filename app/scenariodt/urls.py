"""
URL configuration for app project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf.urls import include, url
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .views import knowledgeGraph

urlpatterns = [
    path('', views.main, name='main'),
    path('admin/', admin.site.urls),
    path('accounts/logout/', views.logout, name='logout'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/register/', views.register, name='register'),
    path('accounts/profile/', views.profile),
    path('configure_scenario/', views.configureScenario, name='configure_scenario'),
    path('new_scenario/', views.configureNewScenario, name='new_scenario'),
    path('select_scenario/', views.selectScenario, name='select_scenario'),
    path('reconfigure_scenario/', views.reconfigureScenario, name='reconfigure_scenario'),
    path('compare_scenarios/', views.compareScenarios, name='compare_scenarios'),
    path('share_scenario/', views.shareScenario, name='share_scenario'),
    path('execute_scenario/', views.executeScenario, name='execute_scenario'),
    path('knowledge_graph/', knowledgeGraph, name='knowledge_graph'),
    url('^django_plotly_dash/', include('django_plotly_dash.urls')),
]
