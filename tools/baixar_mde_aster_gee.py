#!/usr/bin/env python3
"""Exporta MDE ASTER (GEE) recortado para Pernambuco.

Motivação
- Evitar depender de um tif local já pronto.
- Reproduzir o fluxo que o aluno fez no Google Earth Engine (GEE), mas via script.

Como funciona
- Lê o shapefile de municípios de PE (IBGE) e dissolve para obter o contorno do estado.
- Converte o contorno para WGS84 e usa como `region` no Earth Engine.
- Exporta para o Google Drive (recomendado para áreas grandes como um estado).

Requisitos
- Conta e projeto no Google Earth Engine
- `earthengine-api`, `geemap`, `geopandas`, `shapely`

Instalação típica (em um venv):
  pip install earthengine-api geemap geopandas shapely

Autenticação (uma vez):
  earthengine authenticate

Execução:
    python tools/baixar_mde_aster_gee.py --drive-folder "GEE" --prefix "mde_pernambuco_aster" --project "SEU_PROJECT_ID"

Obs.
- O arquivo será exportado para o Drive; após finalizar o task, baixe manualmente do Drive.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _load_pernambuco_region_geojson(
    municipios_shp: Path,
    nome_coluna_uf: str = "SIGLA_UF",
    uf: str = "PE",
) -> dict[str, Any]:
    """Cria um GeoJSON (Polygon/MultiPolygon) do estado a partir de municípios."""
    import geopandas as gpd

    gdf = gpd.read_file(municipios_shp)

    # Tenta filtrar PE se existir a coluna.
    if nome_coluna_uf in gdf.columns:
        gdf = gdf[gdf[nome_coluna_uf] == uf]

    if gdf.empty:
        raise ValueError(
            f"Shapefile não contém feições após filtro {nome_coluna_uf}={uf}. "
            "Verifique o shapefile/colunas."
        )

    # Dissolve para obter contorno do estado.
    # GeoPandas >= 0.14: unary_union foi depreciado.
    try:
        geom = gdf.geometry.union_all()
    except Exception:
        geom = gdf.geometry.unary_union

    # GEE espera lon/lat.
    gdf_state = gpd.GeoDataFrame({"name": [uf]}, geometry=[geom], crs=gdf.crs)
    gdf_state = gdf_state.to_crs("EPSG:4326")

    geom4326 = gdf_state.geometry.iloc[0]
    mapping = json.loads(gdf_state.geometry.to_json())
    # mapping é um FeatureCollection; extrair geometry
    geom_geojson = mapping["features"][0]["geometry"]

    # sanity check
    if geom_geojson.get("type") not in {"Polygon", "MultiPolygon"}:
        raise ValueError(f"Geometria inesperada: {geom_geojson.get('type')}")

    # Garante que não está vazio
    if geom4326.is_empty:
        raise ValueError("Geometria do estado ficou vazia após dissolve.")

    return geom_geojson


def _ensure_ee_initialized(project: str | None):
    import ee

    try:
        if project:
            ee.Initialize(project=project)
        else:
            ee.Initialize()
    except Exception as e:
        msg = str(e)
        low = msg.lower()

        # Caso 1: API do Earth Engine não habilitada no projeto
        if (
            "earth engine api has not been used" in low
            or "service_disabled" in low
            or "earthengine.googleapis.com" in low
            or "enable it" in low
        ):
            proj = project or "SEU_PROJECT_ID"
            url = f"https://console.developers.google.com/apis/api/earthengine.googleapis.com/overview?project={proj}"
            raise RuntimeError(
                "O projeto informado existe, mas a API `earthengine.googleapis.com` está desabilitada (ou nunca foi usada) nele.\n\n"
                "Como resolver:\n"
                f"1) Abra: {url}\n"
                "2) Clique em 'Enable' (Ativar)\n"
                "3) Aguarde 1–5 minutos e rode o script novamente\n\n"
                f"Erro original: {msg}"
            )

        # Caso 2: nenhum project default encontrado
        if "no project found" in low:
            raise RuntimeError(
                "Falha ao inicializar o Earth Engine: nenhum project foi encontrado. "
                "Isso acontece mesmo após `earthengine authenticate` quando a conta não tem um projeto padrão. "
                "Rode novamente informando explicitamente o project id, por exemplo: \n"
                "  python tools/baixar_mde_aster_gee.py --project SEU_PROJECT_ID\n\n"
                "Dicas para descobrir o project id:\n"
                "- Pelo Console do Google Cloud (seletor de projeto no topo)\n"
                "- Ou use o projeto associado ao seu Earth Engine\n\n"
                f"Erro original: {msg}"
            )

        raise RuntimeError(
            "Não consegui inicializar o Earth Engine. Rode antes: `earthengine authenticate` "
            "(e garanta que sua conta tem acesso ao GEE). Erro original: "
            + msg
        )


def _load_gee_image(dataset: str, band: str | None):
    """Carrega um dataset do GEE como ee.Image.

    Alguns datasets são `ee.Image` e outros são `ee.ImageCollection`.
    Este helper tenta ambos e retorna uma imagem pronta para export.
    """
    import ee

    last_err: Exception | None = None

    # 1) Tentar como Image
    try:
        img = ee.Image(dataset)
        if band:
            img = img.select(band)
        return img
    except Exception as e:
        last_err = e

    # 2) Tentar como ImageCollection (mosaic para obter uma única imagem)
    try:
        ic = ee.ImageCollection(dataset)
        if band:
            ic = ic.select(band)
        return ic.mosaic()
    except Exception as e:
        last_err = e

    # 3) Falhou: orientar alternativas
    msg = str(last_err) if last_err else "(erro desconhecido)"
    raise RuntimeError(
        "Não consegui carregar o dataset no Earth Engine. Ele pode ter sido removido/renomeado ou você não tem acesso.\n\n"
        f"Dataset informado: {dataset}\n"
        f"Band: {band}\n\n"
        "Alternativas comuns (30m-ish) que normalmente funcionam no GEE:\n"
        "- `USGS/SRTMGL1_003` (banda: elevation)\n"
        "- `NASA/NASADEM_HGT/001` (banda: elevation)\n"
        "- `COPERNICUS/DEM/GLO30` (banda: DEM)\n\n"
        "Exemplos:\n"
        "  python tools/baixar_mde_aster_gee.py --project SEU_PROJECT_ID --dataset USGS/SRTMGL1_003 --band elevation\n"
        "  python tools/baixar_mde_aster_gee.py --project SEU_PROJECT_ID --dataset NASA/NASADEM_HGT/001 --band elevation\n"
        "  python tools/baixar_mde_aster_gee.py --project SEU_PROJECT_ID --dataset COPERNICUS/DEM/GLO30 --band DEM\n\n"
        f"Erro original: {msg}"
    )


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Exporta ASTER do GEE recortado para Pernambuco (Drive).")
    parser.add_argument(
        "--municipios-shp",
        type=Path,
        default=repo_root / "dados/PE_Municipios_2023/PE_Municipios_2023.shp",
        help="Shapefile de municípios (usado para dissolver e formar o contorno do estado)",
    )
    parser.add_argument(
        "--uf",
        type=str,
        default="PE",
        help="Sigla da UF a dissolver (default: PE)",
    )
    parser.add_argument(
        "--nome-coluna-uf",
        type=str,
        default="SIGLA_UF",
        help="Nome da coluna com a sigla da UF (default: SIGLA_UF). Se não existir, não filtra.",
    )
    parser.add_argument(
        "--project",
        type=str,
        default=None,
        help=(
            "Google Cloud project id para o Earth Engine. Necessário em algumas contas (erro 'no project found'). "
            "Ex: --project meu-projeto-123"
        ),
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default="USGS/SRTMGL1_003",
        help=(
            "Asset ID do dataset no GEE (default: USGS/SRTMGL1_003). "
            "Obs.: alguns assets do ASTER podem não estar mais disponíveis no seu ambiente." 
        ),
    )
    parser.add_argument(
        "--band",
        type=str,
        default="elevation",
        help="Nome da banda a exportar (default: elevation)",
    )
    parser.add_argument(
        "--scale",
        type=float,
        default=30,
        help="Resolução alvo em metros (default: 30)",
    )
    parser.add_argument(
        "--crs",
        type=str,
        default="EPSG:4326",
        help="CRS da exportação (default: EPSG:4326). Você pode usar EPSG:31984/31985 se preferir.",
    )
    parser.add_argument(
        "--drive-folder",
        type=str,
        default="GEE",
        help="Pasta do Google Drive para exportação (default: GEE)",
    )
    parser.add_argument(
        "--prefix",
        type=str,
        default="mde_pernambuco_aster",
        help="Prefixo do nome do arquivo no Drive (default: mde_pernambuco_aster)",
    )
    parser.add_argument(
        "--max-pixels",
        type=float,
        default=1e13,
        help="maxPixels do GEE (default: 1e13)",
    )

    args = parser.parse_args()

    # Permite executar a partir de qualquer CWD: se vier relativo, resolve na raiz do repo.
    municipios_shp = args.municipios_shp
    if not municipios_shp.is_absolute():
        municipios_shp = (repo_root / municipios_shp).resolve()
    args.municipios_shp = municipios_shp

    if not args.municipios_shp.exists():
        raise FileNotFoundError(f"Não encontrei: {args.municipios_shp}")

    region_geojson = _load_pernambuco_region_geojson(
        municipios_shp=args.municipios_shp,
        nome_coluna_uf=args.nome_coluna_uf,
        uf=args.uf,
    )

    _ensure_ee_initialized(args.project)

    import ee
    import geemap

    # Carregar dataset como imagem (Image ou ImageCollection)
    img = _load_gee_image(args.dataset, args.band)

    # Define region
    region = ee.Geometry(region_geojson)

    desc = f"{args.prefix}_{args.uf}".replace("/", "_")

    print("Iniciando exportação para o Google Drive...")
    print(f"  dataset: {args.dataset}")
    print(f"  band:    {args.band}")
    print(f"  scale:   {args.scale} m")
    print(f"  crs:     {args.crs}")
    print(f"  folder:  {args.drive_folder}")
    print(f"  prefix:  {args.prefix}")

    task = geemap.ee_export_image_to_drive(
        image=img,
        description=desc,
        folder=args.drive_folder,
        fileNamePrefix=args.prefix,
        region=region,
        scale=args.scale,
        crs=args.crs,
        maxPixels=args.max_pixels,
        fileFormat="GeoTIFF",
    )

    # A API do geemap já inicia o task; mas retornamos o task para status.
    print("\nTask criado no Earth Engine.")
    print("Acompanhe em: https://code.earthengine.google.com/tasks")

    # Tentar imprimir status imediatamente
    try:
        status = task.status()
        print("\nStatus inicial:")
        for k in ("state", "description", "creation_timestamp_ms"):
            if k in status:
                print(f"  {k}: {status[k]}")
    except Exception:
        pass

    print("\nQuando terminar, baixe o GeoTIFF do Google Drive e salve como, por exemplo:")
    if str(args.dataset).strip() == "USGS/SRTMGL1_003":
        print("  dados/mde_pernambuco_srtm.tif  (ou use direto no webapp/zonas)")
    else:
        print("  dados/mde_pernambuco.tif  (ou renomeie para identificar a fonte: mde_pernambuco_<fonte>.tif)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
