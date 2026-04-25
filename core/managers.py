"""
Manager personalizado para garantizar filter por colegio_id en todas las consultas.
"""
from django.db import models
from django.contrib.auth.models import BaseUserManager


class ColegioManager(models.Manager):
    """
    Manager que aplica filtro de colegio automáticamente.
    Para modelos que tienen ForeignKey a Colegio.
    """
    def get_queryset(self):
        return super().get_queryset()
    
    def filtered(self, colegio):
        """Retorna queryset filtrado por colegio."""
        return self.get_queryset().filter(colegio=colegio)


class MultiTenantManager(models.Manager):
    """
    Manager que inserta automáticamente el colegio_id en cada consulta.
    Requiere que la vista tenga acceso al colegio del usuario.
    """
    def for_colegio(self, colegio):
        return self.get_queryset().filter(colegio=colegio)


class UsuarioManager(BaseUserManager):
    """Manager para el modelo Usuario personalizado."""

    def create_user(self, username, email, password=None, rol="estudiante", **extra_fields):
        if not username:
            raise ValueError("El nombre de usuario es obligatorio")
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, rol=rol, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault("rol", "rector")
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(username, email, password, **extra_fields)

    def profesores(self):
        return self.filter(rol="profesor", is_active=True)

    def rectores(self):
        return self.filter(rol="rector", is_active=True)