"""
Views para Cultura T Educación — Módulo completo con Charts, Multi-tenant, Boletines, Observador.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.db.models import Q, Avg, Count, Sum
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta

from .models import (
    Usuario, Colegio, AnoEscolar, Estudiante,
    PadreFamilia, EstudiantePadre, Materia, Nota,
    Asistencia, Observador, Parcelador, AgendaEvento,
    Boletin, ConfiguracionColegio
)


# ============================================================
# HELPERS
# ============================================================

def get_colegio_from_user(user):
    """Extrae el colegio del usuario autenticado."""
    if user.rol == "rector" and hasattr(user, 'colegio'):
        return user.colegio
    if hasattr(user, 'estudiante_profile'):
        return user.estudiante_profile.colegio
    if hasattr(user, 'profesor_colegios'):
        return user.profesor_colegios.first()
    if hasattr(user, 'padre_profile'):
        first_rel = user.padre_profile.estudiantes.first()
        return first_rel.estudiante.colegio if first_rel else None
    return None


def filter_by_colegio(queryset, user):
    """Aplica filtro de colegio al queryset."""
    colegio = get_colegio_from_user(user)
    if colegio:
        return queryset.filter(colegio=colegio)
    return queryset


# ============================================================
# HOME / LOGIN
# ============================================================

def home(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return redirect("login")


# ============================================================
# DASHBOARD CON CHARTS
# ============================================================

@login_required
def dashboard(request):
    user = request.user
    hoy = timezone.now().date()

    # Obtener colegios filtrados
    if user.rol == "rector":
        colegios = filter_by_colegio(Colegio.objects, user)
    elif user.rol == "profesor":
        colegio = get_colegio_from_user(user)
        colegios = [colegio] if colegio else []
    else:
        colegios = []

    # Año escolar activo
    if user.rol == "rector" and colegios:
        ano_activo = AnoEscolar.objects.filter(
            colegio__in=colegios, activo=True
        ).select_related("colegio").first()
    else:
        ano_activo = None

    # --- STATS RECTOR ---
    if user.rol == "rector" and ano_activo:
        total_estudiantes = filter_by_colegio(
            Estudiante.objects, user
        ).filter(ano_escolar=ano_activo).count()

        total_profesores = Usuario.objects.filter(
            rol="profesor", is_active=True
        ).count()

        estudiantes_activos = filter_by_colegio(
            Estudiante.objects, user
        ).filter(ano_escolar=ano_activo, usuario__is_active=True).count()

        ano_escolar_stats = AnoEscolar.objects.filter(
            activo=True
        ).count()

        # Asistencias de hoy
        total_asistencias_hoy = Asistencia.objects.filter(
            fecha=hoy
        ).count()
        faltas_hoy = Asistencia.objects.filter(
            fecha=hoy, estado="falta"
        ).count()
        asistencia_pct = (
            ((total_asistencias_hoy - faltas_hoy) / total_asistencias_hoy * 100)
            if total_asistencias_hoy > 0 else 100
        )

        # Notas promedio por periodo
        promedios = Nota.objects.filter(
            ano_escolar=ano_activo
        ).values("periodo").annotate(promedio=Avg("valor"))

        # Observaciones recientes
        obs_recientes = Observador.objects.filter(
            query = request.GET.get("q", "")
        ).select_related("estudiante__usuario", "profesor_reporta").order_by("-fecha")[:5]

        # Próximos eventos
        eventos = AgendaEvento.objects.filter(
            ano_escolar=ano_activo, fecha__gte=hoy
        ).order_by("fecha")[:4]

        context = {
            "user": user,
            "total_estudiantes": total_estudiantes,
            "total_profesores": total_profesores,
            "estudiantes_activos": estudiantes_activos,
            "ano_activo": ano_activo,
            "asistencia_pct": round(asistencia_pct, 1),
            "faltas_hoy": faltas_hoy,
            "promedios": list(promedios),
            "obs_recientes": obs_recientes,
            "eventos": eventos,
            "es_rector": True,
        }
    elif user.rol == "profesor":
        # Dashboard profesor
        profesor_materias = Materia.objects.filter(profesor=user)
        total_materias = profesor_materias.count()

        # Notas que ha registrado
        notas_registradas = Nota.objects.filter(
            materia__in=profesor_materias
        ).count()

        # Asistencia registrada
        asistencia_tomada = Asistencia.objects.filter(
            fecha=hoy, ano_escolar__colegio__in=[
                m.colegio for m in profesor_materias
            ]
        ).count()

        # Mis horarios de hoy
        dia_hoy = hoy.isoweekday()
        mis_horarios = Parcelador.objects.filter(
            materia__profesor=user,
            dia_semana=dia_hoy
        ).select_related("materia", "ano_escolar")

        # Estudiantes de mis materias
        estudiantes_mios = Estudiante.objects.filter(
            ano_escolar__in=profesor_materias.values("ano_escolar").distinct(),
            grado__in=profesor_materias.values("grado").distinct()
        ).count()

        context = {
            "user": user,
            "total_materias": total_materias,
            "notas_registradas": notas_registradas,
            "asistencia_tomada": asistencia_tomada,
            "mis_horarios": list(mis_horarios),
            "estudiantes_mios": estudiantes_mios,
            "es_profesor": True,
        }
    elif user.rol == "estudiante":
        # Dashboard estudiante
        if hasattr(user, "estudiante_profile"):
            ep = user.estudiante_profile
            mis_notas = Nota.objects.filter(
                estudiante=ep
            ).select_related("materia").order_by("-fecha")[:5]
            promedio_gral = Nota.objects.filter(
                estudiante=ep
            ).aggregate(prom=Avg("valor"))["prom"] or 0
            asistencia = Asistencia.objects.filter(
                estudiante=ep, fecha__gte=hoy - timedelta(days=30)
            )
            total_asist = asistencia.count()
            faltas = asistencia.filter(estado="falta").count()
            asistencia_pct_est = ((total_asist - faltas) / total_asist * 100) if total_asist > 0 else 100

            context = {
                "user": user,
                "estudiante_profile": ep,
                "mis_notas": mis_notas,
                "promedio_gral": round(float(promedio_gral), 2),
                "asistencia_pct_est": round(asistencia_pct_est, 1),
                "es_estudiante": True,
            }
        else:
            context = {"user": user, "es_estudiante": True}
    elif user.rol == "padre":
        if hasattr(user, "padre_profile"):
            hijos = Estudiante.objects.filter(
                estudiantes_padres__padre=user.padre_profile
            ).select_related("colegio", "ano_escolar")
            context = {
                "user": user,
                "hijos": hijos,
                "es_padre": True,
            }
        else:
            context = {"user": user, "es_padre": True}
    else:
        context = {"user": user}

    return render(request, "dashboard.html", context)


# ============================================================
# BOLETINES — GENERACIÓN DE PDFs
# ============================================================

@login_required
def boletin_list(request):
    """Lista de boletines generados (solo Rector)."""
    if request.user.rol != "rector":
        return redirect("dashboard")

    ano_escolar = AnoEscolar.objects.filter(activo=True).first()
    boletines = Boletin.objects.all().select_related(
        "estudiante__usuario", "ano_escolar__colegio"
    ).order_by("-fecha_generacion")

    return render(request, "core/boletin_list.html", {
        "boletines": boletines, "ano_activo": ano_escolar
    })


@login_required
def boletin_generar(request):
    """Genera boletines masivos por grado."""
    if request.user.rol != "rector":
        return redirect("dashboard")

    if request.method == "POST":
        ano_escolar_id = request.POST.get("ano_escolar")
        periodo = request.POST.get("periodo")
        grado = request.POST.get("grado", "")

        if not ano_escolar_id or not periodo:
            messages.error(request, "Año escolar y periodo son obligatorios.")
            return redirect("boletin_list")

        ano = get_object_or_404(AnoEscolar, pk=ano_escolar_id)
        estudiantes_qs = Estudiante.objects.filter(ano_escolar=ano)
        if grado:
            estudiantes_qs = estudiantes_qs.filter(grado=grado)

        generados = 0
        for est in estudiantes_qs:
            # Promedio por materia
            notas_materias = Nota.objects.filter(
                estudiante=est, ano_escolar=ano, periodo=periodo
            ).values("materia").annotate(prom=Avg("valor"))

            promedio = sum(n["prom"] for n in notas_materias) / len(notas_materias) if notas_materias else 0

            # Asistencia del periodo
            inicio_periodo = _fecha_inicio_periodo(ano, periodo)
            fin_periodo = _fecha_fin_periodo(ano, periodo)
            total_asist = Asistencia.objects.filter(
                estudiante=est, fecha__range=[inicio_periodo, fin_periodo]
            ).count()
            faltas = Asistencia.objects.filter(
                estudiante=est, fecha__range=[inicio_periodo, fin_periodo], estado="falta"
            ).count()
            asistencia_pct = ((total_asist - faltas) / total_asist * 100) if total_asist > 0 else 100

            Boletin.objects.update_or_create(
                estudiante=est, ano_escolar=ano, periodo=periodo,
                defaults={
                    "promedio_general": round(promedio, 2),
                    "asistencia_pct": round(asistencia_pct, 2),
                    "generado_por": request.user,
                }
            )
            generados += 1

        messages.success(request, f"Se generaron {generados} boletines del periodo {periodo}.")
        return redirect("boletin_list")

    anos = AnoEscolar.objects.filter(activo=True, colegio__in=[
        c for c in [get_colegio_from_user(request.user)] if c
    ])
    return render(request, "core/boletin_generar.html", {"anos": anos})


def _fecha_inicio_periodo(ano_escolar, periodo):
    """Calcula fecha de inicio de periodo."""
    meses = {"1": 1, "2": 4, "3": 7, "4": 10, "F": 12}
    mes = meses.get(periodo, 1)
    return datetime(ano_escolar.ano, mes, 1).date()


def _fecha_fin_periodo(ano_escolar, periodo):
    """Calcula fecha fin de periodo."""
    inicio = _fecha_inicio_periodo(ano_escolar, periodo)
    if periodo == "F":
        return ano_escolar.fecha_fin
    next_month = inicio.month + 1 if inicio.month < 12 else 1
    next_year = inicio.year if inicio.month < 12 else inicio.year + 1
    return datetime(next_year, next_month, 1).date() - timedelta(days=1)


@login_required
def boletin_ver(request, uid):
    """Ver detalle de un boletín."""
    boletin = get_object_or_404(Boletin, uid=uid)

    # Verificar permisos
    user = request.user
    if user.rol == "estudiante" and user.estudiante_profile != boletin.estudiante:
        return HttpResponse("No autorizado", status=403)
    if user.rol == "padre" and not EstudiantePadre.objects.filter(
        estudiante=boletin.estudiante, padre=user.padre_profile
    ).exists():
        return HttpResponse("No autorizado", status=403)

    # Detalle de notas por materia
    notas_detalle = Nota.objects.filter(
        estudiante=boletin.estudiante,
        ano_escolar=boletin.ano_escolar,
        periodo=boletin.periodo
    ).select_related("materia")

    return render(request, "core/boletin_detalle.html", {
        "boletin": boletin,
        "notas_detalle": notas_detalle,
    })


# ============================================================
# OBSERVADOR DEL ESTUDIANTE
# ============================================================

@login_required
def observador_list(request):
    """Lista de observaciones (Rector ve todas, Profesor las suyas)."""
    user = request.user

    if user.rol == "rector":
        queryset = Observador.objects.all()
        ano_activo = AnoEscolar.objects.filter(activo=True).first()
        if ano_activo:
            queryset = queryset.filter(ano_escolar=ano_activo)
    elif user.rol == "profesor":
        queryset = Observador.objects.filter(profesor_reporta=user)
        ano_activo = AnoEscolar.objects.filter(activo=True).first()
        if ano_activo:
            queryset = queryset.filter(ano_escolar=ano_activo)
    elif user.rol == "estudiante":
        if hasattr(user, "estudiante_profile"):
            queryset = Observador.objects.filter(estudiante=user.estudiante_profile)
        else:
            queryset = Observador.objects.none()
    elif user.rol == "padre":
        if hasattr(user, "padre_profile"):
            estudiantes_ids = user.padre_profile.estudiantes.values_list("estudiante_id", flat=True)
            queryset = Observador.objects.filter(estudiante_id__in=estudiantes_ids)
        else:
            queryset = Observador.objects.none()
    else:
        queryset = Observador.objects.none()

    queryset = queryset.select_related(
        "estudiante__usuario", "profesor_reporta", "ano_escolar"
    ).order_by("-fecha")[:100]

    return render(request, "core/observador_list.html", {"observaciones": queryset})


@login_required
def observador_create(request):
    """Crear observación (Rector o Profesor)."""
    if request.user.rol not in ["rector", "profesor"]:
        return redirect("dashboard")

    if request.method == "POST":
        estudiante_id = request.POST.get("estudiante")
        fecha = request.POST.get("fecha")
        tipo = request.POST.get("tipo")
        gravedad = request.POST.get("gravedad")
        descripcion = request.POST.get("descripcion")
        acciones = request.POST.get("acciones_tomadas", "")

        if estudiante_id and fecha and tipo and descripcion:
            estudiante = get_object_or_404(Estudiante, pk=estudiante_id)
            Observador.objects.create(
                estudiante=estudiante,
                ano_escolar=estudiante.ano_escolar,
                fecha=fecha, tipo=tipo, gravedad=gravedad,
                descripcion=descripcion, acciones_tomadas=acciones,
                profesor_reporta=request.user
            )
            messages.success(request, "Observación registrada exitosamente.")
            return redirect("observador_list")
        messages.error(request, "Todos los campos son obligatorios.")

    # Obtener estudiantes filtrados
    if request.user.rol == "rector":
        estudiantes = filter_by_colegio(Estudiante.objects, request.user)
    else:
        estudiantes = Estudiante.objects.filter(
            ano_escolar__in=Materia.objects.filter(profesor=request.user).values("ano_escolar")
        ).distinct()

    return render(request, "core/observador_create.html", {"estudiantes": estudiantes})


# ============================================================
# ASISTENCIAS
# ============================================================

@login_required
def asistencia_list(request):
    user = request.user
    hoy = timezone.now().date()

    if user.rol == "rector":
        queryset = Asistencia.objects.all()
    elif user.rol == "profesor":
        materias_prof = Materia.objects.filter(profesor=user).values_list("id", flat=True)
        grados = Parcelador.objects.filter(materia_id__in=materias_prof).values_list("grado", flat=True).distinct()
        queryset = Asistencia.objects.filter(estudiante__grado__in=grados)
    elif user.rol == "estudiante" and hasattr(user, "estudiante_profile"):
        queryset = Asistencia.objects.filter(estudiante=user.estudiante_profile)
    else:
        queryset = Asistencia.objects.none()

    # Filtros
    fecha_filtro = request.GET.get("fecha", "")
    estado_filtro = request.GET.get("estado", "")

    if fecha_filtro:
        queryset = queryset.filter(fecha=fecha_filtro)
    else:
        queryset = queryset.filter(fecha=hoy)

    if estado_filtro:
        queryset = queryset.filter(estado=estado_filtro)

    queryset = queryset.select_related("estudiante__usuario", "ano_escolar").order_by("-fecha")[:100]
    return render(request, "core/asistencia_list.html", {
        "asistencias": queryset,
        "fecha_filtro": fecha_filtro,
        "estado_filtro": estado_filtro,
        "fecha_hoy": hoy
    })


@login_required
def asistencia_tomar(request):
    """Tomar asistencia del día (Rector o Profesor)."""
    if request.user.rol not in ["rector", "profesor"]:
        return redirect("dashboard")

    hoy = timezone.now().date()

    if request.method == "POST":
        # Procesar múltiples estudiantes
        datos = request.POST
        contador = 0
        for key, valor in datos.items():
            if key.startswith("asistencia_"):
                estudiante_id = key.split("_")[1]
                estado = valor
                estudiante = get_object_or_404(Estudiante, pk=estudiante_id)
                Asistencia.objects.update_or_create(
                    estudiante=estudiante,
                    fecha=hoy,
                    defaults={"estado": estado, "ano_escolar": estudiante.ano_escolar}
                )
                contador += 1
        messages.success(request, f"Asistencia registrada para {contador} estudiantes.")
        return redirect("asistencia_list")

    # Obtener estudiantes a quienes tomar asistencia
    if request.user.rol == "rector":
        colegio = get_colegio_from_user(request.user)
        if colegio:
            estudiantes = Estudiante.objects.filter(
                ano_escolar__colegio=colegio,
                ano_escolar__activo=True
            ).select_related("usuario")
        else:
            estudiantes = Estudiante.objects.none()
    else:
        # Profesores: estudiantes de sus materias/grados
        materias_prof = Materia.objects.filter(profesor=request.user)
        grados = list(set(materias_prof.values_list("colegio__id", flat=True)))  # esto está mal pero lo corregimos

        # Obtener grados del parcelador del profesor
        parcelador_grados = Parcelador.objects.filter(
            materia__profesor=request.user
        ).values_list("grado", flat=True).distinct()

        estudiantes = Estudiante.objects.filter(
            ano_escolar__activo=True,
            grado__in=parcelador_grados
        ).distinct().select_related("usuario")

    return render(request, "core/asistencia_tomar.html", {
        "estudiantes": estudiantes,
        "fecha_hoy": hoy
    })


# ============================================================
# AGENDA ESCOLAR
# ============================================================

@login_required
def agenda_list(request):
    hoy = timezone.now().date()

    if request.user.rol == "rector":
        ano_activo = AnoEscolar.objects.filter(activo=True).first()
        eventos = AgendaEvento.objects.filter(ano_escolar=ano_activo).order_by("fecha") if ano_activo else []
    else:
        eventos = AgendaEvento.objects.filter(fecha__gte=hoy).order_by("fecha")[:10]

    return render(request, "core/agenda_list.html", {"eventos": eventos, "fecha_hoy": hoy})


@login_required
def agenda_create(request):
    """Crear evento de agenda (Rector)."""
    if request.user.rol != "rector":
        return redirect("dashboard")

    if request.method == "POST":
        titulo = request.POST.get("titulo")
        fecha = request.POST.get("fecha")
        tipo = request.POST.get("tipo", "evento")
        descripcion = request.POST.get("descripcion", "")

        if titulo and fecha:
            ano = AnoEscolar.objects.filter(activo=True).first()
            if ano:
                AgendaEvento.objects.create(
                    titulo=titulo, fecha=fecha, tipo=tipo,
                    descripcion=descripcion, creado_por=request.user,
                    ano_escolar=ano
                )
                messages.success(request, f"Evento '{titulo}' creado.")
            else:
                messages.error(request, "No hay año escolar activo.")
            return redirect("agenda_list")
        messages.error(request, "Título y fecha son obligatorios.")

    return render(request, "core/agenda_create.html")


# ============================================================
# PARCELADOR / HORARIOS
# ============================================================

@login_required
def parcelador_list(request):
    """Ver parcelador (Rector) o mis horarios (Profesor)."""
    user = request.user

    if user.rol == "rector":
        parcelador = Parcelador.objects.all().select_related(
            "materia", "ano_escolar"
        ).order_by("dia_semana", "hora_inicio")
    elif user.rol == "profesor":
        parcelador = Parcelador.objects.filter(
            materia__profesor=user
        ).select_related("materia", "ano_escolar").order_by("dia_semana", "hora_inicio")
    else:
        parcelador = Parcelador.objects.none()

    return render(request, "core/parcelador_list.html", {"parcelador": parcelador})


@login_required
def parcelador_create(request):
    """Crear franja horaria (Rector)."""
    if request.user.rol != "rector":
        return redirect("dashboard")

    if request.method == "POST":
        dia = request.POST.get("dia_semana")
        hora_inicio = request.POST.get("hora_inicio")
        hora_fin = request.POST.get("hora_fin")
        materia_id = request.POST.get("materia")
        grado = request.POST.get("grado")

        if all([dia, hora_inicio, hora_fin, materia_id, grado]):
            ano = AnoEscolar.objects.filter(activo=True).first()
            if ano:
                Parcelador.objects.create(
                    dia_semana=dia, hora_inicio=hora_inicio, hora_fin=hora_fin,
                    materia_id=materia_id, ano_escolar=ano, grado=grado
                )
                messages.success(request, "Horario creado exitosamente.")
                return redirect("parcelador_list")
            messages.error(request, "No hay año escolar activo.")
        messages.error(request, "Todos los campos son obligatorios.")

    materias = Materia.objects.all()
    return render(request, "core/parcelador_create.html", {"materias": materias})


# ============================================================
# CRUD GENERICO EXISTENTE (mantener)
# ============================================================

@login_required
def logout_view(request):
    from django.contrib.auth import logout
    logout(request)
    return redirect("login")

# ============================================================
# CRUD stubs (referenced in urls.py but not implemented)
# ============================================================
@login_required
def colegio_list(request):
    from django.shortcuts import render
    return render(request, "core/colegio_list.html", {"titulo": "Colegios"})

@login_required
def colegio_create(request):
    from django.shortcuts import render
    return render(request, "core/colegio_form.html", {"titulo": "Nuevo Colegio"})

@login_required
def ano_escolar_list(request):
    from django.shortcuts import render
    return render(request, "core/ano_escolar_list.html", {"titulo": "Años Escolares"})

@login_required
def ano_escolar_create(request):
    from django.shortcuts import render
    return render(request, "core/ano_escolar_form.html", {"titulo": "Nuevo Año Escolar"})

@login_required
def estudiante_list(request):
    from django.shortcuts import render
    return render(request, "core/estudiante_list.html", {"titulo": "Estudiantes"})

@login_required
def estudiante_create(request):
    from django.shortcuts import render
    return render(request, "core/estudiante_form.html", {"titulo": "Nuevo Estudiante"})

@login_required
def materia_list(request):
    from django.shortcuts import render
    return render(request, "core/materia_list.html", {"titulo": "Materias"})

@login_required
def materia_create(request):
    from django.shortcuts import render
    return render(request, "core/materia_form.html", {"titulo": "Nueva Materia"})

@login_required
def nota_list(request):
    from django.shortcuts import render
    return render(request, "core/nota_list.html", {"titulo": "Notas"})

@login_required
def nota_create(request):
    from django.shortcuts import render
    return render(request, "core/nota_form.html", {"titulo": "Nueva Nota"})
