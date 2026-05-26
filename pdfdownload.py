import os
import csv
import requests
import time

# 1. Configuración de rutas
CSV_PATH = "data/papers_corpus.csv"
PDF_DIR = "data/pdfs"

# Unpaywall exige un email real para usar su API pública
EMAIL = "juan.navarro.mora@alumnos.upm.es" 

# Crear la carpeta si no existe
os.makedirs(PDF_DIR, exist_ok=True)

def get_oa_pdf_url(doi):
    """Consulta Unpaywall para obtener el enlace directo al PDF en Open Access."""
    url = f"https://api.unpaywall.org/v2/{doi}?email={EMAIL}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            best_oa = data.get("best_oa_location")
            if best_oa and best_oa.get("url_for_pdf"):
                return best_oa.get("url_for_pdf")
    except Exception as e:
        print(f"  [!] Error de conexión consultando {doi}: {e}")
    return None

def download_pdf(pdf_url, save_path):
    """Descarga el PDF desde la URL dada."""
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
    try:
        response = requests.get(pdf_url, headers=headers, stream=True, timeout=15)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
    except Exception as e:
        print(f"  [!] Error descargando de {pdf_url}: {e}")
    return False

def main():
    print(f"Iniciando descarga de corpus en: {PDF_DIR}")
    
    if not os.path.exists(CSV_PATH):
        print(f"Error: No se encuentra el archivo {CSV_PATH}")
        return

    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            doi = row.get('doi', '').strip()
            if not doi:
                continue
            
            # Reemplazar barras del DOI para el nombre del archivo
            safe_doi = doi.replace('/', '_')
            pdf_path = os.path.join(PDF_DIR, f"{safe_doi}.pdf")
            
            if os.path.exists(pdf_path):
                print(f"[Omitido] Ya existe: {pdf_path}")
                continue
                
            print(f"-> Procesando: {doi}")
            pdf_url = get_oa_pdf_url(doi)
            
            if pdf_url:
                print(f"   Encontrado OA URL: {pdf_url}")
                success = download_pdf(pdf_url, pdf_path)
                if success:
                    print(f"   [OK] Guardado como {safe_doi}.pdf")
                else:
                    print("   [FALLO] No se pudo descargar el archivo.")
            else:
                print("   [FALLO] No se encontró versión Open Access en Unpaywall.")
            
            # Pausa de 1 segundo para no saturar la API
            time.sleep(1)

if __name__ == "__main__":
    main()
