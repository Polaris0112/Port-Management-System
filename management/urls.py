from django.conf.urls import url
from management import views

urlpatterns = [
    url(r'^$', views.index, name='homepage'),
    url(r'^signup/$', views.signup, name='signup'),
    url(r'^dump_data/$', views.dump_data, name='dump_data'),
    url(r'^login/$', views.login, name='login'),
    url(r'^logout/$', views.logout, name='logout'),
    url(r'^set_password/$', views.set_password, name='set_password'),
    url(r'^add_host/$', views.add_host, name='add_host'),
    url(r'^add_port/$', views.add_port, name='add_port'),
    url(r'^view_port/$', views.view_port, name='view_port'), 
    url(r'^view_host/$', views.view_host, name='view_host'), 
    url(r'^export_csv/$', views.export_csv, name='export_csv'), 
    url(r'^import_csv/$', views.import_csv, name='import_csv'), 
]
