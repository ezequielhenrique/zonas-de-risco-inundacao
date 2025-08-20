# Análise de Risco de Inundação – Municípios de Pernambuco

Este repositório contém um **notebook Jupyter** que realiza a análise de risco de inundação para o municípios de Pernambuco, utilizando dados altimétricos, de uso do solo e outros parâmetros geoespaciais.  
O projeto aplica a **metodologia AHP (Analytic Hierarchy Process)** para atribuição de pesos aos critérios, gera mapas temáticos (declividade, uso do solo, reclassificações) e produz o **Mapa Final de Risco**.

---

## 📂 Estrutura do Repositório

- `analise-risco-alagamento.ipynb` → Código principal com todas as etapas da análise
- `data/` → Arquivos de entrada (MDE, uso do solo, shapefiles, etc.)
- `outputs/` → Mapas e resultados gerados

---

## 📊 Dados Utilizados

- **Modelo Digital de Elevação (MDE)**:  
  - Fonte: [NASA Earthdata Search](https://search.earthdata.nasa.gov/search/)  
  - Produto: **ASTER Global Digital Elevation Model (GDEM) V003**  
  - Resolução espacial: **30 metros**  

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