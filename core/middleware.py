"""
Middleware para Cultura T Educación — Multi-tenant y seguridad.
"""
from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import redirect


class ColegioMiddleware(MiddlewareMixin):
    """
    Middleware que inyecta el colegio del usuario en todas las vistas.
    Para usuarios autenticados, request.colegio contiene el colegio del usuario.
    """
    def process_request(self, request):
        if request.user.is_authenticated:
            from .models import Estudiante, PadreFamilia

            if request.user.rol == "rector":
                # Los rectores no tienen perfil vinculado a un colegio específico
                # Pueden ver todos los colegios (super-admin del tenant)
                request.colegio = None
            elif hasattr(request.user, "estudiante_profile"):
                request.colegio = request.user.estudiante_profile.colegio
            elif hasattr(request.user, "profesor_colegios"):
                request.colegio = request.user.profesor_colegios.first()
            elif hasattr(request.user, "padre_profile"):
                # Padres ven el colegio del primer hijo
                primera_relacion = request.user.padre_profile.estudiantes.first()
                request.colegio = primera_relacion.estudiante.colegio if primera_relacion else None
            else:
                request.colegio = None
        else:
            request.colegio = None
        return None


class RateLimitMiddleware(MiddlewareMixin):
    """Limitador simple de requests por IP para evitar abuso."""
    from collections import defaultdict
    from datetime import datetime, timedelta

    requests = defaultdict(list)

    def process_request(self, request):
        ip = request.META.get("REMOTE_ADDR", "unknown")
        now = datetime.now()
        window = timedelta(minutes=1)
        self.requests[ip] = [t for t in self.requests[ip] if t > now - window]
        if len(self.requests[ip]) > 100:  # Max 100 req/min
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("Demasiadas solicitudes.")
        self.requests[ip].append(now)
        return None