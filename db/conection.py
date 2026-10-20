import sqlite3, json

# Nombre de la base de datos
DB_NAME = './db/database.db'

def conectar_db(db_nombre):
    """Establece la conexión y devuelve la conexión y el cursor."""
    try:
        conn = sqlite3.connect(db_nombre)
        cursor = conn.cursor()
        print(f"Conexión a {db_nombre} establecida.")
        return conn, cursor
    except sqlite3.Error as e:
        print(f"Error al conectar con la base de datos: {e}")
        return None, None

def crear_tablas(cursor, conn):
    """Crea la tabla si no existe."""
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS partidos (
            -- Datos principales del partido
            id TEXT PRIMARY KEY,
            home_team TEXT NOT NULL,
            away_team TEXT NOT NULL,
            match_date TEXT,
            competition TEXT,
            referee TEXT,

            -- Marcador
            score_home INTEGER,
            score_away INTEGER,

            -- Tiros Totales
            total_shots INTEGER,
            shots_home INTEGER,
            shots_away INTEGER,

            -- Tiros a Puerta (Shots on Target)
            shots_on_target_total INTEGER,
            shots_on_target_home INTEGER,
            shots_on_target_away INTEGER,

            -- Corners
            corners_total INTEGER,
            corners_home INTEGER,
            corners_away INTEGER,

            -- Faltas (Fouls)
            fouls_total INTEGER,
            fouls_home INTEGER,
            fouls_away INTEGER,

            -- Tarjetas Amarillas
            yellow_cards_total INTEGER,
            yellow_cards_home INTEGER,
            yellow_cards_away INTEGER,

            -- Tarjetas Rojas
            red_cards_total INTEGER,
            red_cards_home INTEGER,
            red_cards_away INTEGER
        );
        ''')
        conn.commit()
        print("Tabla 'partidos' creada/verificada.")
    except sqlite3.Error as e:
        print(f"Error al crear la tabla: {e}")

def mapear_datos_para_db(data_json: dict) -> dict:
    """Aplaza el diccionario JSON anidado a un formato plano para la DB."""
    
    # Crea un diccionario para almacenar los datos planos
    datos_planos = {
        # Datos principales
        'id': data_json['id'],
        'home_team': data_json['home'],
        'away_team': data_json['away'],
        'match_date': data_json['match_date'],
        'referee': data_json['referee'],
        'competition': data_json['data']['competition'],
        
        # Marcador (convertir a int)
        'score_home': int(data_json['score']['home']),
        'score_away': int(data_json['score']['away']),

        # Tiros Totales (convertir a int)
        'total_shots': int(data_json['data']['total_shots']['total']),
        'shots_home': int(data_json['data']['total_shots']['home']),
        'shots_away': int(data_json['data']['total_shots']['away']),

        # Tiros a Puerta (Shots on Target)
        'shots_on_target_total': int(data_json['data']['shots_on_target']['total']),
        'shots_on_target_home': int(data_json['data']['shots_on_target']['home']),
        'shots_on_target_away': int(data_json['data']['shots_on_target']['away']),
        
        # Corners
        'corners_total': int(data_json['data']['corners']['total']),
        'corners_home': int(data_json['data']['corners']['home']),
        'corners_away': int(data_json['data']['corners']['away']),
        
        # Faltas (Fouls)
        'fouls_total': int(data_json['data']['fouls']['total']),
        'fouls_home': int(data_json['data']['fouls']['home']),
        'fouls_away': int(data_json['data']['fouls']['away']),

        # Tarjetas Amarillas
        'yellow_cards_total': int(data_json['data']['cards']['yellow']['total']),
        'yellow_cards_home': int(data_json['data']['cards']['yellow']['home']),
        'yellow_cards_away': int(data_json['data']['cards']['yellow']['away']),

        # Tarjetas Rojas (ya son int en el JSON)
        'red_cards_total': data_json['data']['cards']['red']['total'],
        'red_cards_home': data_json['data']['cards']['red']['home'],
        'red_cards_away': data_json['data']['cards']['red']['away']
    }
    
    return datos_planos

def insertar_partido_desde_json(cursor, conn, partido_json_dict: dict):
    """
    Inserta un registro de partido de fútbol usando un diccionario de datos JSON.
    """
    
    # 1. Aplanar los datos del JSON
    try:
        datos_para_db = mapear_datos_para_db(partido_json_dict)
    except (KeyError, ValueError) as e:
        print(f"Error al mapear datos del JSON: falta una clave o un valor no es convertible a número. Error: {e}")
        return

    # 2. Sentencia SQL con marcadores de posición con nombre
    sql_insert = """
    INSERT INTO partidos (
        id, home_team, away_team, match_date, competition, referee,
        score_home, score_away,
        total_shots, shots_home, shots_away,
        shots_on_target_total, shots_on_target_home, shots_on_target_away,
        corners_total, corners_home, corners_away,
        fouls_total, fouls_home, fouls_away,
        yellow_cards_total, yellow_cards_home, yellow_cards_away,
        red_cards_total, red_cards_home, red_cards_away
    ) VALUES (
        :id, :home_team, :away_team, :match_date, :competition, :referee,
        :score_home, :score_away,
        :total_shots, :shots_home, :shots_away,
        :shots_on_target_total, :shots_on_target_home, :shots_on_target_away,
        :corners_total, :corners_home, :corners_away,
        :fouls_total, :fouls_home, :fouls_away,
        :yellow_cards_total, :yellow_cards_home, :yellow_cards_away,
        :red_cards_total, :red_cards_home, :red_cards_away
    )
    """

    # 3. Ejecutar la inserción
    try:
        # Pasamos el diccionario directamente a execute. SQLite3 mapea :claves a datos_para_db[clave]
        cursor.execute(sql_insert, datos_para_db)
        conn.commit()
        print(f"Partido {datos_para_db['home_team']} vs {datos_para_db['away_team']} insertado correctamente.")
    except sqlite3.IntegrityError:
        print(f"ERROR: El partido con ID {datos_para_db['id']} ya existe (violación de PRIMARY KEY).")
    except sqlite3.Error as e:
        print(f"Ocurrió un error SQL: {e}")

def run(cursor, conn, from_scrape: int = 1, to_scrape: int = 1):
    
    for i in range(from_scrape, to_scrape + 1):
        try:

            with open(f"./statistics_match/results/fragmento_{str(i).zfill(3)}.json", 'r') as file:
                jsonMatchData = json.load(file)

            matchs = jsonMatchData['statistics']
        except FileNotFoundError:
            print("No se pudo abrir el archivo.")
            return
        
        try:
            for match in matchs:
                if (not match.get('data', None).get('total_shots', None).get('total', None) == 0 
                    or not match.get('data', None).get('corners', None).get('total', None) == 0):
                    insertar_partido_desde_json(cursor, conn, match)


        except Exception as e:
            print(f'{e} {e.__traceback__.tb_lineno}')

# --- Flujo principal ---
conn, cursor = conectar_db(DB_NAME)

if conn and cursor:
    # crear_tablas(cursor, conn)
    run(cursor, conn, 2, 196)
    # print(cursor.execute("""SELECT * FROM partidos""").fetchall())
    
    conn.close()
    print("Conexión cerrada.")