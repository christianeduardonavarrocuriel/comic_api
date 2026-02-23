"""Aplicación web Flask para explorar contenido de cómics.

Este módulo define la aplicación principal, integra la API de ComicVine
para obtener personajes, cómics y películas, y se comunica con servicios
de IA (Groq) y texto a voz (ElevenLabs/gTTS) para generar historias
"What If" y su respectivo audio.
"""

from flask import Flask, render_template, request
import requests
import re
import base64
import os
from dotenv import load_dotenv
from groq import Groq
from elevenlabs.client import ElevenLabs
from gtts import gTTS
from io import BytesIO

load_dotenv()

app = Flask(__name__)

COMICVINE_API_KEY = os.getenv('COMICVINE_API_KEY')
HEADERS = {'User-Agent': 'MiAppComics/1.0'}

# CONFIGURACIÓN DE APIS
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')
ELEVENLABS_VOICE_ID = os.getenv('ELEVENLABS_VOICE_ID', '21m00Tcm4TlvDq8ikWAM')  # Rachel por defecto

# Diccionario de traducciones español-inglés para búsquedas
TRADUCCIONES = {
    'hombre araña': 'Spider-Man',
    'hombre arana': 'Spider-Man',
    'spiderman': 'Spider-Man',
    'hombre de hierro': 'Iron Man',
    'iron man': 'Iron Man',
    'capitan america': 'Captain America',
    'capitán américa': 'Captain America',
    'viuda negra': 'Black Widow',
    'ojo de halcon': 'Hawkeye',
    'ojo de halcón': 'Hawkeye',
    'pantera negra': 'Black Panther',
    'lobezno': 'Wolverine',
    'mujer maravilla': 'Wonder Woman',
    'flash': 'Flash',
    'acuaman': 'Aquaman',
    'linterna verde': 'Green Lantern',
    'flecha verde': 'Green Arrow',
    'robin': 'Robin',
    'guason': 'Joker',
    'guasón': 'Joker',
    'joker': 'Joker',
    'harley quinn': 'Harley Quinn',
    'mujer gato': 'Catwoman',
    'pinguino': 'Penguin',
    'pingüino': 'Penguin',
    'acertijo': 'Riddler',
    'hiedra venenosa': 'Poison Ivy',
    'thor': 'Thor',
    'hulk': 'Hulk',
    'increible hulk': 'Incredible Hulk',
    'doctor extraño': 'Doctor Strange',
    'doctor extrano': 'Doctor Strange',
    'bruja escarlata': 'Scarlet Witch',
    'vision': 'Vision',
    'halcon': 'Falcon',
    'halcón': 'Falcon',
    'maquina de guerra': 'War Machine',
    'máquina de guerra': 'War Machine',
    'loki': 'Loki',
    'deadpool': 'Deadpool',
    'cable': 'Cable',
    'tormenta': 'Storm',
    'ciclope': 'Cyclops',
    'picara': 'Rogue',
    'pícara': 'Rogue',
    'gambito': 'Gambit',
    'bestia': 'Beast',
    'rondador nocturno': 'Nightcrawler',
    'profesor x': 'Professor X',
    'magneto': 'Magneto',
    'mistica': 'Mystique',
    'mística': 'Mystique',
    'dientes de sable': 'Sabretooth',
    'coloso': 'Colossus',
    'hombre de hielo': 'Iceman',
    'angel': 'Angel',
    'ángel': 'Angel',
    'superman': 'Superman',
    'supergirl': 'Supergirl',
    'batman': 'Batman',
    'wonder woman': 'Wonder Woman',
    'x-men': 'X-Men',
    'avengers': 'Avengers',
    'liga de la justicia': 'Justice League',
    'guardianes de la galaxia': 'Guardians of the Galaxy',
    'suicide squad': 'Suicide Squad',
    'comic': 'comic',
    'comics': 'comics',
    'pelicula': 'movie',
    'película': 'movie',
    'peliculas': 'movies',
    'películas': 'movies',
    'serie': 'series',
    'volumen': 'volume',
}

def traducir_busqueda(query):
    """Normaliza y traduce una consulta de búsqueda al inglés.

    Si la consulta coincide exactamente con una clave en TRADUCCIONES,
    devuelve el valor traducido. En caso contrario, intenta reemplazar
    subcadenas conocidas; si no hay coincidencias, devuelve el texto
    original sin modificar.
    """
    if not query:
        return query
    q = query.lower().strip()
    if q in TRADUCCIONES:
        return TRADUCCIONES[q]
    for esp, ing in TRADUCCIONES.items():
        if esp in q:
            return q.replace(esp, ing)
    return query

def generar_historia_whatif(scenario):
    """Genera una narración "What If" usando el modelo de Groq.

    Recibe un escenario en texto, construye un prompt de sistema con
    reglas específicas (rol de Uatu, número de renglones, idioma, etc.)
    y obtiene la respuesta en streaming. Intenta devolver exactamente
    10 líneas de narración y acompaña el resultado con un código de
    estado HTTP semántico.
    """
    if not GROQ_API_KEY:
        return ("Error: Falta GROQ_API_KEY", 500)
    # Inicializa el cliente Groq; usa la variable de entorno si está configurada
    client = Groq()
    system_instruction = (
        "Eres Uatu, El Vigilante del multiverso.\n"
        "Tu función es narrar escenarios 'What If' exclusivamente.\n"
        "Si el input no es un escenario What If, responde exactamente: \n"
        "Solo mis ojos ven realidades alternativas. Por favor, preséntame un escenario What If para narrar.\n"
        "Escribe la narración en español, tono épico pero sobrio.\n"
        "OBLIGATORIO: Produce exactamente 10 renglones, ni más ni menos.\n"
        "Cada renglón debe ser una sola línea de texto.\n"
        "No dejes líneas vacías ni separadores entre renglones.\n"
        "No incluyas listas, viñetas, títulos ni conclusiones añadidas.\n"
        "No menciones que eres una IA ni des advertencias.\n"
        "Mantén coherencia con los personajes y hechos sin contradicciones.\n"
        "No generes audio ni instrucciones; solo la narración textual.\n"
        "RECUERDA: La narración debe tener exactamente 10 renglones."
    )
    try:
        completion = client.chat.completions.create(
            # Modelo y parámetros según la implementación solicitada
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": f"El escenario What If es: '{scenario}'"}
            ],
            temperature=1,
            max_completion_tokens=8192,
            top_p=1,
            reasoning_effort="medium",
            stream=True,
            stop=None
        )
        texto = ""
        for chunk in completion:
            texto += chunk.choices[0].delta.content or ""
        try:
            # Preferimos exactamente 10 líneas (renglones) sin vacíos
            lineas = [l.strip() for l in texto.strip().splitlines() if l.strip()]
            if len(lineas) >= 10:
                return ("\n".join(lineas[:10]), 200)
            # Fallback: tomar oraciones y poner una por renglón
            oraciones = [s.strip() for s in re.split(r"(?<=[\.!?…])\s+", texto.strip()) if s.strip()]
            if len(oraciones) >= 10:
                return ("\n".join(oraciones[:10]), 200)
        except Exception:
            pass
        return (texto.strip(), 200)
    except Exception as e:
        return (f"Error Groq: {str(e)}", 500)

def status_text(code):
    """Devuelve una descripción en español para un código de estado.

    Se utiliza principalmente en la vista "What If" para mostrar al
    usuario si la generación de la narración se procesó correctamente
    o produjo algún tipo de error.
    """
    mapping = {200:'Solicitud procesada con éxito',400:'Solicitud inválida',401:'No autorizado',403:'Prohibido',404:'No encontrado',429:'Demasiadas solicitudes',500:'Error interno del servidor'}
    return mapping.get(code, 'Estado desconocido')

def generar_audio_tts(texto):
    """Genera audio en base64 a partir de un texto en español.

    Intenta primero utilizar ElevenLabs si hay API key disponible y,
    en caso de fallo o ausencia de credenciales, hace fallback a gTTS.
    Devuelve la representación base64 del audio o ``None`` si no fue
    posible sintetizarlo.
    """
    # Primero intentamos con ElevenLabs, luego caemos a gTTS si falla o no hay API key
    try:
        if ELEVENLABS_API_KEY:
            try:
                client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
                audio = client.text_to_speech.convert(
                    text=texto,
                    voice_id=ELEVENLABS_VOICE_ID,
                    model_id="eleven_multilingual_v2"
                )
                audio_bytes = b"".join(audio)
                return base64.b64encode(audio_bytes).decode('utf-8')
            except Exception as e:
                print(f"ElevenLabs fallo: {type(e).__name__}: {str(e)}. Probando gTTS...")
        # Fallback a gTTS (español)
        try:
            tts = gTTS(text=texto, lang='es')
            buf = BytesIO()
            tts.write_to_fp(buf)
            audio_bytes = buf.getvalue()
            return base64.b64encode(audio_bytes).decode('utf-8')
        except Exception as e:
            print(f"gTTS fallo: {type(e).__name__}: {str(e)}")
            return None
    except Exception as e:
        print(f"Excepción TTS: {type(e).__name__}: {str(e)}")
        return None

def fetch_movies_direct(limit=20):
    """Obtiene un listado de películas directamente desde ComicVine.

    Llama al endpoint de películas, limita el número de resultados y
    marca cada elemento con ``resource_type = 'movie'`` para facilitar
    su tratamiento en la capa de presentación.
    """
    url = (
        "https://comicvine.gamespot.com/api/movies/"
        f"?api_key={COMICVINE_API_KEY}&format=json"
        f"&limit={limit}"
        "&field_list=name,deck,image,site_detail_url,id,release_date"
        "&sort=date_last_updated:desc"
    )
    try:
        response = requests.get(url, headers=HEADERS, timeout=12)
        data = response.json()
        results = data.get('results', [])
        for item in results:
            item['resource_type'] = 'movie'
        return results
    except Exception as e:
        print(f"Error fetching movies: {e}")
        return []

def fetch_content(query, limit=20):
    """Busca personajes, cómics y películas en ComicVine.

    Aplica primero ``traducir_busqueda`` a la consulta para mejorar los
    resultados cuando el usuario escribe en español. Limita el número de
    elementos devueltos y retorna la lista de resultados tal como la
    expone la API.
    """
    q = traducir_busqueda(query)
    url = (
        "https://comicvine.gamespot.com/api/search/"
        f"?api_key={COMICVINE_API_KEY}&format=json&query={q}"
        "&resources=character,issue,volume,movie"
        f"&limit={limit}"
        "&field_list=name,real_name,deck,image,site_detail_url,resource_type,cover_date,issue_number,volume,release_date,api_detail_url,id"
    )
    try:
        response = requests.get(url, headers=HEADERS, timeout=12)
        data = response.json()
        return data.get('results', [])
    except Exception:
        return []

def get_detail(resource_type, resource_id):
    """Recupera el detalle de un recurso específico desde ComicVine.

    Usa un mapa interno para construir la URL adecuada según el tipo
    de recurso (personaje, issue, volumen o película) y ajusta el
    ``field_list`` para incluir los campos relevantes. Devuelve el
    diccionario de resultados o ``None`` si ocurre un error.
    """
    resource_map = {'character':('character','4005'),'issue':('issue','4000'),'volume':('volume','4050'),'movie':('movie','4025')}
    if resource_type not in resource_map:
        return None
    resource, code = resource_map[resource_type]
    fields = "name,deck,description,image,site_detail_url"
    if resource_type == 'character':
        fields += ",real_name,origin,powers,issue_credits,movie_credits,volume_credits"
    elif resource_type == 'issue':
        fields += ",character_credits,volume,cover_date,issue_number"
    elif resource_type == 'volume':
        fields += ",publisher,start_year,count_of_issues,issues"
    elif resource_type == 'movie':
        fields += ",release_date,characters,runtime,rating"
    url = f"https://comicvine.gamespot.com/api/{resource}/{code}-{resource_id}/?api_key={COMICVINE_API_KEY}&format=json&field_list={fields}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=12)
        data = response.json()
        if data.get('status_code') != 1:
            return None
        return data.get('results')
    except Exception as e:
        print(f"Error fetching detail: {e}")
        return None

@app.route('/', methods=['GET', 'POST'])
def index():
    """Vista principal de la aplicación.

    En modo GET muestra listados de contenido popular (personajes,
    cómics y películas) preconfigurados. En modo POST procesa el
    formulario de búsqueda, clasifica los resultados por tipo de
    recurso y selecciona un personaje destacado para la portada.
    """
    personaje = None
    personajes = []
    comics_issues = []
    comics_volumes = []
    peliculas = []
    error_msg = None
    consulta = None
    if request.method == 'POST':
        consulta = request.form.get('nombre')
        results = fetch_content(consulta, 100)
        if results:
            for item in results:
                rtype = item.get('resource_type')
                if rtype == 'character':
                    personajes.append(item)
                elif rtype == 'issue':
                    comics_issues.append(item)
                elif rtype == 'volume':
                    comics_volumes.append(item)
                elif rtype == 'movie':
                    peliculas.append(item)
            # Si no encontramos películas en la búsqueda inicial, buscar directamente
            if not peliculas and consulta:
                direct_movies = fetch_movies_direct(30)
                # Filtrar por término de búsqueda
                search_lower = consulta.lower()
                for movie in direct_movies:
                    movie_name = (movie.get('name') or '').lower()
                    if search_lower in movie_name or any(word in movie_name for word in search_lower.split()):
                        peliculas.append(movie)
                        if len(peliculas) >= 20:
                            break
            if personajes:
                personaje = personajes[0]
        else:
            error_msg = "No se encontraron resultados para ese nombre."
    else:
        popular_searches = ['Spider-Man','Batman','Superman','Iron Man','Wolverine','Wonder Woman','Joker','Captain America','Flash','Thor','Green Lantern','Hulk','Deadpool','X-Men','Avengers']
        movie_searches = ['Dark Knight','Avengers','Spider-Man','Batman','Superman','Iron Man','X-Men','Guardians','Thor','Wonder Woman','Justice League','Deadpool','Black Panther','Captain America']
        for search_term in popular_searches[:10]:
            results = fetch_content(search_term, 6)
            for item in results:
                rtype = item.get('resource_type')
                item_id = item.get('id')
                if rtype == 'character' and len(personajes) < 40:
                    if not any(p.get('id') == item_id for p in personajes):
                        personajes.append(item)
                elif rtype == 'issue' and len(comics_issues) < 25:
                    if not any(c.get('id') == item_id for c in comics_issues):
                        comics_issues.append(item)
                elif rtype == 'volume' and len(comics_volumes) < 30:
                    if not any(v.get('id') == item_id for v in comics_volumes):
                        comics_volumes.append(item)
                elif rtype == 'movie' and len(peliculas) < 20:
                    if not any(m.get('id') == item_id for m in peliculas):
                        peliculas.append(item)
        if len(peliculas) < 5:
            direct_movies = fetch_movies_direct(25)
            for movie in direct_movies:
                if len(peliculas) >= 20:
                    break
                movie_id = movie.get('id')
                if not any(m.get('id') == movie_id for m in peliculas):
                    peliculas.append(movie)
        if len(peliculas) < 20:
            for search_term in movie_searches:
                if len(peliculas) >= 20:
                    break
                results = fetch_content(search_term, 10)
                for item in results:
                    if item.get('resource_type') == 'movie':
                        item_id = item.get('id')
                        if not any(m.get('id') == item_id for m in peliculas):
                            peliculas.append(item)
                            if len(peliculas) >= 20:
                                break
        if len(peliculas) < 5:
            generic_movie_searches = ['Marvel movie','DC movie','superhero movie','comic movie']
            for search_term in generic_movie_searches:
                if len(peliculas) >= 20:
                    break
                results = fetch_content(search_term, 15)
                for item in results:
                    if item.get('resource_type') == 'movie':
                        item_id = item.get('id')
                        if not any(m.get('id') == item_id for m in peliculas):
                            peliculas.append(item)
                            if len(peliculas) >= 20:
                                break
        if personajes:
            personaje = personajes[0]
        print(f"DEBUG: Personajes: {len(personajes)}, Volúmenes: {len(comics_volumes)}, Issues: {len(comics_issues)}, Películas: {len(peliculas)}")
    return render_template('index.html', personaje=personaje, personajes=personajes, comics_issues=comics_issues, comics_volumes=comics_volumes, peliculas=peliculas, error_msg=error_msg, consulta=consulta)

@app.route('/api/load-more/<resource_type>')
def load_more(resource_type):
    """Endpoint para cargar más elementos vía AJAX.

    Recibe ``resource_type`` (characters, comics o movies) y un
    parámetro ``offset`` para paginación. Construye una lista adicional
    de resultados usando búsquedas predefinidas y devuelve fragmentos
    HTML junto con un indicador de si hay más datos disponibles.
    """
    from flask import jsonify
    offset = request.args.get('offset', 0, type=int)
    limit = 10
    results = []
    if resource_type == 'characters':
        searches = ['Spider','Bat','Super','Iron','Captain','Thor','Hulk','Black','Wonder','Flash','Green','Aqua','Wolverine','Storm','Cyclops','Jean','Rogue','Gambit','Beast','Nightcrawler','Professor','Magneto','Mystique','Sabretooth','Deadpool','Cable','Colossus','Kitty','Iceman','Angel','Scarlet','Vision','Hawkeye','Widow','Panther','Strange','Ant','Wasp','Falcon','War Machine','Loki','Joker','Harley','Catwoman','Penguin','Riddler','Bane','Ivy','Lex','Cyborg','Starfire','Raven','Robin','Nightwing','Red','Arrow','Canary','Atom','Firestorm','Shazam','Martian','Spectre']
        search_index = (offset // limit) % len(searches)
        search_term = searches[search_index]
        items = fetch_content(search_term, 30)
        results = [item for item in items if item.get('resource_type') == 'character']
    elif resource_type == 'comics':
        searches = ['Amazing Spider','Spectacular Spider','Web of Spider','Ultimate Spider','Batman Detective','Batman Dark Knight','Batman Legends','Batman Shadow','Superman Action','Superman Adventures','Man of Steel','Superman Unchained','X-Men','Uncanny X-Men','New X-Men','Astonishing X-Men','X-Force','Avengers','New Avengers','Mighty Avengers','Secret Avengers','Justice League','JLA','Justice League Dark','Justice League International','Iron Man','Invincible Iron Man','Captain America','Thor','Hulk','Wonder Woman','Flash','Green Lantern','Aquaman','Teen Titans','Fantastic Four','Incredible Hulk','Daredevil','Punisher','Ghost Rider','Spawn','Hellboy','Walking Dead','Saga','Watchmen','Sandman','Deadpool','Wolverine','Black Panther','Doctor Strange','Guardians']
        search_index = (offset // limit) % len(searches)
        search_term = searches[search_index]
        items = fetch_content(search_term, 30)
        results = [item for item in items if item.get('resource_type') in ['volume','issue']]
    elif resource_type == 'movies':
        if offset < 50:
            direct_movies = fetch_movies_direct(50)
            results = direct_movies[offset:offset + limit] if direct_movies else []
        else:
            results = []
        if len(results) < limit:
            searches = ['Dark Knight','Batman Begins','Batman Returns','Batman Forever','Superman Returns','Man of Steel','Superman II','Superman III','Spider-Man','Amazing Spider-Man','Spider-Man Homecoming','Avengers','Age of Ultron','Infinity War','Endgame','Iron Man','Captain America','Thor','Black Panther','Guardians','Doctor Strange','Ant-Man','Black Widow','Hulk','Winter Soldier','Civil War','Ragnarok','Wakanda','Multiverse','Quantumania','Justice League','Wonder Woman','Aquaman','Shazam','Flash','Joker','Suicide Squad','Birds of Prey','Green Lantern','X-Men','Days of Future Past','First Class','Apocalypse','Logan','Deadpool','New Mutants','Wolverine','Phoenix','Fantastic Four','Venom','Morbius','Blade','Constantine']
            search_offset = max(0, offset - 50) // limit
            existing_ids = {r.get('id') for r in results}
            searches_tried = 0
            max_searches = 5
            while len(results) < limit and searches_tried < max_searches:
                search_index = (search_offset + searches_tried) % len(searches)
                search_term = searches[search_index]
                items = fetch_content(search_term, 20)
                for item in items:
                    if item.get('resource_type') == 'movie':
                        movie_id = item.get('id')
                        if movie_id not in existing_ids:
                            results.append(item)
                            existing_ids.add(movie_id)
                            if len(results) >= limit:
                                break
                searches_tried += 1
    html_items = []
    for item in results[:limit]:
        if resource_type == 'characters':
            name = item.get('name', 'Personaje sin nombre')
            if not name or name == 'None' or name.strip() == '':
                name = 'Personaje sin nombre'
            img_html = '<div class="w-full h-80 bg-gray-200 flex items-center justify-center text-6xl">🦸‍♂️</div>'
            if item.get('image') and item['image'].get('medium_url'):
                img_html = f'<img src="{item["image"]["medium_url"]}" alt="{name}" class="w-full h-80 object-cover">'
            html = f'''\n                <a href="/detail/character/{item.get('id')}" class="card block">\n                    {img_html}\n                    <div class="p-4">\n                        <h4 class="text-base font-semibold text-gray-900">{name}</h4>\n                    </div>\n                </a>\n            '''
        elif resource_type == 'comics':
            rtype = item.get('resource_type')
            name = item.get('name', 'Cómic' if rtype == 'issue' else 'Serie sin título')
            if not name or name == 'None' or name.strip() == '':
                name = 'Cómic' if rtype == 'issue' else 'Serie sin título'
            issue_num = ''
            if rtype == 'issue' and item.get('issue_number'):
                issue_number = str(item.get('issue_number'))
                if issue_number and issue_number != 'None' and issue_number.strip() != '':
                    issue_num = f" #{issue_number}"
            img_html = '<div class="w-full h-80 bg-gray-200 flex items-center justify-center text-6xl">📚</div>'
            if item.get('image') and item['image'].get('medium_url'):
                img_html = f'<img src="{item["image"]["medium_url"]}" alt="{name}" class="w-full h-80 object-cover">'
            html = f'''\n                <a href="/detail/{rtype}/{item.get('id')}" class="card block">\n                    {img_html}\n                    <div class="p-4">\n                        <h4 class="text-base font-semibold text-gray-900">{name}{issue_num}</h4>\n                    </div>\n                </a>\n            '''
        elif resource_type == 'movies':
            name = item.get('name', 'Película sin título')
            if not name or name == 'None' or name.strip() == '':
                name = 'Película sin título'
            img_html = '<div class="w-full h-80 bg-gray-200 flex items-center justify-center text-6xl">🎥</div>'
            if item.get('image') and item['image'].get('medium_url'):
                img_html = f'<img src="{item["image"]["medium_url"]}" alt="{name}" class="w-full h-80 object-cover">'
            html = f'''\n                <a href="/detail/movie/{item.get('id')}" class="card block">\n                    {img_html}\n                    <div class="p-4">\n                        <h4 class="text-base font-semibold text-gray-900">{name}</h4>\n                    </div>\n                </a>\n            '''
        html_items.append(html)
    return jsonify({'html': html_items, 'has_more': len(results) >= limit})

@app.route('/detail/<resource_type>/<int:resource_id>')
def detail(resource_type, resource_id):
    """Muestra la vista de detalle para un recurso concreto.

    Obtiene la información desde ComicVine mediante ``get_detail`` y
    renderiza la plantilla correspondiente. Si no se encuentra el
    recurso, devuelve una página de error 404.
    """
    item = get_detail(resource_type, resource_id)
    if not item:
        return render_template('error.html', message="No se pudo obtener la información del recurso."), 404
    return render_template('detail.html', item=item, resource_type=resource_type)

@app.route('/what-if', methods=['GET', 'POST'])
def what_if():
    """Gestiona la sección de escenarios "What If".

    En GET muestra el formulario vacío. En POST recibe un escenario,
    genera la narración con ``generar_historia_whatif``, asigna un
    mensaje de estado legible y, si es posible, produce audio en base64
    utilizando ``generar_audio_tts``.
    """
    historia = None
    audio_b64 = None
    scenario = ''
    status_code = None
    status_label = None
    if request.method == 'POST':
        scenario = request.form.get('scenario')
        if scenario:
            historia, status_code = generar_historia_whatif(scenario)
            if status_code is not None:
                status_label = status_text(status_code)
            if historia and not historia.startswith("Error"):
                audio_b64 = generar_audio_tts(historia)
    return render_template('whatif.html', historia=historia, audio=audio_b64, scenario=scenario, status_code=status_code, status_label=status_label)

if __name__ == '__main__':
    app.run(debug=True)