"""
Modelos para Cultura T Educación — Plataforma Multi-tenant de Gestión Escolar
Versión profesional con módulos de Observador, Agenda y Boletines.
"""
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import uuid


# ============================================================
# USUARIO PERSONALIZADO CON ROLES
# ============================================================

class Usuario(AbstractUser):
    """
    Modelo de usuario personalizado con roles para el sistema escolar.
    Roles: Rector (admin del colegio), Profesor, Estudiante, Padre de Familia.
    """

    class Rol(models.TextChoices):
        RECTOR = "rector", "Rector"
        PROFESOR = "profesor", "Profesor"
        ESTUDIANTE = "estudiante", "Estudiante"
        PADRE = "padre", "Padre de Familia"

    class EstadoUsuario(models.TextChoices):
        ACTIVO = "activo", "Activo"
        INACTIVO = "inactivo", "Inactivo"
        SUSPENDIDO = "suspendido", "Suspendido"

    rol = models.CharField(max_length=20, choices=Rol.choices, default=Rol.ESTUDIANTE)
    telefono = models.CharField(max_length=20, blank=True, default="")
    foto = models.ImageField(upload_to="usuarios/fotos/", blank=True, null=True)
    estado = models.CharField(
        max_length=20, choices=EstadoUsuario.choices,
        default=EstadoUsuario.ACTIVO
    )
    fecha_nacimiento = models.DateField(blank=True, null=True)

    class Meta:
        db_table = "usuarios"
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    def __str__(self):
        return f"{self.username} ({self.get_rol_display()})"

    @property
    def es_admin(self):
        return self.rol == self.Rol.RECTOR

    @property
    def es_profesor(self):
        return self.rol == self.Rol.PROFESOR

    @property
    def es_estudiante(self):
        return self.rol == self.Rol.ESTUDIANTE

    @property
    def es_padre(self):
        return self.rol == self.Rol.PADRE

    @property
    def nombre_completo(self):
        return self.get_full_name() or self.username


# ============================================================
# MULTI-TENANT: COLEGIO
# ============================================================

class Colegio(models.Model):
    """
    Cada Colegio es un tenant independiente en el sistema multi-tenant.
    """
    nombre = models.CharField(max_length=200)
    nit = models.CharField(max_length=20, unique=True)
    direccion = models.TextField(blank=True, default="")
    ciudad = models.CharField(max_length=100, blank=True, default="")
    departamento = models.CharField(max_length=100, blank=True, default="")
    telefono = models.CharField(max_length=20, blank=True, default="")
    email = models.EmailField(blank=True, default="")
    website = models.URLField(blank=True, default="")
    logo = models.ImageField(upload_to="colegios/logos/", blank=True, null=True)
    activo = models.BooleanField(default=True)
    resolucion = models.CharField(max_length=50, blank=True, default="")
    dane = models.CharField(max_length=20, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "colegios"
        verbose_name = "Colegio"
        verbose_name_plural = "Colegios"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


# ============================================================
# AÑO ESCOLAR
# ============================================================

class AnoEscolar(models.Model):
    """
    Año escolar activo dentro de un colegio.
    """
    class EstadoAnoEscolar(models.TextChoices):
        ACTIVO = "activo", "Activo"
        CERRADO = "cerrado", "Cerrado"
        PENDIENTE = "pendiente", "Pendiente"

    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name="anos_escolares")
    ano = models.IntegerField()
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    estado = models.CharField(
        max_length=20, choices=EstadoAnoEscolar.choices,
        default=EstadoAnoEscolar.ACTIVO
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "anos_escolares"
        verbose_name = "Año Escolar"
        verbose_name_plural = "Años Escolares"
        unique_together = ["colegio", "ano"]
        ordering = ["-ano"]

    def __str__(self):
        return f"{self.colegio.nombre} - {self.ano}"


# ============================================================
# ESTUDIANTE
# ============================================================

class Estudiante(models.Model):
    """
    Estudiante vinculado a un colegio y año escolar.
    """
    GRADO_CHOICES = [
        ("0", "Transición"),
        ("1", "1°"),
        ("2", "2°"),
        ("3", "3°"),
        ("4", "4°"),
        ("5", "5°"),
        ("6", "6°"),
        ("7", "7°"),
        ("8", "8°"),
        ("9", "9°"),
        ("10", "10°"),
        ("11", "11°"),
    ]
    TIPO_DOC_CHOICES = [
        ("CC", "Cédula de Ciudadanía"),
        ("RC", "Registro Civil"),
        ("TI", "Tarjeta de Identidad"),
        ("CE", "Cédula de Extranjería"),
        ("PA", "Pasaporte"),
    ]

    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name="estudiante_profile")
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name="estudiantes")
    ano_escolar = models.ForeignKey(AnoEscolar, on_delete=models.CASCADE, related_name="estudiantes")
    grado = models.CharField(max_length=2, choices=GRADO_CHOICES, default="1")
    paralelo = models.CharField(max_length=5, blank=True, default="A")
    tipo_documento = models.CharField(max_length=5, choices=TIPO_DOC_CHOICES, default="RC")
    numero_documento = models.CharField(max_length=20, blank=True, default="")
    fecha_nacimiento = models.DateField(blank=True, null=True)
    lugar_nacimiento = models.CharField(max_length=200, blank=True, default="")
    _genero = models.CharField(max_length=1, blank=True, default="")
    grupo_sanguineo = models.CharField(max_length=5, blank=True, default="")
    eps = models.CharField(max_length=200, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "estudiantes"
        verbose_name = "Estudiante"
        verbose_name_plural = "Estudiantes"

    def __str__(self):
        return f"{self.usuario.get_full_name() or self.usuario.username} - {self.grado}{self.paralelo}"

    @property
    def nombre_completo(self):
        return self.usuario.get_full_name() or self.usuario.username


# ============================================================
# PADRE DE FAMILIA
# ============================================================

class PadreFamilia(models.Model):
    """
    Padre de familia vinculado a sus hijos estudiantes.
    """
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name="padre_profile")
    telefono = models.CharField(max_length=20, blank=True, default="")
    tipo_documento = models.CharField(max_length=5, default="CC")
    numero_documento = models.CharField(max_length=20, blank=True, default="")
    ocupacion = models.CharField(max_length=100, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "padres_familia"
        verbose_name = "Padre de Familia"
        verbose_name_plural = "Padres de Familia"

    def __str__(self):
        return f"{self.usuario.get_full_name() or self.usuario.username}"

    @property
    def nombre_completo(self):
        return self.usuario.get_full_name() or self.usuario.username


class EstudiantePadre(models.Model):
    """
    Relación many-to-many entre estudiantes y sus padres.
    """
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE)
    padre = models.ForeignKey(PadreFamilia, on_delete=models.CASCADE)
    es_principal = models.BooleanField(default=True)

    class Meta:
        db_table = "estudiantes_padres"
        unique_together = ["estudiante", "padre"]


# ============================================================
# MATERIA / AREA
# ============================================================

class Materia(models.Model):
    """
    Materia/Asignatura dentro de un colegio, asignada a un profesor.
    """
    nombre = models.CharField(max_length=200)
    abreviatura = models.CharField(max_length=20, blank=True, default="")
    area = models.CharField(max_length=100, blank=True, default="")
    intensidad_horaria = models.IntegerField(default=0, help_text="Horas semanales")
    colegio = models.ForeignKey(Colegio, on_delete=models.CASCADE, related_name="materias")
    profesor = models.ForeignKey(
        Usuario, on_delete=models.SET_NULL, null=True, blank=True,
        limit_choices_to={"rol": Usuario.Rol.PROFESOR}
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "materias"
        verbose_name = "Materia"
        verbose_name_plural = "Materias"
        unique_together = ["nombre", "colegio"]
        ordering = ["area", "nombre"]

    def __str__(self):
        return f"{self.nombre} - {self.colegio.nombre}"


# ============================================================
# NOTAS (GRADES)
# ============================================================

class Nota(models.Model):
    """
    Registro de nota para un estudiante en una materia específica.
    """
    PERIODO_CHOICES = [
        ("1", "Periodo 1"),
        ("2", "Periodo 2"),
        ("3", "Periodo 3"),
        ("4", "Periodo 4"),
        ("F", "Final"),
    ]

    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE, related_name="notas")
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE, related_name="notas")
    ano_escolar = models.ForeignKey(AnoEscolar, on_delete=models.CASCADE, related_name="notas")
    periodo = models.CharField(max_length=2, choices=PERIODO_CHOICES, default="1")
    valor = models.DecimalField(max_digits=5, decimal_places=2)
    observacion = models.TextField(blank=True, default="")
    fecha = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "notas"
        verbose_name = "Nota"
        verbose_name_plural = "Notas"
        unique_together = ["estudiante", "materia", "ano_escolar", "periodo"]
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.estudiante} - {self.materia} ({self.periodo}): {self.valor}"


# ============================================================
# ASISTENCIAS
# ============================================================

class Asistencia(models.Model):
    """
    Registro diario de asistencia de un estudiante.
    """
    class EstadoAsistencia(models.TextChoices):
        ASISTIO = "asistio", "Asistió"
        FALTA = "falta", "Falta"
        TARDE = "tarde", "Llegó tarde"
        JUSTIFICADO = "justificado", "Justificado"

    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE, related_name="asistencias")
    ano_escolar = models.ForeignKey(AnoEscolar, on_delete=models.CASCADE, related_name="asistencias")
    fecha = models.DateField()
    estado = models.CharField(max_length=20, choices=EstadoAsistencia.choices, default=EstadoAsistencia.ASISTIO)
    observacion = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "asistencias"
        verbose_name = "Asistencia"
        verbose_name_plural = "Asistencias"
        unique_together = ["estudiante", "fecha"]
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.estudiante} - {self.fecha}: {self.get_estado_display()}"


# ============================================================
# OBSERVADOR DEL ESTUDIANTE (Diario)
# ============================================================

class Observador(models.Model):
    """
    Observador del Estudiante — registro de eventos diarios.
    Tipo: comportamiento (positivo/negativo), llamado de atención, observación académica.
    """
    class TipoObservacion(models.TextChoices):
        POSITIVO = "positivo", "Acto Positivo"
        NEGATIVO = "negativo", "Acto Negativo"
        LLAMADO = "llamado", "Llamado de Atención"
        ACADEMICO = "academico", "Observación Académica"
        FALTAS = "faltas", "Registro de Faltas"

    class Gravedad(models.TextChoices):
        LEVE = "leve", "Leve"
        MODERADO = "moderado", "Moderado"
        GRAVE = "grave", "Grave"
        MUY_GRAVE = "muy_grave", "Muy Grave"

    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE, related_name="observaciones")
    ano_escolar = models.ForeignKey(AnoEscolar, on_delete=models.CASCADE, related_name="observaciones")
    fecha = models.DateField(default=timezone.now)
    tipo = models.CharField(max_length=20, choices=TipoObservacion.choices, default=TipoObservacion.POSITIVO)
    gravedad = models.CharField(max_length=20, choices=Gravedad.choices, default=Gravedad.LEVE)
    descripcion = models.TextField()
    profesor_reporta = models.ForeignKey(
        Usuario, on_delete=models.SET_NULL, null=True, blank=True,
        limit_choices_to={"rol": Usuario.Rol.PROFESOR}
    )
    acciones_tomadas = models.TextField(blank=True, default="")
    fecha_seguimiento = models.DateField(blank=True, null=True)
    resuelto = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "observadores"
        verbose_name = "Observador"
        verbose_name_plural = "Observadores"
        ordering = ["-fecha"]

    def __str__(self):
        return f"[{self.get_tipo_display()}] {self.estudiante} - {self.fecha}"


# ============================================================
# AGENDA ESCOLAR / PARCELADOR
# ============================================================

class Parcelador(models.Model):
    """
    Parcelador de clase — programación semanal de horarios por grado.
    Cada registro = una franja horaria específica.
    """
    dia_semana = models.IntegerField(choices=[
        (1, "Lunes"), (2, "Martes"), (3, "Miércoles"),
        (4, "Jueves"), (5, "Viernes"), (6, "Sábado")
    ])
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE, related_name="horarios")
    ano_escolar = models.ForeignKey(AnoEscolar, on_delete=models.CASCADE, related_name="parcelador")
    grado = models.CharField(max_length=2)  # Se filtra por grado dentro del colegio del año escolar
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "parceladores"
        verbose_name = "Parcelador"
        verbose_name_plural = "Parceladores"
        ordering = ["dia_semana", "hora_inicio"]
        unique_together = ["dia_semana", "hora_inicio", "ano_escolar", "grado"]

    def __str__(self):
        return f"{self.get_dia_semana_display()} {self.hora_inicio}-{self.hora_fin}: {self.materia.nombre}"


class AgendaEvento(models.Model):
    """
    Agenda de eventos escolares: fechas de exámenes, actividades, reuniones.
    """
    class TipoEvento(models.TextChoices):
        EVENTO = "evento", "Evento"
        EXAMEN = "examen", "Examen"
        REUNION = "reunion", "Reunión"
        ACTIVIDAD = "actividad", "Actividad Extra"
        ENTREGA = "entrega", "Fecha de Entrega"

    ano_escolar = models.ForeignKey(AnoEscolar, on_delete=models.CASCADE, related_name="eventos")
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, default="")
    fecha = models.DateField()
    hora = models.TimeField(blank=True, null=True)
    tipo = models.CharField(max_length=20, choices=TipoEvento.choices, default=TipoEvento.EVENTO)
    grado = models.CharField(max_length=2, blank=True, default="", help_text="Grados afectados (vacío = todos)")
    creado_por = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "agenda_eventos"
        verbose_name = "Evento"
        verbose_name_plural = "Eventos"
        ordering = ["fecha"]

    def __str__(self):
        return f"{self.titulo} - {self.fecha}"


# ============================================================
# BOLETINES
# ============================================================

class Boletin(models.Model):
    """
    Boletín informativo generado por periodo.
    Cada estudiante tiene un boletín por periodo por año escolar.
    """
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE, related_name="boletines")
    ano_escolar = models.ForeignKey(AnoEscolar, on_delete=models.CASCADE, related_name="boletines")
    periodo = models.CharField(max_length=2, choices=Nota.PERIODO_CHOICES, default="1")
    promedio_general = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    lugar = models.IntegerField(default=0)
    observaciones_generales = models.TextField(blank=True, default="")
    asistencia_pct = models.DecimalField(max_digits=5, decimal_places=2, default=100.0)
    generado_por = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True)
    fecha_generacion = models.DateTimeField(auto_now_add=True)
    uid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    class Meta:
        db_table = "boletines"
        verbose_name = "Boletín"
        verbose_name_plural = "Boletines"
        unique_together = ["estudiante", "ano_escolar", "periodo"]

    def __str__(self):
        return f"Boletín {self.estudiante} - P{self.periodo} {self.ano_escolar}"


# ============================================================
# CONFIGURACIÓN DEL COLEGIO
# ============================================================

class ConfiguracionColegio(models.Model):
    """
    Configuraciones específicas por colegio.
    """
    colegio = models.OneToOneField(Colegio, on_delete=models.CASCADE, related_name="config")
    rector_nombre = models.CharField(max_length=200, blank=True, default="")
    rector_cedula = models.CharField(max_length=20, blank=True, default="")
    rector_firma = models.ImageField(upload_to="colegios/firmas/", blank=True, null=True)
    mensaje_boletin = models.TextField(blank=True, default="")
    escala_valoracion = models.TextField(blank=True, default="1.0 - 3.0: Bajo\n3.1 - 3.9: Básico\n4.0 - 4.5: Alto\n4.6 - 5.0: Superior")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "configuraciones_colegio"
        verbose_name = "Configuración"
        verbose_name_plural = "Configuraciones"