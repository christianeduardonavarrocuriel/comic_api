# Comic API – Buscador de cómics, personajes y películas

## Descripción del proyecto

Comic API es una aplicación web desarrollada con Flask que permite buscar y explorar información de personajes, cómics (issues y volúmenes) y películas de superhéroes utilizando la API pública de ComicVine. Además, incluye una sección "What If" donde se generan narraciones alternativas inspiradas en el multiverso de los cómics y se convierten en audio mediante un servicio de texto a voz.

El objetivo del proyecto es integrar varias APIs en una misma interfaz sencilla, practicar consumo de servicios externos desde Python y ofrecer una experiencia de consulta rápida y visual para fans de los cómics.

## ¿Qué hace la aplicación?

- Permite buscar personajes, cómics y películas a partir de un nombre o término de búsqueda.
- Agrupa los resultados por tipo de recurso: personajes, issues, volúmenes y películas.
- Muestra listados iniciales de contenido popular cuando no se ha hecho ninguna búsqueda.
- Ofrece una vista de detalle para cada recurso con información ampliada.
- Incluye una sección "What If" donde se genera una historia alternativa usando IA (rol de narrador tipo "Uatu, el Vigilante").
- Convierte la narración generada en audio usando un motor de texto a voz.

## Tecnologías utilizadas

- **Python 3** como lenguaje principal del proyecto.
- **Flask** como framework web para definir rutas, controlar la lógica del servidor y renderizar plantillas HTML.
- **Jinja2** a través de las plantillas en la carpeta `templates/` para construir las vistas (`index.html`, `detail.html`, `whatif.html`, `error.html`).
- **ComicVine API** como fuente de datos para personajes, cómics y películas.
- **Requests** para realizar peticiones HTTP a las APIs externas.
- **python-dotenv** para cargar las claves de API y configuraciones desde variables de entorno (`.env`).
- **Groq API** para generar las narraciones de tipo "What If" a partir de un escenario de entrada.
- **ElevenLabs** como motor principal de texto a voz para generar el audio de las historias.
- **gTTS (Google Text-to-Speech)** como alternativa de respaldo cuando ElevenLabs no está disponible o falla.
- **HTML/CSS** (incluyendo estilos utilitarios) para la parte visual de la aplicación.

## Problemas que resuelve

- Centraliza en una sola interfaz la consulta de información relacionada con cómics, personajes y películas que normalmente está dispersa en distintos sitios.
- Facilita la exploración rápida de contenido popular sin que el usuario tenga que conocer de antemano todos los nombres o títulos.
- Mejora la experiencia del usuario al presentar resultados enriquecidos con imágenes, descripciones y enlaces de detalle.
- Permite experimentar con escenarios alternativos "What If" generados por IA, añadiendo una capa creativa sobre los datos de cómics.
- Hace accesible el contenido generado a través de audio, útil para usuarios que prefieren escuchar la narración o tienen dificultades para leer en pantalla.

Este proyecto está pensado como una práctica completa de integración de APIs, manejo de variables de entorno y desarrollo de una aplicación web sencilla pero funcional con Flask.

## Requisitos previos

- Python 3.10 o superior.
- Una cuenta y API key de ComicVine.
- (Opcional) API key de Groq para generar narraciones "What If".
- (Opcional) API key de ElevenLabs para la funcionalidad de texto a voz avanzada.

## Instalación y ejecución


1. (Recomendado) Crear y activar un entorno virtual:

	```bash
	python -m venv venv
	source venv/bin/activate  # Linux / macOS
	# .\\venv\\Scripts\\activate  # Windows PowerShell
	```

3. Instalar las dependencias principales (ejemplo mínimo):

	```bash
	pip install flask requests python-dotenv groq elevenlabs gTTS
	```

4. Configurar las variables de entorno en un archivo `.env` dentro de la carpeta `carpeta/` (o en el entorno del sistema):

	```env
	COMICVINE_API_KEY=tu_api_key_de_comicvine
	GROQ_API_KEY=tu_api_key_de_groq
	ELEVENLABS_API_KEY=tu_api_key_de_elevenlabs
	ELEVENLABS_VOICE_ID=opcional_id_de_voz
	```

	Para que la búsqueda básica funcione es obligatorio definir `COMICVINE_API_KEY`. Las claves de Groq y ElevenLabs son opcionales, pero necesarias para aprovechar al máximo la sección "What If" y el audio.

5. Ejecutar la aplicación Flask:

	```bash
	cd carpeta
	python app.py
	```

6. Abrir el navegador en:

	```
	http://127.0.0.1:5000/
	```

## Endpoints principales

- `GET /`
  - Página principal.
  - Muestra contenido popular por defecto (personajes, cómics y películas).
  - Acepta también `POST` con el parámetro `nombre` en un formulario para buscar contenido específico.

- `GET /api/load-more/<resource_type>`
  - Carga más elementos de forma paginada vía AJAX.
  - `resource_type` puede ser `characters`, `comics` o `movies`.
  - Devuelve un JSON con HTML precargado para insertar en la interfaz y un indicador `has_more`.

- `GET /detail/<resource_type>/<id>`
  - Muestra la vista de detalle de un recurso específico obtenido desde la API de ComicVine.
  - `resource_type` puede ser `character`, `issue`, `volume` o `movie`.

- `GET /what-if`
  - Muestra el formulario para introducir un escenario "What If".

- `POST /what-if`
  - Genera una narración basada en el escenario proporcionado, usando Groq.
  - Intenta sintetizar la narración en audio utilizando ElevenLabs o, en su defecto, gTTS.

## Autor

- **Autor:** Christian Eduardo Navarro Curiel
- **Repositorio:** https://github.com/christianeduardonavarrocuriel/comic_api

