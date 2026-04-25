from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Home
    path("", views.home, name="home"),

    # Auth
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", views.logout_view, name="logout"),

    # Dashboard
    path("dashboard/", views.dashboard, name="dashboard"),

    # Boletines
    path("boletines/", views.boletin_list, name="boletin_list"),
    path("boletines/generar/", views.boletin_generar, name="boletin_generar"),
    path("boletines/ver/<uuid:uid>/", views.boletin_ver, name="boletin_ver"),
    path("boletines/mis/", views.boletin_ver, name="boletin_mis"),

    # Observador
    path("observador/", views.observador_list, name="observador_list"),
    path("observador/crear/", views.observador_create, name="observador_create"),
    path("observador/mis/", views.observador_list, name="observador_mis"),

    # Asistencias
    path("asistencias/", views.asistencia_list, name="asistencia_list"),
    path("asistencias/tomar/", views.asistencia_tomar, name="asistencia_tomar"),
    path("asistencias/mis/", views.asistencia_list, name="asistencia_mis"),

    # Agenda
    path("agenda/", views.agenda_list, name="agenda_list"),
    path("agenda/crear/", views.agenda_create, name="agenda_create"),

    # Parcelador
    path("parcelador/", views.parcelador_list, name="parcelador_list"),
    path("parcelador/crear/", views.parcelador_create, name="parcelador_create"),
    path("parcelador/mis-horarios/", views.parcelador_list, name="parcelador_mis_horarios"),

    # Colegio CRUD
    path("colegios/", views.colegio_list, name="colegio_list"),
    path("colegios/nuevo/", views.colegio_create, name="colegio_create"),

    # Año Escolar CRUD
    path("anos-escolares/", views.ano_escolar_list, name="ano_escolar_list"),
    path("anos-escolares/nuevo/", views.ano_escolar_create, name="ano_escolar_create"),

    # Estudiantes CRUD
    path("estudiantes/", views.estudiante_list, name="estudiante_list"),
    path("estudiantes/nuevo/", views.estudiante_create, name="estudiante_create"),

    # Materias CRUD
    path("materias/", views.materia_list, name="materia_list"),
    path("materias/nuevo/", views.materia_create, name="materia_create"),

    # Notas CRUD
    path("notas/", views.nota_list, name="nota_list"),
    path("notas/nuevo/", views.nota_create, name="nota_create"),
]