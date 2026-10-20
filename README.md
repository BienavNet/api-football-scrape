# api-football-scrape

Pipeline de scraping en Python para extraer estadísticas de partidos de fútbol de varias ligas. Funciona por etapas: ligas → equipos → partidos → estadísticas, guardando los resultados en JSON y SQLite.

> Proyecto con fines educativos y de práctica de automatización. Los datos provienen de [Flashscore](https://www.flashscoreusa.com). Revisa los términos de uso del sitio antes de usarlo.

## Tecnologías

- Python 3 <!-- TODO: versión -->
- [Playwright](https://playwright.dev/python/) (async) para automatizar el navegador
- BeautifulSoup para parsear el HTML
- asyncio + `Semaphore` para controlar la concurrencia
- SQLite3 para almacenar las estadísticas

## Cómo funciona

| Etapa | Módulo | Entrada | Salida |
|-------|--------|---------|--------|
| 1. Equipos | `teams/scrapeTeams.py` | `inputLeagues.txt` (una URL de liga por línea) | JSON con equipos y su liga |
| 2. Partidos | `matchs/scrapeMatchs.py` | JSON de equipos | JSON con los enlaces a los partidos de cada equipo |
| 3. Estadísticas | `statistics_match/scrapeStatistics.py` | Archivos numerados de enlaces (`001.json`, `002.json`...) | JSON con las estadísticas de cada partido |
| Persistencia | `db/` | Estadísticas | Base de datos SQLite (`futbol_data.db`) |

Detalles de cada etapa:

- **Equipos:** abre la tabla de posiciones de cada liga y extrae el nombre y el enlace de cada equipo.
- **Partidos:** entra a la página de resultados de cada equipo y pulsa "Show more games" (hasta 10 veces) para cargar el historial completo antes de extraer los enlaces.
- **Estadísticas:** abre cada partido, entra a la pestaña *Stats* y extrae equipos, fecha, marcador y todas las secciones de estadísticas. Se procesa por lotes (`from_scrape` / `to_scrape`) para poder reanudar o dividir el trabajo.

## Estructura del proyecto

```
├── config/             # rutas, timeouts, workers concurrentes, proxy, headless
├── db/                 # conexión a SQLite y almacenamiento
├── exceptions/         # excepciones personalizadas
├── matchs/             # etapa 2: enlaces a partidos
├── statistics_match/   # etapa 3: estadísticas por partido
├── teams/              # etapa 1: equipos por liga
├── main.py             # punto de entrada
└── requirements.txt
```

## Instalación

```bash
git clone https://github.com/BienavNet/api-football-scrape.git
cd api-football-scrape
python -m venv venv
source venv/bin/activate      # En Windows: venv\Scripts\activate
pip install -r requirements.txt
playwright install
```

> Nota: el código lanza el navegador con `channel="msedge"`, por lo que necesita Microsoft Edge instalado. <!-- TODO: quitar esta nota si cambias a Chromium -->

## Configuración

En `config/` se definen:

- Rutas de entrada y salida de cada etapa
- `TIMEOUT`: tiempo máximo de espera por página
- `CONCURRENCY_WORKERS`: número de páginas procesadas en paralelo
- `MAX_RETRIES` y `HEADLESS`
- Proxy (opcional)

Agrega las ligas a scrapear en `inputLeagues.txt`, una URL por línea:

```
https://www.flashscoreusa.com/soccer/england/premier-league/#/OEEq9Yvp/standings/overall/
```

## Uso

<!-- TODO: confirma cómo se ejecuta cada etapa desde main.py -->
```bash
python main.py
```

## Formato de salida

Equipos:

```json
{ "teams": [ { "id": "...", "name": "...", "link": "...", "league": "..." } ] }
```

Estadísticas de un partido:

```json
{
  "id": "...",
  "home": "Equipo local",
  "away": "Equipo visitante",
  "match_date": "...",
  "score": { "home": "2", "away": "1" },
  "data": { "<sección>": { "<estadística>": { "home": "...", "away": "..." } } }
}
```

## Limitaciones conocidas

- Los selectores CSS de Flashscore incluyen clases generadas automáticamente (por ejemplo `wcl-row_...`) que pueden cambiar. Si dejan de extraerse estadísticas, hay que actualizar los selectores.
- Depende de la estructura actual del sitio y puede romperse si cambia.

## Mejoras pendientes

- [ ] Tests
- [ ] Reintentos robustos en la etapa de estadísticas
- [ ] Rutas relativas y navegador configurable
- [ ] Logging en lugar de `print`

## Licencia

<!-- TODO: agrega una licencia (por ejemplo MIT) -->
