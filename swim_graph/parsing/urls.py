from django.urls import path
from . import views


urlpatterns = [
    path('upload/',
         views.upload_file_view,
         name='upload'),
    path('report_setup/<int:session_id>/',
         views.report_setup_view,
         name='report_setup'),
    path('sessions/',
         views.sessions_list_view,
         name='sessions_list'),
    path('sessions/<int:session_id>/',
         views.session_results_view,
         name='session_results'),
]
