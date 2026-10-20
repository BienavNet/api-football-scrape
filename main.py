import sys, asyncio, json, os
sys.path.append('\\Users\\User\\Desktop\\api futbol scrapping')

from teams.scrapeTeams import run as scrapeTeamsRun
from matchs.scrapeMatchs import run as scrapeMatchsRun
from statistics_match.scrapeStatistics import run as scrapeStatisticsRun
from config.config import SCRAPE_MATCHS_LINKS_DIR_OUTPUT

from termcolor import colored

def clearLinks():

    with open(SCRAPE_MATCHS_LINKS_DIR_OUTPUT, 'r') as file:
        jsonMatchData = json.load(file)

    matchs = jsonMatchData['matchs']

    links_vistos = set()

    partidos_limpios = []

    for partido in matchs:
        link_actual = partido["link"]
        
        # 4. Comprueba si el link ya está en el conjunto de vistos
        if link_actual not in links_vistos:
            # Si NO ha sido visto, es un link único.
            
            # Agrega el objeto completo a la lista limpia
            partidos_limpios.append(partido)
            
            # Agrega el link al conjunto de vistos para evitar repeticiones futuras
            links_vistos.add(link_actual)

    # 5. Reemplaza la lista original con la lista limpia
    matchs = partidos_limpios

    with open("matchs/dataProcesed.json", 'w', encoding='utf-8') as outfile:
        json.dump({"matchs": matchs}, outfile, indent=4, ensure_ascii=False)

def fragmentar_y_guardar(lista_partidos, tamano_fragmento, carpeta_salida):
    contador_fragmentos = 0

    with open(lista_partidos, 'r', encoding='UTF-8') as file:
        partidos = json.load(file)['matchs']
    
    for i in range(0, len(partidos), tamano_fragmento):
        
        fragmento_actual = partidos[i:i + tamano_fragmento]
        contador_fragmentos += 1
        
        nombre_archivo = f"fragmento_{contador_fragmentos:03}.json"
        ruta_completa = os.path.join(carpeta_salida, nombre_archivo)
        
        # 3. Estructura el JSON para el archivo (opcional, pero recomendado)
        # Puedes guardar solo la lista de partidos, o envolverla en un objeto
        datos_a_guardar = {
            "total_registros": len(fragmento_actual),
            "matchs": fragmento_actual
        }
        
        # 4. Escribe el fragmento en el archivo
        try:
            with open(ruta_completa, 'w', encoding='utf-8') as f:
                # Usa 'indent=4' para que el JSON sea legible, si lo deseas
                json.dump(datos_a_guardar, f, indent=4, ensure_ascii=False)
            
            print(f"✅ Fragmento {contador_fragmentos} guardado: {ruta_completa} ({len(fragmento_actual)} registros)")
            
        except IOError as e:
            print(f"❌ ERROR al escribir el archivo {ruta_completa}: {e}")
            break # Detiene el proceso si no puede escribir
            
    print("\n--- Proceso de fragmentación completado. ---")


# Llama a la función para ejecutar el proceso
# fragmentar_y_guardar(data["matchs"], TAMANO_FRAGMENTO, CARPETA_SALIDA)


async def main():
    print(colored("Scrape data started, starting the task.", 'blue'))
    await scrapeTeamsRun()
    print(colored("Scrape Teams Finished, going on next task.", 'blue'))
    await scrapeMatchsRun()
    print(colored("Scrape Matchs Finished, going on next task.", 'blue'))
    

if __name__ == "__main__":
    # asyncio.run(main())
    clearLinks()
    # fragmentar_y_guardar('matchs/dataProcesed.json', 100, 'statistics_match/fragments')