import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pdfplumber
from datetime import date, timedelta
import random
import math
import re
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(
    page_title="Frunance",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={}
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@300;400;600;700;800&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200');
@import url('https://fonts.googleapis.com/icon?family=Material+Icons');
* { font-family: 'Futura','Century Gothic','Nunito','Trebuchet MS',sans-serif !important; }
h1,h2,h3,h4 { font-weight:700 !important; letter-spacing:0.04em !important; }
.block-container { padding-top:1.2rem; }
[data-testid="metric-container"] {
    background:#12182b; border-radius:12px; padding:14px 18px; border:1px solid #1e2d4a;
}
.ticker-wrap {
    background:#0b111f; border-radius:10px; padding:10px 16px; margin-bottom:10px;
    border:1px solid #1e2d4a; overflow:hidden; white-space:nowrap;
}
.ticker-item { display:inline-block; margin-right:48px; font-size:0.88rem; letter-spacing:0.06em; }
.ticker-up   { color:#00e676; }
.ticker-down { color:#ff4444; }
.ticker-flat { color:#aaaaaa; }
.sidebar-title { font-size:1.3rem; font-weight:800; letter-spacing:0.12em; color:#00e676; }

/* Estilos limpios sin workarounds de íconos */
[data-testid="metric-container"] {
    background:#12182b; border-radius:12px;
    padding:14px 18px; border:1px solid #1e2d4a;
}
</style>
""", unsafe_allow_html=True)


# ── Conexión Supabase via REST API ────────
import requests as _req

def _sb_headers(prefer="return=representation"):
    try:
        key = st.secrets["SUPABASE_KEY"]
    except Exception:
        key = ""
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": prefer
    }

def _sb_url(tabla):
    try:
        url = st.secrets["SUPABASE_URL"]
    except Exception:
        url = ""
    return f"{url}/rest/v1/{tabla}"

MERCADOS = {
    "excel":       "Bogotá (Corabastos)",
    "pdf":         "Bogotá (Corabastos)",
    "historico":   "Demo",
    "granabastos": "Barranquilla (Granabastos)",
}
COLOR_MERCADO = {
    "Bogotá (Corabastos)":        "#00e676",
    "Barranquilla (Granabastos)": "#FFD600",
    "Demo":                       "#8888ff",
}
PRODUCTOS_DESTACADOS = [
    "Aguacate hass","Ahuyama (kg)","Papa pastusa (kg)","Naranja (kg)","Limón Tahití (kg)"
]
UNIDADES = {"bulto":50,"canasta":25,"kg":1,"kilogramo":1,"unidad":1}

# ── Traducciones Español → Papiamento ────
TRADUCCIONES_PAP = {
    "ALAS DE POLLO": "ALA DI GALIÑA",
    "MENUDENCIAS": "GIBLETS",
    "PECHUGA DE POLLO": "PECHO DI GALIÑA",
    "PERNILES DE POLLO": "DRUMSTICK DI GALIÑA",
    "POLLO SIN VICERAS": "galiña sin tripa",
    "BAGRE DORADO": "PISKA DI GALOPÁ",
    "BAGRE PINTADO": "CATFISH PINTÁ",
    "BLANQUILLO GALLEGO": "GALLEGO BLANQUILLO (GALLEGO BLANQUILLO)",
    "BOCA CHICO": "BOCA CHICO (BOCA CHIKITO)",
    "CACHAMA": "CACHAMA (CACHAMA)",
    "CAJARO": "CAJARO (CAJARO)",
    "CAMARÓN TIGRE": "KAMARON TIGER",
    "CAMARÓN TITI": "TITI SHRIMP",
    "CAPACETA": "CAPACETA (CAPACETA)",
    "CARACOL ALMEJA": "CLAM DI SNAIL",
    "CORVINA": "CORVINA (CORVINA)",
    "CUCHA": "CUCHA (CUCHA)",
    "DONCELLA": "DONCELLA (DONCELLA)",
    "FILETE DE MERLUZA": "FILETE DI HAKE",
    "FILETE DE ROBALO": "FILETE DI BASS DI LAMA",
    "GUALAJO": "GUALAJO (GUALAJO)",
    "MOJARRA DE MAR": "SEA MOJARRA (MOJARRA)",
    "MOJARRA O TILAPIA ROJA": "TILAPIA KÒRA (MOJARRA)",
    "NICURO": "NICURO (NICURO)",
    "PALETÓN": "PALETÓN (PALETÓN)",
    "PELADA": "PELADA (PELADA)",
    "PESCADO SECO": "PISKA SEKU",
    "PEZ MERO O POLLITO DE MAR": "GRUPO (GRUPO)",
    "PIRA BOTÓN": "PIRA BOTÓN (PIRA)",
    "SIERRA": "SIERRA (SIERRA)",
    "TOYO TIBURON PEQUEÑO": "TOYO (TOYO) TIBURON CHIKITO",
    "TRUCHA ARCO IRIS": "TRUITA DI AREKOIRIS",
    "VALENTÓN": "VALENTÓN (VALENTÓN)",
    "ACEITE (1000 C.C.)": "ZETA (1000 cc)",
    "ACEITE (500 C.C.)": "ZETA (500 cc)",
    "ACEITE GALÓN (3000 C.C)": "ZETA (GALON) (3000 c.c)",
    "ARROZ CORRIENTE": "Aros Regular",
    "ARROZ ORYZICA": "Arroz di Oryza",
    "ARROZ SOPA CRISTAL": "Sòpi di Aros di Kristal",
    "ARVEJA VERDE SECA": "Erwten Berde Seku",
    "AZUCAR EMPACADA": "Suku Empaketá",
    "AZUCAR SULFITADA": "Suku Sulfito",
    "CAFÉ 500GR": "Koffie 500g",
    "CEBADA": "Puspas",
    "CHOCOLATE DULCE": "Chukulati Dushi",
    "CUCHUCO DE CEBADA": "Porridge di Sebada",
    "CUCHUCO DE MAÍZ": "Papa di Maishi",
    "CUCHUCO DE TRIGO": "Papa di Trigu",
    "FRIJOL NIMA CALIMA": "Nima Calima Beans",
    "FRIJOL RADICAL": "Bonchi Radikal",
    "GARBANZO": "Chickpeas",
    "HARINA DE MAIZ": "Hariña di Maishi",
    "HARINA DE TRIGO": "Hariña di Trigu",
    "LECHE PROVO 400GR": "Provo Milk 400g",
    "MAIZ AMARILLO DURO": "Maishi Duru Geel",
    "MAIZ BLANCO DURO": "Maishi Duru Blanku",
    "MAIZ TRILLADO PETO": "Maishi kayente",
    "MANTECA HIDROGENADA": "Kortashon Hidrogená",
    "MARGARINA": "Margarina",
    "PANELAS": "Panela (Suku di Kaña No Refiná)",
    "PASTAS ALIMENTICIAS": "Pasta",
    "SAL": "Salu",
    "PLATANO COLICERO": "Plantain",
    "PLATANO HARTON": "Plantain",
    "ARRACACHA": "Arracacha (Berdura di Rais di Chile)",
    "PAPA CRIOLLA LAVADA": "Batata Krioyo Labá",
    "PAPA CRIOLLA SUCIA": "Batata Krioyo Sushi",
    "PAPA PASTUSA": "Batata Pastusa",
    "PAPA R12 INDUSTRIAL": "Batata R12 INDUSTRIAL",
    "PAPA R12 NEGRA": "R12 BATA PRETU",
    "PAPA R12 ROJA": "R12 BATA KÓRA",
    "PAPA SABANERA": "SABANERA POTATO",
    "PAPA SUPREMA": "SUPREMA POTATO",
    "PAPA TOCARRE": "TOCARRE POTATO",
    "YUCA ARMENIA": "ARMENIA YUCA",
    "YUCA LLANERA": "LLANERA YUCA",
    "AGUACATE HASS X TONELADA": "TIN AWACATI PA TON",
    "AGUACATE PIELES VERDES X TONELADA": "AWACADO DI CUERO BERDE PA TON",
    "BANANO CRIOLLO": "BANANA CRIOLLO",
    "BANANO URABA": "Banana di Urabá",
    "BREVA": "Fig",
    "COCO": "Koko",
    "CURUBA BOYACENCE": "Boyacá Curuba",
    "CURUBA SAN BERNARDO": "San Bernardo Curuba",
    "DURAZNO IMPORTADO": "Peach Importá",
    "DURAZNO NACIONAL": "Peach Doméstiko",
    "FEIJOA": "Feijoa",
    "FRESA": "Stròbèri",
    "GRANADILLA": "Granadilla",
    "GUANABANA": "Soursop",
    "GUAYABA": "Guyaba",
    "LIMÓN COMÚN": "Kalki Komun",
    "LIMÓN TAHITÍ": "Tahiti Lime",
    "LULO": "Lulo",
    "MANDARINA ARRAYANA": "Arrayana Mandarin",
    "MANDARINA ONECO": "Oneco Mandarin",
    "MANGO CHANCLETO": "Chancleto Mango",
    "MANGO DE AZUCAR": "Mango di suku",
    "MANGO REINA": "Reina Mango",
    "MANGO TOMMY": "Tommy Mango",
    "MANZANA NACIONAL": "Apel Doméstiko",
    "MANZANA ROJA IMPORTADA": "Apel Kòrá Importá",
    "MANZANA VERDA IMPORTADA": "Apel Berde Importá",
    "MARACUYA": "Fruta di Pashon",
    "MELÓN": "Melon",
    "MORA DE CASTILLA": "Blackberry",
    "NARANJA ARMENIA": "Oraño Armenio",
    "NARANJA GREY": "Oraño Gris",
    "NARANJA OMBLIGONA": "Navel Oranje",
    "NARANHA VALENCIA": "Valencia Oraño",
    "PAPAYA HAWAIANA": "Papaya Hawaiano",
    "PAPAYA MARADOL": "Papaya Maradol",
    "PAPAYA MELONA": "Papaya di melon",
    "PAPAYA REDONDA": "Papaya rondo",
    "PAPAYA TAINUNG": "Tainung Papaya",
    "PATILLA": "Patia",
    "PIÑA GOLF": "Pineapple GOLF",
    "PIÑA PEROLERA": "ANASA",
    "PITAHAYA": "PITAHAYA",
    "TOMATE DE ÁRBOL": "Tomati di palu",
    "UVA CHAMPA": "Champa Grape",
    "UVA NEGRA": "Druif Pretu",
    "UVA ROJA": "Druif Kòrá",
    "ACELGA": "Swiss Chard",
    "AHUYAMA": "Pampuna",
    "AJO ROSADO": "Garlic Ros",
    "ALCACHOFA": "Alcachofa",
    "APIO": "Selder",
    "ARVEJA VERDE SABANERA": "Erwten Berde",
    "BERENJENA": "Berehèin",
    "BROCOLI": "Bròkoli",
    "CALABACÍN": "Zucchini",
    "CALABAZA": "Pampuna",
    "CEBOLLA CABEZONA BLANCA": "Siboyo Blanku",
    "CEBOLLA CABEZONA ROJA": "Siboyo Kòrá",
    "CEBOLLA LARGA": "Scallion",
    "CILANTRO": "Koriantro",
    "COLIFLOR": "Koliflor",
    "ESPINACA": "Spinazi",
    "FRIJOL VERDE": "Bonchi Berde",
    "HABA VERDE SABANERA": "Broad Bean",
    "HABICHUELA": "Bonchi Berde",
    "LECHUGA": "Kròpslá",
    "MAZORCA": "Maishi riba e Cob",
    "PEPINO COHOMBRO": "Kòmkòmer",
    "PEPINO COMÚN": "Konkomber Komun",
    "PIMENTÓN": "Peper",
    "RÁBANO ROJO": "Rabano Kòrá",
    "REMOLACHA": "Remolacha",
    "REPOLLO": "Kolo",
    "TOMATE CHONTO": "Tomati Chonto",
    "TOMATE LARGA VIDA": "Tomati di bida largu",
    "TOMATE MILANO": "Tomati di Milano",
    "ZANAHORIA": "Wòrtel",
    "CADERA": "Rump",
    "CHATAS": "Bifstùk",
    "COSTILLA": "Repchi",
    "LOMO": "Lomo",
    "PIERNA": "Pia",
    "SOBREBARRIGA": "Flank Steak",
    "HUEVO BLANCO A": "Webu Blanku A",
    "HUEVO BLANCO AA": "Webu Blanku AA",
    "HUEVO BLANCO B": "Webu Blanku B",
    "HUEVO BLANCO EXTRA": "Webu Blanku Èkstra",
    "HUEVO ROJO A": "Webu Bruin A",
    "HUEVO ROJO AA": "Webu Bruin AA",
    "HUEVO ROJO B": "Webu Bruin B",
    "HUEVO ROJO EXTRA": "Webu Kòrá Èkstra",
    "CUAJADA": "Curd",
    "QUESO CAMPESINO": "Keshi di Kunukero",
    "QUESO COSTEÑO": "Keshi di Kosta",
    "QUESO DOBLE CREMA": "Keshi Dobel Krema",
    "QUESO PAIPA": "Keshi Paipa",
    "QUESO PERA": "Keshi di pera",
    "JENGIBRE": "Ehèmber",
    "ÑAME": "Yam",
    "CORAZÓN": "Kurason",
    "VINAGRE": "Binager",
}

# Tasa de cambio COP → ANG (Florín antillano)
# 1 ANG ≈ 2,450 COP (aproximado — se puede actualizar)
COP_A_ANG = 1 / 2450.0

def traducir(nombre, idioma="es"):
    """Traduce nombre de producto si el idioma es papiamento."""
    if idioma != "pap": return nombre
    return TRADUCCIONES_PAP.get(str(nombre).strip().upper(), nombre)

def fmt_precio(v, idioma="es"):
    """Formatea precio según idioma/moneda."""
    try:
        import math
        n = float(v)
        if math.isnan(n) or math.isinf(n): return "N/A"
        if idioma == "pap":
            ang = n * COP_A_ANG
            return f"ƒ {ang:,.2f}"
        return f"${n:,.0f}".replace(",",".")
    except: return "N/A"

UI_TEXT = {
    "es": {
        "titulo": "🌿 FRUNANCE",
        "subtitulo": "Plataforma de inteligencia de mercados de alimentos · Colombia",
        "producto": "Producto",
        "agrupar": "Agrupar",
        "mercado": "Mercado",
        "todos": "Todos",
        "ult_semana": "Última semana",
        "semana": "Semana",
        "mes": "Mes",
        "dia": "Día",
        "ult_precio": "Último precio",
        "precio_actual": "Precio actual",
        "cambio_ayer": "Cambio vs ayer",
        "max_hist": "Máximo histórico",
        "min_hist": "Mínimo histórico",
        "moneda": "COP",
        "flag": "🇨🇴",
        "lang_label": "Idioma / Lenguahe",
    },
    "pap": {
        "titulo": "🌿 FRUNANCE",
        "subtitulo": "Plataforma di inteligencia di merkado di kuminda · Kòrsou",
        "producto": "Produkto",
        "agrupar": "Agrupá",
        "mercado": "Merkado",
        "todos": "Tur",
        "ult_semana": "Último siman",
        "semana": "Siman",
        "mes": "Luna",
        "dia": "Día",
        "ult_precio": "Último presio",
        "precio_actual": "Presio aktual",
        "cambio_ayer": "Kambio vs awe",
        "max_hist": "Máximo histórico",
        "min_hist": "Mínimo histórico",
        "moneda": "ANG",
        "flag": "🇨🇼",
        "lang_label": "Idioma / Lenguahe",
    }
}

# ── DB (Supabase REST) ────────────────────
def init_db():
    pass  # Las tablas ya existen en Supabase

def guardar_registros(records, fuente, fecha):
    if not records: return 0
    ins = 0
    h = _sb_headers("resolution=ignore-duplicates,return=representation")
    # Enviar en lotes de 500 para mayor velocidad
    lote_size = 500
    datos = [{
        "fecha": fecha, "producto": r["producto"],
        "precio_min": r.get("precio_min"),
        "precio_max": r.get("precio_max"),
        "precio_prom": r.get("precio_prom"),
        "volumen": r.get("volumen"),
        "fuente": fuente, "unidad": r.get("unidad","")
    } for r in records]
    for i in range(0, len(datos), lote_size):
        lote = datos[i:i+lote_size]
        try:
            resp = _req.post(_sb_url("precios"), json=lote, headers=h)
            if resp.status_code in (200,201):
                ins += len(lote)
        except: pass
    return ins

def cargar_datos():
    """Carga todos los datos de Supabase paginando de 1000 en 1000."""
    todos = []
    offset = 0
    page_size = 1000
    try:
        h = _sb_headers()
        h["Prefer"] = "count=none"
        while True:
            resp = _req.get(
                _sb_url("precios") + f"?order=fecha,producto&limit={page_size}&offset={offset}",
                headers=h)
            if not resp.ok: break
            datos = resp.json()
            if not datos: break
            todos.extend(datos)
            if len(datos) < page_size: break
            offset += page_size
        df = pd.DataFrame(todos)
    except:
        df = pd.DataFrame()
    if not df.empty:
        df["fecha"] = pd.to_datetime(df["fecha"])
        df["mercado"] = df["fuente"].map(lambda f: MERCADOS.get(f,f))
    return df

def eliminar_datos(fecha_str, fuente):
    if fecha_str == "historico":
        _req.delete(_sb_url("precios") + f"?fuente=eq.{fuente}",
            headers=_sb_headers())
    else:
        _req.delete(_sb_url("precios") + f"?fecha=eq.{fecha_str}&fuente=eq.{fuente}",
            headers=_sb_headers())

def cargar_compras():
    try:
        resp = _req.get(
            _sb_url("compras") + "?order=id.desc&limit=1000",
            headers=_sb_headers())
        return pd.DataFrame(resp.json() if resp.ok else [])
    except:
        return pd.DataFrame()

def guardar_compra(fecha, producto, cantidad_kg, precio_unit, mercado, unidad_orig):
    total = cantidad_kg * precio_unit
    _req.post(_sb_url("compras"), headers=_sb_headers(), json={
        "fecha": str(fecha), "producto": producto,
        "cantidad_kg": cantidad_kg, "precio_unit": precio_unit,
        "total": total, "mercado": mercado, "unidad_orig": unidad_orig
    })
    return total

def eliminar_compra(cid):
    _req.delete(_sb_url("compras") + f"?id=eq.{cid}", headers=_sb_headers())

def historico_ya_existe():
    try:
        resp = _req.get(
            _sb_url("precios") + "?fuente=eq.historico&limit=1",
            headers=_sb_headers())
        return len(resp.json()) > 0
    except:
        return False

def generar_historico():
    PRODS_E = [
        ("Tomate chonto",2800,0.18,3),("Papa pastusa (kg)",1600,0.13,6),
        ("Papa criolla (kg)",2100,0.16,6),("Cebolla cabezona",1500,0.21,4),
        ("Zanahoria (kg)",950,0.11,5),("Plátano hartón",1200,0.14,11),
        ("Aguacate hass",3800,0.26,8),("Yuca (kg)",1050,0.12,7),
        ("Arroz blanco (kg)",2700,0.06,1),("Fríjol cargamanto",5200,0.15,2),
        ("Lenteja (kg)",4000,0.09,1),("Maíz amarillo (kg)",1400,0.08,9),
        ("Naranja (kg)",950,0.17,12),("Limón Tahití (kg)",1800,0.23,7),
        ("Mango tommy (kg)",2200,0.31,3),("Mora de castilla",3800,0.29,10),
        ("Pollo entero (kg)",8200,0.07,1),
    ]
    PRODS_P = [
        ("Lechuga batavia",1300,0.19,5),("Espinaca (manojo)",2400,0.21,4),
        ("Brócoli (kg)",3000,0.18,3),("Pepino cohombro",1050,0.16,6),
        ("Habichuela (kg)",2700,0.20,5),("Arveja verde (kg)",3200,0.17,4),
        ("Fresa (kg)",4500,0.26,9),("Pimentón rojo (kg)",2800,0.23,7),
        ("Cilantro (manojo)",850,0.22,1),("Ahuyama (kg)",1150,0.13,10),
        ("Berenjena (kg)",2100,0.19,8),("Remolacha (kg)",1400,0.14,3),
        ("Coliflor (kg)",2600,0.20,6),
    ]
    hoy = date.today()
    fin = hoy-timedelta(days=5); ini = fin-timedelta(days=335)
    dias = []
    d = ini
    while d<=fin:
        if d.weekday()<5: dias.append(d)
        d+=timedelta(days=1)

    def rw(base,vol,pico,dias):
        p,s=base,[]
        for d in dias:
            est=1+0.15*math.sin(2*math.pi*(d.month-pico)/12)
            p=max(p+0.03*(base*est-p)+p*vol*random.gauss(0,1)*0.04,base*0.4)
            s.append(round(p,0))
        return s

    random.seed(42); ti=0
    h = _sb_headers()
    h["Prefer"] = "resolution=ignore-duplicates,return=representation"
    for grp,fuente in [(PRODS_E,"historico"),(PRODS_P,"historico")]:
        for nm,base,vol,pico in grp:
            ps=rw(base,vol,pico,dias)
            # Agrupar en lotes de 100 para no saturar la API
            lote = []
            for i,d in enumerate(dias):
                p=ps[i]; sp=random.uniform(0.06,0.14)
                lote.append({
                    "fecha": str(d), "producto": nm,
                    "precio_min": round(p*(1-sp/2),0),
                    "precio_max": round(p*(1+sp/2),0),
                    "precio_prom": p,
                    "volumen": round(random.uniform(50,800),1),
                    "fuente": fuente, "unidad": "kg"
                })
                if len(lote) >= 100:
                    try:
                        resp = _req.post(_sb_url("precios"), json=lote, headers=h)
                        if resp.ok: ti += len(lote)
                    except: pass
                    lote = []
            if lote:
                try:
                    resp = _req.post(_sb_url("precios"), json=lote, headers=h)
                    if resp.ok: ti += len(lote)
                except: pass
    return ti,len(dias),len(PRODS_E)+len(PRODS_P)

# ── PARSERS ───────────────────────────────
NINGUNA="(Ninguna)"

def a_float(val):
    """Convierte precio colombiano a float.
    Maneja: $1.600, $1,600, $1.600.000, 1600, etc.
    """
    try:
        s = str(val).replace("$","").replace("\xa0","").replace(" ","").strip()
        if not s or s.lower() in ("nan","none",""): return None
        # Formato colombiano: punto=miles, coma=decimal -> $1.600 o $1.600.000
        # Formato internacional: coma=miles, punto=decimal -> $1,600
        puntos = s.count(".")
        comas  = s.count(",")
        if puntos > 0 and comas == 0:
            # Solo puntos: pueden ser separadores de miles colombianos
            # $1.600 -> 1600, $1.600.000 -> 1600000
            s = s.replace(".","")
        elif comas > 0 and puntos == 0:
            # Solo comas: separador de miles -> $1,600 -> 1600
            s = s.replace(",","")
        elif puntos > 0 and comas > 0:
            # Ambos: el último es decimal
            if s.rfind(".") > s.rfind(","):
                s = s.replace(",","")  # coma=miles, punto=decimal
            else:
                s = s.replace(".","").replace(",",".")  # punto=miles, coma=decimal
        return float(s)
    except:
        return None

def detectar_unidad(nombre):
    n=nombre.lower()
    for u in UNIDADES:
        if u in n: return u
    return "kg"

def registros_desde_df(df,c_prod,c_min,c_max,c_prom,c_vol):
    recs=[]
    for _,row in df.iterrows():
        nm=str(row[c_prod]).strip()
        if nm.lower() in ("nan","none","","producto","products"): continue
        r={"producto":nm,"unidad":detectar_unidad(nm)}
        if c_min!=NINGUNA:  r["precio_min"] =a_float(row[c_min])
        if c_max!=NINGUNA:  r["precio_max"] =a_float(row[c_max])
        if c_prom!=NINGUNA: r["precio_prom"]=a_float(row[c_prom])
        if c_vol!=NINGUNA:  r["volumen"]    =a_float(row[c_vol])
        recs.append(r)
    return recs

def parse_excel(file,c_prod,c_min,c_max,c_prom,c_vol):
    return registros_desde_df(pd.read_excel(file,dtype=str),c_prod,c_min,c_max,c_prom,c_vol)

def parse_pdf(file,tidx,c_prod,c_min,c_max,c_prom,c_vol):
    with pdfplumber.open(file) as pdf:
        tabs=[t for p in pdf.pages for t in p.extract_tables()]
    if not tabs: return []
    t=tabs[tidx]
    return registros_desde_df(pd.DataFrame(t[1:],columns=t[0]).astype(str),
                               c_prod,c_min,c_max,c_prom,c_vol)

def parse_pdf_todas_tablas(file, c_prod, c_min, c_max, c_prom, c_vol):
    """Extrae TODAS las tablas del PDF y combina los registros."""
    todos_records = []
    try:
        with pdfplumber.open(file) as pdf:
            tabs = [t for p in pdf.pages for t in p.extract_tables()]
        for t in tabs:
            if not t or len(t) < 2: continue
            # Limpiar encabezados
            headers = [str(h) if h is not None else f"col_{i}"
                      for i,h in enumerate(t[0])]
            # Verificar que la columna de producto existe
            if c_prod not in headers: continue
            try:
                rows = [[str(c) if c is not None else "" for c in row]
                        for row in t[1:]]
                df = pd.DataFrame(rows, columns=headers)
                recs = registros_desde_df(df, c_prod, c_min, c_max, c_prom, c_vol)
                # Filtrar filas vacías o de encabezado repetido
                recs = [r for r in recs
                        if r["producto"] and
                        r["producto"].lower() not in ("nombre","product","nan","none","")]
                todos_records.extend(recs)
            except: continue
    except: pass
    return todos_records

# ── HELPERS ───────────────────────────────
def col_precio(df):
    for c in ["precio_prom","precio_min","precio_max"]:
        if c in df.columns and df[c].notna().any(): return c
    return None

def fmtcop(v):
    try:
        if v is None: return "N/A"
        n = float(v)
        import math
        if math.isnan(n) or math.isinf(n): return "N/A"
        return f"${n:,.0f}".replace(",",".")
    except: return "N/A"

FONT = "Futura, Century Gothic, Nunito, sans-serif"

# ── GRÁFICAS ──────────────────────────────
def fig_velas(df_p, nombre, freq, color="#00e676"):
    """
    Construye velas usando:
    - open  = precio del día anterior (shift)
    - close = precio del día actual
    - high  = precio_max si existe, sino max(open,close)*1.01
    - low   = precio_min si existe, sino min(open,close)*0.99
    Así cada vela muestra el movimiento real entre días.
    """
    cp = col_precio(df_p)
    if not cp: return None
    df = df_p.set_index("fecha").sort_index()
    ser = pd.to_numeric(df[cp], errors="coerce").dropna()
    if ser.empty: return None

    # Resamplear por período
    close = ser.resample(freq).last()
    open_ = close.shift(1)  # precio del período anterior = open
    high  = ser.resample(freq).max()
    low   = ser.resample(freq).min()

    # Usar precio_min/max reales si existen
    if "precio_min" in df.columns:
        real_low = pd.to_numeric(df["precio_min"], errors="coerce").resample(freq).min()
        low = low.combine(real_low, min)
    if "precio_max" in df.columns:
        real_high = pd.to_numeric(df["precio_max"], errors="coerce").resample(freq).max()
        high = high.combine(real_high, max)

    oh = pd.DataFrame({"open":open_,"high":high,"low":low,"close":close}).dropna()
    if oh.empty: return None

    dn = "#ff1744"
    fig = make_subplots(rows=1, cols=1)
    fig.add_trace(go.Candlestick(
        x=oh.index,
        open=oh["open"], high=oh["high"],
        low=oh["low"],   close=oh["close"],
        name=nombre,
        increasing_line_color=color, increasing_fillcolor=color,
        decreasing_line_color=dn,    decreasing_fillcolor=dn
    ))
    if len(oh) >= 4:
        fig.add_trace(go.Scatter(
            x=oh.index, y=oh["close"].rolling(4).mean(),
            name="Media móvil (4p)",
            line=dict(color="#FFD600", width=1.8, dash="dot")
        ))
    fig.update_layout(
        title=dict(text=f"📈  {nombre}", font=dict(size=18, family=FONT)),
        xaxis_rangeslider_visible=False,
        template="plotly_dark", height=520,
        yaxis_title="Precio (COP)",
        yaxis_tickformat=",.0f",
        legend=dict(orientation="h", y=1.06, x=0),
        margin=dict(l=60, r=30, t=70, b=40),
        plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
        font=dict(family=FONT)
    )
    return fig

def fig_comparar_mercados(df_all, producto, freq):
    mercados=df_all[df_all["producto"]==producto]["mercado"].unique()
    if not len(mercados): return None
    fig=go.Figure()
    for merc in mercados:
        color=COLOR_MERCADO.get(merc,"#ffffff")
        dm=df_all[(df_all["producto"]==producto)&(df_all["mercado"]==merc)].set_index("fecha").sort_index()
        cp=col_precio(dm.reset_index())
        if not cp: continue
        ser=pd.to_numeric(dm[cp],errors="coerce").dropna()
        if ser.empty: continue
        close=ser.resample(freq).last()
        open_=close.shift(1)
        high=ser.resample(freq).max()
        low=ser.resample(freq).min()
        oh=pd.DataFrame({"open":open_,"high":high,"low":low,"close":close}).dropna()
        if oh.empty: continue
        fig.add_trace(go.Candlestick(x=oh.index,open=oh["open"],high=oh["high"],
            low=oh["low"],close=oh["close"],name=merc,
            increasing_line_color=color,increasing_fillcolor=color,
            decreasing_line_color="#ff1744",decreasing_fillcolor="#ff1744"))
    fig.update_layout(title=f"Comparación — {producto}",
        xaxis_rangeslider_visible=False,template="plotly_dark",height=480,
        yaxis_title="Precio (COP)",legend=dict(orientation="h",y=1.06),
        margin=dict(l=50,r=30,t=70,b=40),plot_bgcolor="#0d1117",
        paper_bgcolor="#0d1117",font=dict(family=FONT))
    return fig

def fig_barras_dia(df_all, fecha_sel, mercado_sel=None):
    dd=df_all[df_all["fecha"]==pd.Timestamp(fecha_sel)].copy()
    if mercado_sel: dd=dd[dd["mercado"]==mercado_sel]
    cp=col_precio(dd)
    if not cp: return None
    dd[cp]=pd.to_numeric(dd[cp],errors="coerce")
    dd=dd.dropna(subset=[cp]).sort_values(cp,ascending=True)
    tit=f"Precios del {pd.Timestamp(fecha_sel).strftime('%d/%m/%Y')}"
    if mercado_sel: tit+=f" — {mercado_sel}"
    fig=go.Figure(go.Bar(x=dd[cp],y=dd["producto"],orientation="h",
        marker=dict(color=dd[cp],colorscale="Teal"),
        text=dd[cp].apply(lambda v:f"${v:,.0f}"),textposition="outside"))
    fig.update_layout(title=tit,template="plotly_dark",
        height=max(400,len(dd)*24+100),xaxis_title="Precio (COP)",
        plot_bgcolor="#0d1117",paper_bgcolor="#0d1117",
        margin=dict(l=180,r=80,t=60,b=40),font=dict(family=FONT))
    return fig

def fig_evolucion(df_all, productos, mercado_sel=None):
    cp=col_precio(df_all)
    if not cp: return None
    fig=go.Figure()
    for prod in productos:
        dp=df_all[df_all["producto"]==prod]
        if mercado_sel: dp=dp[dp["mercado"]==mercado_sel]
        dp=dp.sort_values("fecha")
        dp[cp]=pd.to_numeric(dp[cp],errors="coerce")
        fig.add_trace(go.Scatter(x=dp["fecha"],y=dp[cp],mode="lines+markers",name=prod))
    fig.update_layout(title="Evolución de precios",template="plotly_dark",height=430,
        yaxis_title="Precio (COP)",plot_bgcolor="#0d1117",paper_bgcolor="#0d1117",
        margin=dict(l=50,r=30,t=60,b=40),font=dict(family=FONT))
    return fig

def ticker_html(df_all):
    if df_all.empty or len(df_all["fecha"].unique())<2: return ""
    fechas=sorted(df_all["fecha"].unique())
    ult,pen=fechas[-1],fechas[-2]
    items=[]
    for prod in PRODUCTOS_DESTACADOS:
        dp=df_all[df_all["producto"]==prod]; cp=col_precio(dp)
        if not cp: continue
        hoy =pd.to_numeric(dp[dp["fecha"]==ult][cp], errors="coerce").mean()
        ayer=pd.to_numeric(dp[dp["fecha"]==pen][cp], errors="coerce").mean()
        if pd.isna(hoy): continue
        if pd.notna(ayer) and ayer>0:
            pct=(hoy-ayer)/ayer*100
            arr="▲" if pct>=0 else "▼"
            cls="ticker-up" if pct>=0 else "ticker-down"
            items.append(f'<span class="ticker-item {cls}">{prod}&nbsp;&nbsp;{fmtcop(hoy)}&nbsp;&nbsp;{arr} {abs(pct):.1f}%</span>')
        else:
            items.append(f'<span class="ticker-item ticker-flat">{prod}&nbsp;&nbsp;{fmtcop(hoy)}</span>')
    if not items: return ""
    return '<div class="ticker-wrap">'+"".join(items*4)+"</div>"

# ─────────────────────────────────────────────
# INIT
# ─────────────────────────────────────────────
init_db()
df_all=cargar_datos()

# ══════════════ SIDEBAR ══════════════════════
with st.sidebar:
    st.markdown('<div class="sidebar-title">🌿 FRUNANCE</div>',unsafe_allow_html=True)
    st.caption("Mercados de alimentos · Colombia")
    st.divider()

    # Selector de idioma con banderas
    lang_col1, lang_col2 = st.columns(2)
    if "idioma" not in st.session_state:
        st.session_state["idioma"] = "es"
    if lang_col1.button("🇨🇴 Español", use_container_width=True,
        type="primary" if st.session_state["idioma"]=="es" else "secondary"):
        st.session_state["idioma"] = "es"; st.rerun()
    if lang_col2.button("🇨🇼 Papiamento", use_container_width=True,
        type="primary" if st.session_state["idioma"]=="pap" else "secondary"):
        st.session_state["idioma"] = "pap"; st.rerun()
    IDIOMA = st.session_state.get("idioma","es")
    TX = UI_TEXT[IDIOMA]

    st.divider()
    st.header("📁 Cargar datos del día")
    fecha_carga=st.date_input("Fecha",value=date.today())
    fecha_str=str(fecha_carga)

    # Excel
    st.divider(); st.subheader("📊 Excel")
    fuente_e=st.selectbox("Mercado",["Bogotá (Corabastos)","Barranquilla (Granabastos)"],key="src_e")
    fk_e="excel" if "Bogotá" in fuente_e else "granabastos"
    ef=st.file_uploader("Archivo .xlsx",type=["xlsx","xls"])
    if ef:
        dpe=pd.read_excel(ef,dtype=str); ef.seek(0)
        st.dataframe(dpe.head(3),use_container_width=True)
        ce=list(dpe.columns); oe=[NINGUNA]+ce
        cep=st.selectbox("PRODUCTO *",ce,key="ep")
        cem=st.selectbox("PRECIO MÍN",oe,key="emn")
        ceM=st.selectbox("PRECIO MÁX",oe,key="emx")
        cePr=st.selectbox("PRECIO PROM",oe,key="epr")
        ceV=st.selectbox("VOLUMEN",oe,key="ev")
        if st.button("✅ Guardar Excel",use_container_width=True,type="primary"):
            n=guardar_registros(parse_excel(ef,cep,cem,ceM,cePr,ceV),fk_e,fecha_str)
            if n: st.success(f"✔ {n} productos"); df_all=cargar_datos(); st.rerun()
            else: st.warning("Ya existían.")

    # PDF
    st.divider(); st.subheader("📄 PDF")
    fuente_p=st.selectbox("Mercado",["Bogotá (Corabastos)","Barranquilla (Granabastos)"],key="src_p")
    fk_p="pdf" if "Bogotá" in fuente_p else "granabastos"
    pf=st.file_uploader("Archivo .pdf",type=["pdf"])
    if pf:
        with pdfplumber.open(pf) as _p:
            tabs=[t for pg in _p.pages for t in pg.extract_tables()]
        pf.seek(0)
        if not tabs: st.error("No se encontraron tablas.")
        else:
            tab_opciones=[f"Tabla {i+1} ({len(tabs[i])} filas)" for i in range(len(tabs))]
            tab_sel=st.selectbox("Tabla",tab_opciones)
            it=tab_opciones.index(tab_sel)
            t=tabs[it]; dpp=pd.DataFrame(t[1:],columns=t[0]).astype(str)
            st.dataframe(dpp.head(3),use_container_width=True)
            cp2=list(dpp.columns); op2=[NINGUNA]+cp2
            cpp=st.selectbox("PRODUCTO *",cp2,key="pp")
            cpm=st.selectbox("PRECIO MÍN",op2,key="pmn")
            cpM=st.selectbox("PRECIO MÁX",op2,key="pmx")
            cpPr=st.selectbox("PRECIO PROM",op2,key="ppr")
            cpV=st.selectbox("VOLUMEN",op2,key="pv")
            if st.button("✅ Guardar PDF",use_container_width=True,type="primary"):
                n=guardar_registros(parse_pdf(pf,it,cpp,cpm,cpM,cpPr,cpV),fk_p,fecha_str)
                if n: st.success(f"✔ {n} productos"); df_all=cargar_datos(); st.rerun()
                else: st.warning("Ya existían.")

    # Test conexión Supabase
    st.divider()
    if st.button("🔌 Probar conexión Supabase", use_container_width=True):
        try:
            resp = _req.get(_sb_url("precios") + "?limit=1", headers=_sb_headers())
            if resp.ok:
                st.success(f"✅ Conexión OK — status {resp.status_code}")
            else:
                st.error(f"❌ Error {resp.status_code}: {resp.text[:200]}")
        except Exception as e:
            st.error(f"❌ Excepción: {e}")

    # Histórico
    st.divider(); st.subheader("🕰️ Histórico demo")
    if historico_ya_existe():
        st.success("✔ Demo cargado")
        if st.button("🗑️ Borrar demo",use_container_width=True):
            eliminar_datos("historico", "historico")
            df_all=cargar_datos(); st.rerun()
    else:
        if st.button("⚡ Cargar demo",use_container_width=True,type="primary"):
            with st.spinner("Generando datos y enviando a Supabase..."):
                n,d,p=generar_historico()
            if n > 0:
                st.success(f"✔ {n:,} registros guardados")
                df_all=cargar_datos(); st.rerun()
            else:
                st.error("❌ No se guardaron registros. Prueba el botón 'Probar conexión Supabase' arriba.")

    # Eliminar
    if not df_all.empty:
        st.divider(); st.subheader("🗑️ Eliminar")
        fdel=st.selectbox("Fecha",sorted(df_all["fecha"].dt.date.unique(),reverse=True),key="fdel")
        sdel=st.selectbox("Fuente",["excel","pdf","granabastos","historico"],key="sdel")
        if st.button("Eliminar",use_container_width=True):
            eliminar_datos(str(fdel),sdel); df_all=cargar_datos(); st.rerun()

# ══════════════ MAIN ═════════════════════════
IDIOMA = st.session_state.get("idioma","es")
TX = UI_TEXT[IDIOMA]
st.markdown(f'<h1 style="letter-spacing:0.15em;font-size:2.2rem;">{TX["titulo"]}</h1>',unsafe_allow_html=True)
st.caption(TX["subtitulo"])

if df_all.empty:
    st.info("👈  Carga archivos o el histórico de demo desde el panel izquierdo.")
    st.stop()

# Ticker
tk=ticker_html(df_all)
if tk: st.markdown(tk,unsafe_allow_html=True)

# KPIs
fechas=sorted(df_all["fecha"].unique()); ult=fechas[-1]
df_hoy=df_all[df_all["fecha"]==ult]; cr=col_precio(df_all)
mercs_disp=sorted([m for m in df_all["mercado"].unique() if m!="Demo"])
k1,k2,k3,k4,k5=st.columns(5)
k1.metric("🌿 Productos",df_all["producto"].nunique())
k2.metric("📅 Días",len(fechas))
k3.metric("🗓️ Actualización",pd.Timestamp(ult).strftime("%d/%m/%Y"))
k4.metric("🏪 Mercados",len(mercs_disp) if mercs_disp else df_all["mercado"].nunique())
if cr:
    med=pd.to_numeric(df_hoy[cr],errors="coerce").median()
    k5.metric("💰 Precio mediano",fmtcop(med) if pd.notna(med) else "N/A")

st.divider()

# ── TABS ──────────────────────────────────────
t1,t2,t3,t4,t5,t6,t7=st.tabs([
    "📈 Velas","🏪 Por mercado","⚖️ Comparar mercados",
    "📊 Precios del día","📉 Evolución","🛒 Compras","📂 Carga masiva"
])

# ── T1: Velas ─────────────────────────────────
with t1:
    prods=sorted(df_all["producto"].unique())
    # Mostrar nombres traducidos en el selector
    prods_display=[traducir(p,IDIOMA) for p in prods]
    prods_map={traducir(p,IDIOMA):p for p in prods}  # display->original
    ca,cb,cc=st.columns([3,1,1])
    ag_opts=[TX["ult_semana"],TX["semana"],TX["mes"],TX["dia"]]
    ag_key =["Última semana","Semana","Mes","Día"]
    ps_disp=ca.selectbox(TX["producto"],prods_display,key="t1p")
    ps=prods_map.get(ps_disp,ps_disp)  # original name for DB lookup
    ag_disp=cb.selectbox(TX["agrupar"],ag_opts,key="t1ag")
    ag=ag_key[ag_opts.index(ag_disp)]
    mf_opts=[TX["todos"]]+sorted(df_all["mercado"].unique().tolist())
    mf=cc.selectbox(TX["mercado"],mf_opts,key="t1m")
    if mf==TX["todos"]: mf="Todos"
    freq={"Semana":"W","Mes":"ME","Día":"D","Última semana":"D"}[ag]
    dfp=df_all[df_all["producto"]==ps].copy()
    if mf!="Todos": dfp=dfp[dfp["mercado"]==mf]

    # Filtrar últimos 5 días si se selecciona "Última semana"
    if ag=="Última semana" and not dfp.empty:
        ultimas_fechas=sorted(dfp["fecha"].unique())[-5:]
        dfp=dfp[dfp["fecha"].isin(ultimas_fechas)]

    uni=(dfp["unidad"].dropna().mode().iloc[0] if "unidad" in dfp.columns and not dfp["unidad"].dropna().empty else "kg")
    if uni in UNIDADES and UNIDADES[uni]>1:
        st.info(f"ℹ️ Producto transado por **{uni}** ({UNIDADES[uni]} kg). Precio/kg = precio ÷ {UNIDADES[uni]}.")
    col_v=COLOR_MERCADO.get(mf,"#00e676") if mf!="Todos" else "#00e676"

    # Mostrar último precio destacado encima de la gráfica
    crp=col_precio(dfp)
    if crp and not dfp.empty:
        dfp[crp]=pd.to_numeric(dfp[crp],errors="coerce")
        pa=dfp[dfp["fecha"]==dfp["fecha"].max()][crp].dropna().values
        pa=pa[0] if len(pa) else None
        pant=dfp[dfp["fecha"]<dfp["fecha"].max()][crp].dropna().values
        if pa:
            fecha_ult=dfp["fecha"].max().strftime("%d/%m/%Y")
            lbl_ult = TX.get("ult_precio","Último precio")
            if len(pant):
                cam=pa-pant[-1]; pct=cam/pant[-1]*100
                arrow="▲" if pct>=0 else "▼"
                color_arr="#00e676" if pct>=0 else "#ff4444"
                st.markdown(
                    f'<div style="font-size:1.1rem;padding:8px 0 4px 0;">'
                    f'<b>{lbl_ult} ({fecha_ult}):</b> '
                    f'<span style="font-size:1.4rem;font-weight:800;">{fmt_precio(pa,IDIOMA)}</span>'
                    f'&nbsp;&nbsp;<span style="color:{color_arr};font-size:1rem;">'
                    f'{arrow} {fmt_precio(abs(cam),IDIOMA)} ({pct:+.1f}%)</span></div>',
                    unsafe_allow_html=True)
            else:
                st.markdown(
                    f'<div style="font-size:1.1rem;padding:8px 0 4px 0;">'
                    f'<b>{lbl_ult} ({fecha_ult}):</b> '
                    f'<span style="font-size:1.4rem;font-weight:800;">{fmt_precio(pa,IDIOMA)}</span></div>',
                    unsafe_allow_html=True)

    if len(dfp)<2:
        st.info(f"Necesitas al menos 2 días de datos para **{ps}**.")
    else:
        fv=fig_velas(dfp,ps,freq,col_v)
        if fv: st.plotly_chart(fv,use_container_width=True)
        if crp:
            m1,m2,m3,m4=st.columns(4)
            m1.metric(TX["precio_actual"],fmt_precio(pa,IDIOMA) if pa else "N/A")
            if pa and len(pant):
                cam=pa-pant[-1]; pct=cam/pant[-1]*100
                m2.metric(TX["cambio_ayer"],fmt_precio(cam,IDIOMA),f"{pct:+.1f}%")
            m3.metric(TX["max_hist"],fmt_precio(dfp[crp].max(),IDIOMA))
            m4.metric(TX["min_hist"],fmt_precio(dfp[crp].min(),IDIOMA))

    st.divider()
    key_show = f"show_compra_{ps}"
    if key_show not in st.session_state:
        st.session_state[key_show] = False
    if st.button("🛒 Registrar compra de este producto", key=f"tog_{ps}"):
        st.session_state[key_show] = not st.session_state[key_show]
    if st.session_state[key_show]:
        with st.container():
            crp2=col_precio(df_all[df_all["producto"]==ps])
            psug=None
            if crp2:
                psug=pd.to_numeric(df_all[(df_all["producto"]==ps)&(df_all["fecha"]==ult)][crp2],errors="coerce").mean()
            bc1,bc2,bc3=st.columns(3)
            ckg=bc1.number_input("Cantidad (kg)",min_value=0.0,step=0.5,key=f"ck_{ps}")
            pcu=bc2.number_input("Precio/kg (COP)",min_value=0.0,
                value=float(psug) if psug and not pd.isna(psug) else 0.0,
                step=100.0,key=f"pc_{ps}")
            mcu=bc3.selectbox("Mercado",sorted(df_all["mercado"].unique()),key=f"mc_{ps}")
            if st.button("➕ Agregar compra",key=f"bt_{ps}"):
                if ckg>0 and pcu>0:
                    tot=guardar_compra(date.today(),ps,ckg,pcu,mcu,uni)
                    st.success(f"✔ {ckg} kg × {fmtcop(pcu)} = **{fmtcop(tot)}**")
                else: st.warning("Ingresa cantidad y precio.")

# ── T2: Por mercado ───────────────────────────
with t2:
    todos_m=sorted(df_all["mercado"].unique())
    ms2=st.selectbox("Mercado",todos_m,key="t2m")
    dfm=df_all[df_all["mercado"]==ms2]
    if dfm.empty: st.info("Sin datos.")
    else:
        fms=sorted(dfm["fecha"].dt.date.unique(),reverse=True)
        st.markdown("**Selecciona la fecha:**")
        if len(fms)>1:
            opciones2=[f.strftime("%d/%m/%Y") for f in fms]
            sel2=st.select_slider("Fecha",options=opciones2,value=opciones2[0],key="t2sl")
            fsel2=fms[opciones2.index(sel2)]
        else: fsel2=fms[0]
        st.caption(f"**{fsel2.strftime('%d/%m/%Y')}** — {ms2}")
        fb=fig_barras_dia(df_all,fsel2,ms2)
        if fb: st.plotly_chart(fb,use_container_width=True)
        dfd=dfm[dfm["fecha"]==pd.Timestamp(fsel2)].copy()
        cp3=col_precio(dfd)
        if cp3:
            dfd[cp3]=pd.to_numeric(dfd[cp3],errors="coerce")
            cols_show=["producto"]
            if "unidad" in dfd.columns: cols_show.append("unidad")
            cols_show.append(cp3)
            ds=dfd[cols_show].copy()
            ds.columns=["Producto"]+( ["Unidad"] if "unidad" in dfd.columns else [])+["Precio (COP)"]
            ds["Precio (COP)"]=ds["Precio (COP)"].apply(lambda v:f"${v:,.0f}" if pd.notna(v) else "N/A")
            st.dataframe(ds,use_container_width=True,hide_index=True)

# ── T3: Comparar mercados ──────────────────────
with t3:
    st.subheader("⚖️ Comparar el mismo producto entre mercados")
    ppmc=df_all.groupby("producto")["mercado"].nunique()
    pcom=sorted(ppmc[ppmc>=2].index.tolist())
    todos3=sorted(df_all["producto"].unique())
    if pcom: st.success(f"✔ {len(pcom)} productos en más de un mercado.")
    solo=st.checkbox("Solo productos en ambos mercados",value=bool(pcom),key="t3f")
    lp3=pcom if solo and pcom else todos3
    c3a,c3b=st.columns([3,1])
    pc3=c3a.selectbox("Producto",lp3,key="t3p")
    ag3=c3b.selectbox("Agrupar",["Semana","Mes","Día"],key="t3ag")
    fr3={"Semana":"W","Mes":"ME","Día":"D"}[ag3]
    fc=fig_comparar_mercados(df_all,pc3,fr3)
    if fc:
        st.plotly_chart(fc,use_container_width=True)
        st.markdown("**Último precio por mercado:**")
        filas=[]
        for merc in sorted(df_all[df_all["producto"]==pc3]["mercado"].unique()):
            dpm=df_all[(df_all["producto"]==pc3)&(df_all["mercado"]==merc)]
            cpm=col_precio(dpm)
            if not cpm: continue
            up=pd.to_numeric(dpm[dpm["fecha"]==dpm["fecha"].max()][cpm],errors="coerce").mean()
            um=(dpm["unidad"].dropna().mode().iloc[0] if "unidad" in dpm.columns and not dpm["unidad"].dropna().empty else "kg")
            filas.append({"Mercado":merc,"Precio":fmtcop(up),"Unidad":um})
        if filas: st.dataframe(pd.DataFrame(filas),use_container_width=True,hide_index=True)
        st.divider()
        if "show_compra_comp" not in st.session_state:
            st.session_state["show_compra_comp"] = False
        if st.button("🛒 Registrar compra desde comparación", key="tog_comp"):
            st.session_state["show_compra_comp"] = not st.session_state["show_compra_comp"]
        if st.session_state["show_compra_comp"]:
            with st.container():
                cc1,cc2,cc3=st.columns(3)
                cck=cc1.number_input("Cantidad (kg)",min_value=0.0,step=0.5,key="cck")
                pck=cc2.number_input("Precio/kg (COP)",min_value=0.0,step=100.0,key="pck")
                mck=cc3.selectbox("Compra en",sorted(df_all[df_all["producto"]==pc3]["mercado"].unique()),key="mck")
                if st.button("➕ Agregar compra",key="btck"):
                    if cck>0 and pck>0:
                        tot=guardar_compra(date.today(),pc3,cck,pck,mck,"kg")
                        st.success(f"✔ {cck} kg × {fmtcop(pck)} en {mck} = **{fmtcop(tot)}**")
                    else: st.warning("Ingresa cantidad y precio.")
    else: st.info("Sin datos suficientes para este producto.")

# ── T4: Precios del día ───────────────────────
with t4:
    fd4=sorted([f.date() for f in fechas],reverse=True)
    st.markdown("**Selecciona la fecha:**")
    opciones4=[f.strftime("%d/%m/%Y") for f in fd4]
    sel4=st.select_slider("Fecha",options=opciones4,value=opciones4[0],key="t4sl")
    fc4=fd4[opciones4.index(sel4)]
    mf4=st.selectbox("Mercado",["Todos"]+sorted(df_all["mercado"].unique().tolist()),key="t4m")
    fb4=fig_barras_dia(df_all,fc4,None if mf4=="Todos" else mf4)
    if fb4: st.plotly_chart(fb4,use_container_width=True)

# ── T5: Evolución ─────────────────────────────
with t5:
    mev=st.selectbox("Mercado",["Todos"]+sorted(df_all["mercado"].unique().tolist()),key="t5m")
    pev=st.multiselect("Productos (máx 10)",sorted(df_all["producto"].unique()),max_selections=10)
    if len(pev)>=2:
        fe=fig_evolucion(df_all,pev,None if mev=="Todos" else mev)
        if fe: st.plotly_chart(fe,use_container_width=True)
    else: st.info("Selecciona al menos 2 productos.")

# ── T6: Compras ───────────────────────────────
with t6:
    st.subheader("🛒 Registro de compras")
    dfc=cargar_compras()
    if dfc.empty:
        st.info("Sin compras registradas. Usa el botón 🛒 en las pestañas de producto.")
    else:
        tg=dfc["total"].sum()
        cr1,cr2,cr3=st.columns(3)
        cr1.metric("Total invertido",fmtcop(tg))
        cr2.metric("Compras registradas",len(dfc))
        cr3.metric("Productos distintos",dfc["producto"].nunique())
        st.divider()
        dfs=dfc.copy()
        dfs["total"]=dfs["total"].apply(fmtcop)
        dfs["precio_unit"]=dfs["precio_unit"].apply(fmtcop)
        dfs=dfs.rename(columns={"fecha":"Fecha","producto":"Producto","cantidad_kg":"Kg",
            "precio_unit":"Precio/kg","total":"Total","mercado":"Mercado","unidad_orig":"Unidad"})
        st.dataframe(dfs.drop(columns=["id"],errors="ignore"),
                     use_container_width=True,hide_index=True)
        st.divider()
        idc=dfc["id"].tolist()
        idd=st.selectbox("ID a eliminar",idc,key="dlc")
        if st.button("🗑️ Eliminar compra"):
            eliminar_compra(idd); st.rerun()
        csv_c=dfc.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Exportar CSV",csv_c,"frunance_compras.csv","text/csv")
        if "mercado" in dfc.columns:
            gm=dfc.groupby("mercado")["total"].sum().reset_index()
            fg=go.Figure(go.Pie(labels=gm["mercado"],values=gm["total"],hole=0.4,
                marker_colors=["#00e676","#FFD600","#8888ff"]))
            fg.update_layout(title="Gasto por mercado",template="plotly_dark",height=320,
                paper_bgcolor="#0d1117",font=dict(family=FONT))
            st.plotly_chart(fg,use_container_width=True)

# ── T7: Carga masiva ──────────────────────────
with t7:
    def ext_fecha(nombre):
        for pat in [r'(\d{4})[-_](\d{2})[-_](\d{2})',r'(\d{2})[-_](\d{2})[-_](\d{4})',r'(\d{4})(\d{2})(\d{2})']:
            m=re.search(pat,nombre)
            if m:
                g=m.groups()
                try:
                    if int(g[0])>1900: return date(int(g[0]),int(g[1]),int(g[2]))
                    else: return date(int(g[2]),int(g[1]),int(g[0]))
                except: pass
        return None

    st.subheader("📂 Carga masiva de histórico")
    st.info("Sube varios archivos a la vez (Ctrl+clic). El sistema detecta la fecha del nombre del archivo.")
    tm=st.radio("Tipo",["📄 PDF","📊 Excel","🔀 Mixto"],horizontal=True,key="tm")
    ta=(["pdf"] if "PDF" in tm else ["xlsx","xls"] if "Excel" in tm else ["pdf","xlsx","xls"])
    fm7=st.selectbox("Mercado",["Bogotá (Corabastos)","Barranquilla (Granabastos)"],key="fm7")
    fk7="pdf" if "Bogotá" in fm7 else "granabastos"
    ams=st.file_uploader("Archivos",type=ta,accept_multiple_files=True,key="masivo")
    if ams:
        exls=[f for f in ams if f.name.lower().endswith((".xlsx",".xls"))]
        pdfs=[f for f in ams if f.name.lower().endswith(".pdf")]
        st.markdown(f"**{len(ams)} archivos** ({len(pdfs)} PDF · {len(exls)} Excel)")
        cpdf,cexc={},{}
        if pdfs:
            st.markdown("#### Config PDFs")
            st.info("✅ Se importarán **todas las tablas** de cada PDF automáticamente (Frutas, Verduras, Granos, etc.)")
            with pdfplumber.open(pdfs[0]) as _p:
                tbs=[t for pg in _p.pages for t in pg.extract_tables()]
            pdfs[0].seek(0)
            # Usar la primera tabla con más de 3 filas como referencia
            t7_ref = next((t for t in tbs if t and len(t)>=3), tbs[0] if tbs else None)
            if t7_ref:
                headers7=[str(h) if h is not None else f"col_{i}"
                          for i,h in enumerate(t7_ref[0])]
                seen={}; unique_h=[]
                for h in headers7:
                    if h in seen: seen[h]+=1; unique_h.append(f"{h}_{seen[h]}")
                    else: seen[h]=0; unique_h.append(h)
                try:
                    df7=pd.DataFrame(
                        [[str(c) if c is not None else "" for c in row]
                         for row in t7_ref[1:]],
                        columns=unique_h)
                    st.caption("Vista previa (primera tabla del PDF):")
                    st.dataframe(df7.head(3),use_container_width=True)
                except Exception as e:
                    st.warning(f"Vista previa no disponible: {e}")
                    df7=pd.DataFrame(columns=unique_h)
                c7=list(df7.columns); o7=[NINGUNA]+c7
                p71,p72=st.columns(2)
                cpdf={"prod":p71.selectbox("PRODUCTO *",c7,key="mprod"),
                    "min":p71.selectbox("MÍN",o7,key="mmin"),
                    "max":p72.selectbox("MÁX",o7,key="mmax"),
                    "prom":p72.selectbox("PROM",o7,key="mprom"),
                    "vol":p72.selectbox("VOL",o7,key="mvol")}
        if exls:
            st.markdown("#### Config Excel")
            de7=pd.read_excel(exls[0],dtype=str); exls[0].seek(0)
            st.dataframe(de7.head(3).astype(str),use_container_width=True)
            ce7=list(de7.columns); oe7=[NINGUNA]+ce7
            e71,e72=st.columns(2)
            cexc={"prod":e71.selectbox("PRODUCTO *",ce7,key="eprod"),
                "min":e71.selectbox("MÍN",oe7,key="emin"),
                "max":e72.selectbox("MÁX",oe7,key="emax"),
                "prom":e72.selectbox("PROM",oe7,key="eprom"),
                "vol":e72.selectbox("VOL",oe7,key="evol")}
        st.divider()
        st.markdown("**Fechas por archivo:**")
        fdm={}
        for f in ams:
            fa=ext_fecha(f.name)
            ic="📄" if f.name.lower().endswith(".pdf") else "📊"
            cn7,cf7=st.columns([3,2])
            cn7.markdown(f"{ic} `{f.name}`")
            fdm[f.name]=cf7.date_input("Fecha" if fa else "⚠️ Fecha",
                value=fa or date.today(),key=f"fd_{f.name}")
        st.divider()
        if st.button("⚡ Importar todos",type="primary",use_container_width=True):
            tok=0; terr=0
            bar=st.progress(0,text="Procesando...")
            for i,f in enumerate(ams):
                fstr=str(fdm[f.name])
                try:
                    if f.name.lower().endswith(".pdf") and cpdf:
                        r=parse_pdf_todas_tablas(f,cpdf["prod"],cpdf["min"],cpdf["max"],cpdf["prom"],cpdf["vol"]); fk="pdf"
                    else:
                        r=parse_excel(f,cexc["prod"],cexc["min"],cexc["max"],cexc["prom"],cexc["vol"]); fk=fk7
                    tok+=guardar_registros(r,fk,fstr)
                except Exception as e:
                    st.warning(f"Error en `{f.name}`: {e}"); terr+=1
                bar.progress((i+1)/len(ams),text=f"Procesando {i+1}/{len(ams)}: {f.name}")
            bar.empty()
            if tok: st.success(f"✅ {tok} registros de {len(ams)} archivos."); df_all=cargar_datos(); st.rerun()
            if terr: st.error(f"⚠️ {terr} archivos con error.")
