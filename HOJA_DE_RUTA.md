# HOJA DE RUTA — Cultura T Educación
**Versión:** 1.0  
**Actualizado:** 25-Abr-2026 20:55 UTC

---

## ESTADO ACTUAL

```
cultura-t-educacion/
├── config/          ✅ settings, urls, wsgi, asgi
├── core/            ✅ models, views, urls, admin, managers, middleware
├── templates/      ✅ base.html, dashboard.html, registration/login.html
├── static/          ✅ (vacío — Bootstrap CDN)
├── media/           ✅ (para uploads)
├── manage.py        ✅
├── requirements.txt ✅
├── runtime.txt      ✅
├── render.yaml      ✅
└── .env.example     ✅
```

---

## 📋 HOJA DE RUTA — Por módulo

### FASE 1 — Fundamento ✅ COMPLETADO
- [x] Estructura Django + config multi-tenant
- [x] Modelos (Usuario, Colegio, Año, Estudiante, Materia, Nota, etc.)
- [x] Middleware multi-tenant (`request.colegio`)
- [x] Sistema de roles (rector, profesor, estudiante, padre)
- [x] Templates base + dashboard Bootstrap 5

### FASE 2 — Módulos pendientes
- [ ] **Módulo Boletines** — Generación PDF por grado (ReportLab)
- [ ] **Módulo Observador** — Registro diario comportamiento
- [ ] **Módulo Parcelador** — Programación semanal profesores
- [ ] **Módulo Agenda** — Eventos del calendario escolar
- [ ] **Módulo Pagos** — Estados de cuenta padres
- [ ] **Módulo Reportes** — Chart.js dashboards por rol

### FASE 3 — Despliegue
- [ ] Configurar Supabase (crear tablas, FK, triggers)
- [ ] Subir código a GitHub (ya ✅ SSH funciona)
- [ ] Desplegar en Render (Droplet)
- [ ] Configurar dominio

### FASE 4 — Automatización
- [ ] Heartbeat cada 30 min
- [ ] Auto-push tras cada módulo completado
- [ ] Notificaciones automáticas (email/push)

---

## 🖧 CONFIGURACIÓN BASE DE DATOS (Supabase)

### Variables de entorno necesarias
```
DATABASE_URL=postgresql://postgres.[PROJECT-REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres
```

### Alternativa (variables individuales)
```
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=xxxxxxxxxxxx
DB_HOST=db.[PROJECT-REF].supabase.co
DB_PORT=5432
```

### Tablas a crear en Supabase (via SQL Editor)
```sql
-- Todas las tablas del modelo Django (después de makemigrations)
-- El ORM de Django crea las tablas con migraciones
```

---

## ⚙️ HEARTBEAT RUPERT (autónomo)

**Frecuencia:** Cada 30 min  
**Archivo:** `/home/openclaw/.openclaw/workspace/HEARTBEAT.md`  
**Token Notion:** `ntn_T57129281536xSqlEpYY45vwrwOAW4UYLlEnNlavHI46tg`

### Tareas autónomas del heartbeat:
1. Verificar estado de git push → si hay cambios pendientes, hacer push
2. Verificar conexión DB (Supabase)
3. Verificar si hay nuevas tâches en HEARTBEAT
4. Resumir progreso en HEARTBEAT

### Significado de cada estado:
- `✅` = Completado
- `🔄` = En progreso
- `⏳` = Pendiente (awaiting datos)
- `❌` = Bloqueado / error

---

## 🔑 GIT / GITHUB

**Repo SSH:** `git@github.com:cultura-turistica/educacion.git`  
**SSH key:** `/root/.ssh/id_ed25519` (funciona ✅)  
**Usuario GitHub:** `cultura-turistica`

**Para push manual:**
```bash
GIT_SSH_COMMAND="ssh -i /root/.ssh/id_ed25519" git push educacion main
```

---

## 📌 NOTAS

- **Multi-tenant:** Todo query se filtra por `colegio_id` via middleware
- **DB:** PostgreSQL en Supabase — no usar SQLite en producción
- **PDF boletines:** ReportLab (pure Python, sin deps C)
- **Frontend:** Bootstrap 5 CDN + Bootstrap Icons + Chart.js
- **Despliegue:** Render / Droplet con Gunicorn
