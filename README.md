# Sitemap automático de propiedades — cbimpactopro.com

Genera y envía automáticamente un sitemap XML con todas las fichas de propiedades
(`/p/...`), incluyendo las que se cargan por scroll infinito.

Se ejecuta automáticamente 3 veces por semana (lunes, miércoles y viernes).

---

## Estructura del proyecto

```
sitemap-automation/
├── .github/
│   └── workflows/
│       └── sitemap.yml        ← Automatización (GitHub Actions)
├── generate_sitemap.py        ← Navega el sitio y genera el XML
├── submit_sitemap.py          ← Envía el sitemap a Google Search Console
├── requirements.txt           ← Dependencias Python
├── sitemap_properties.xml     ← Sitemap generado (se actualiza automáticamente)
└── README.md
```

---

## Pasos para configurar (una sola vez)

### Paso 1 — Crear el repositorio en GitHub

1. Ir a https://github.com/new
2. Nombre: `cbimpactopro-sitemap` (o el que prefieras)
3. Visibilidad: **Public** (necesario para que la URL del sitemap sea accesible)
4. Click en "Create repository"
5. Subir todos estos archivos al repositorio

### Paso 2 — Ajustar la URL de listado de propiedades

Abrir `generate_sitemap.py` y verificar que la URL en `LISTING_PAGES` sea correcta.
Por ejemplo, si tu página de propiedades es `https://www.cbimpactopro.com/propiedades`,
dejala así. Si tiene otra URL, ajustala.

### Paso 3 — Ajustar la URL del sitemap en submit_sitemap.py

En `submit_sitemap.py`, reemplazar en `SITEMAP_URL`:
- `{TU_USUARIO}` → tu nombre de usuario de GitHub
- `{TU_REPO}` → el nombre del repositorio que creaste

Ejemplo:
```
https://raw.githubusercontent.com/juanperez/cbimpactopro-sitemap/main/sitemap_properties.xml
```

### Paso 4 — Crear credenciales de Google (Service Account)

Esto permite que el script envíe el sitemap a Google Search Console automáticamente.

1. Ir a https://console.cloud.google.com/
2. Crear un proyecto nuevo (o usar uno existente)
3. Ir a "APIs y servicios" → "Biblioteca"
4. Buscar "Google Search Console API" y habilitarla
5. Ir a "APIs y servicios" → "Credenciales"
6. Click en "Crear credenciales" → "Cuenta de servicio"
7. Ponerle un nombre (ej: `sitemap-bot`) y crear
8. En la lista de cuentas de servicio, click en la que acabás de crear
9. Ir a la pestaña "Claves" → "Agregar clave" → "Crear clave nueva" → JSON
10. Se descarga un archivo `.json` — **guardalo, lo necesitás en el siguiente paso**

### Paso 5 — Agregar la cuenta de servicio a Search Console

1. Ir a https://search.google.com/search-console/
2. Seleccionar tu propiedad (cbimpactopro.com)
3. Ir a Configuración → Usuarios y permisos
4. Click en "Agregar usuario"
5. Ingresar el email de la cuenta de servicio (lo encontrás en el JSON, campo `client_email`)
6. Permiso: **Propietario** (necesario para enviar sitemaps)
7. Guardar

### Paso 6 — Agregar el secreto en GitHub

1. Ir a tu repositorio en GitHub
2. Settings → Secrets and variables → Actions
3. Click en "New repository secret"
4. Nombre: `GOOGLE_CREDENTIALS`
5. Valor: **todo el contenido** del archivo JSON descargado en el Paso 4
6. Click en "Add secret"

### Paso 7 — Primera ejecución manual

1. Ir a tu repositorio → pestaña "Actions"
2. Click en "Generar y enviar sitemap de propiedades"
3. Click en "Run workflow" → "Run workflow"
4. Esperar que termine (aprox. 5-10 minutos)
5. Verificar que aparece `sitemap_properties.xml` en el repositorio

---

## Cómo funciona después

- Se ejecuta automáticamente **lunes, miércoles y viernes a las 3am** (hora Argentina)
- Actualiza el archivo `sitemap_properties.xml` en el repositorio
- Notifica a Google Search Console del sitemap actualizado
- Podés ver el historial de ejecuciones en la pestaña "Actions" de GitHub

## Ajustes posibles

En `generate_sitemap.py`:
- `MAX_SCROLLS`: aumentar si tenés muchas propiedades y no se encuentran todas
- `SCROLL_WAIT`: aumentar si el sitio es lento y no carga a tiempo entre scrolls
- `LISTING_PAGES`: agregar más URLs de listado (por zona, tipo de propiedad, etc.)

En `.github/workflows/sitemap.yml`:
- `cron: "0 6 * * 1,3,5"` → cambiar la frecuencia de ejecución si querés
