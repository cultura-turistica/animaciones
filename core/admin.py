from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, Colegio, AnoEscolar, Estudiante, PadreFamilia, Materia, Nota


@admin.register(Usuario)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "rol", "is_active")
    list_filter = ("rol", "is_active", "is_staff")
    fieldsets = UserAdmin.fieldsets + (
        ("Info Adicional", {"fields": ("rol", "telefono", "foto")}),
    )


@admin.register(Colegio)
class ColegioAdmin(admin.ModelAdmin):
    list_display = ("nombre", "nit", "telefono", "activo")
    search_fields = ("nombre", "nit")
    list_filter = ("activo",)


@admin.register(AnoEscolar)
class AnoEscolarAdmin(admin.ModelAdmin):
    list_display = ("colegio", "ano", "fecha_inicio", "fecha_fin", "activo")
    list_filter = ("colegio", "activo", "ano")
    search_fields = ("colegio__nombre",)


@admin.register(Estudiante)
class EstudianteAdmin(admin.ModelAdmin):
    list_display = ("usuario", "colegio", "grado", "paralelo", "ano_escolar")
    list_filter = ("colegio", "grado", "ano_escolar")
    search_fields = ("usuario__username", "usuario__first_name", "usuario__last_name")


@admin.register(PadreFamilia)
class PadreFamiliaAdmin(admin.ModelAdmin):
    list_display = ("usuario", "telefono", "created_at")
    search_fields = ("usuario__username", "usuario__first_name")


@admin.register(Materia)
class MateriaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "colegio", "profesor")
    list_filter = ("colegio",)
    search_fields = ("nombre", "colegio__nombre")


@admin.register(Nota)
class NotaAdmin(admin.ModelAdmin):
    list_display = ("estudiante", "materia", "periodo", "valor", "fecha")
    list_filter = ("periodo", "materia__colegio", "ano_escolar")
    search_fields = ("estudiante__usuario__username",)
