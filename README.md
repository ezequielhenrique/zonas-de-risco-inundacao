# Análise de Risco de Inundação – Municípios de Pernambuco

Este repositório contém um **notebook Jupyter** que realiza a análise de risco de inundação para o municípios de Pernambuco, utilizando dados altimétricos, de uso do solo e outros parâmetros geoespaciais.  
O projeto aplica a **metodologia AHP (Analytic Hierarchy Process)** para atribuição de pesos aos critérios, gera mapas temáticos (declividade, uso do solo, reclassificações) e produz o **Mapa Final de Risco**.

---

## 📂 Estrutura do Repositório

- `analise-risco-alagamento.ipynb` → Código principal com todas as etapas da análise
- `merge_mde.py` -> Gera um modelo de elevação digital único de Pernambuco quando os dados estão baixados. 
- `data/` → Arquivos de entrada (MDE, uso do solo, shapefiles, etc.)
- `outputs/` → Mapas e resultados gerados

---

## 📊 Dados Utilizados

- **Modelo Digital de Elevação (MDE)**:  
  - Fonte: [NASA Earthdata Search](https://search.earthdata.nasa.gov/search/)  
  - Produto: **ASTER Global Digital Elevation Model (GDEM) V003**  
  - Resolução espacial: **30 metros**  

### Baixar o ASTER automaticamente (via Google Earth Engine)

Se você não tiver o arquivo `dados/mde_pernambuco.tif`, há um script para **exportar o ASTER recortado para Pernambuco** usando o Earth Engine.

1) Instale dependências (em um ambiente virtual)

```bash
pip install earthengine-api geemap geopandas shapely
```

2) Autentique o Earth Engine (uma vez)

```bash
earthengine authenticate
```

3) Rode o export para o Google Drive

```bash
python tools/baixar_mde_aster_gee.py --drive-folder "GEE" --prefix "mde_pernambuco_aster" --project "SEU_PROJECT_ID"
```

Se aparecer o erro `ee.Initialize: no project found`, é obrigatório informar `--project`.

Se aparecer erro 403 dizendo que a Earth Engine API "has not been used" ou está "disabled" no projeto, abra o link do erro (ou o Console) e habilite a API `earthengine.googleapis.com` para o seu projeto, aguarde alguns minutos e rode novamente.

Se aparecer erro do tipo `Image asset ... not found`, o dataset escolhido pode não existir/estar acessível na sua conta. O script permite escolher outra fonte via `--dataset`.

Exemplos de datasets comuns no GEE:

```bash
# SRTM (padrão do script)
python tools/baixar_mde_aster_gee.py --project "SEU_PROJECT_ID" --dataset "USGS/SRTMGL1_003" --band "elevation"

# NASADEM
python tools/baixar_mde_aster_gee.py --project "SEU_PROJECT_ID" --dataset "NASA/NASADEM_HGT/001" --band "elevation"

# Copernicus GLO-30
python tools/baixar_mde_aster_gee.py --project "SEU_PROJECT_ID" --dataset "COPERNICUS/DEM/GLO30" --band "DEM"
```

O export será criado como um *task* no GEE. Acompanhe em: https://code.earthengine.google.com/tasks
Depois de concluir, baixe o GeoTIFF do Drive e salve com um nome que identifique a fonte, por exemplo: `dados/mde_pernambuco_srtm.tif`.

- **Mapa de Uso do Solo de Pernambuco**:  
  - Fonte: [MapBiomas](https://brasil.mapbiomas.org/downloads/)  
  - Produto: **Cobertura e Uso da Terra (Coleção 9)**  
  - Resolução espacial: **30 metros**  

Outros dados:

- Limites municipais
- Camadas temáticas derivadas

---

## 🚀 Como Executar o Notebook

### 1️⃣ Pré-requisitos

Certifique-se de ter instalado:

- **Python 3.x**
- **Jupyter Notebook**
- **GRASS GIS** (necessário para execução de algumas etapas de análise raster), link para [dowload](https://grass.osgeo.org/download/)

### 2️⃣ Passos para execução

1. **Clonar o repositório**  

   ```bash
   git clone https://github.com/ezequielhenrique/zonas-de-risco-inundacao.git
   cd zonas-de-risco-inundacao
    ```

2. **Criar e ativar um ambiente virtual (opcional, mas recomendado)**  

   ```bash
   python -m venv venv
   source venv/bin/activate   # Linux/Mac
   venv\Scripts\activate      # Windows
    ```

3. **Instalar as dependências**  

   ```bash
   pip jupyter install rasterio geopandas numpy matplotlib
    ```

4. **Abrir o Jupyter Notebook**  

   ```bash
   jupyter notebook
    ```

5. **Executar as células**

Siga a ordem das células do notebook para gerar todos os mapas intermediários e o Mapa Final de Risco.