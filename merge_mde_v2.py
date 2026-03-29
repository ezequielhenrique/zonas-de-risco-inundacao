import rasterio
from rasterio.merge import merge
import glob
import os
import zipfile
from pathlib import Path

def descompactar_arquivos_zip(pasta_origem):
    """
    Descompacta todos os arquivos ZIP encontrados na pasta de origem.
    """
    print(f"Procurando arquivos ZIP em: {pasta_origem}")
    arquivos_zip = glob.glob(os.path.join(pasta_origem, "*.zip"))
    
    print(f"Encontrados {len(arquivos_zip)} arquivos ZIP")
    
    for arquivo_zip in arquivos_zip:
        nome_sem_extensao = Path(arquivo_zip).stem
        pasta_destino = os.path.join(pasta_origem, nome_sem_extensao)
        
        # Verifica se já foi descompactado
        if os.path.exists(pasta_destino):
            print(f"  Já descompactado: {nome_sem_extensao}")
            continue
        
        print(f"  Descompactando: {nome_sem_extensao}")
        with zipfile.ZipFile(arquivo_zip, 'r') as zip_ref:
            zip_ref.extractall(pasta_destino)
    
    print("Descompactação concluída!\n")

def juntar_arquivos_tif(pasta_origem, arquivo_saida):
    """
    Junta todos os arquivos .tif encontrados na pasta e subpastas.
    """
    print(f"Procurando arquivos TIF em: {pasta_origem}")
    
    # Busca recursivamente por todos os arquivos .tif
    arquivos_tif = glob.glob(os.path.join(pasta_origem, "**", "*.tif"), recursive=True)
    
    if not arquivos_tif:
        print("ERRO: Nenhum arquivo TIF encontrado!")
        return
    
    print(f"Encontrados {len(arquivos_tif)} arquivos TIF")
    
    # Abre todos os rasters
    print("Abrindo rasters...")
    rasters = []
    for arquivo in arquivos_tif:
        try:
            rasters.append(rasterio.open(arquivo))
        except Exception as e:
            print(f"  Erro ao abrir {arquivo}: {e}")
    
    if not rasters:
        print("ERRO: Nenhum raster válido encontrado!")
        return
    
    print(f"Juntando {len(rasters)} rasters...")
    
    # Cria o mosaico
    mosaico, transform = merge(rasters)
    
    # Configura o perfil de saída
    perfil = rasters[0].meta.copy()
    perfil.update({
        "driver": "GTiff",
        "height": mosaico.shape[1],
        "width": mosaico.shape[2],
        "transform": transform,
        "compress": "lzw"  # Compressão para reduzir tamanho do arquivo
    })
    
    # Salva o mosaico
    print(f"Salvando mosaico em: {arquivo_saida}")
    with rasterio.open(arquivo_saida, "w", **perfil) as dst:
        dst.write(mosaico)
    
    # Fecha todos os rasters
    for raster in rasters:
        raster.close()
    
    print(f"\n✓ Mosaico criado com sucesso: {arquivo_saida}")

if __name__ == "__main__":
    pasta_mde = "dados/mde_pernambuco"
    arquivo_saida = "outputs/mde/mde_recife.tif"
    
    # Cria o diretório de saída se não existir
    os.makedirs(os.path.dirname(arquivo_saida), exist_ok=True)
    
    # Etapa 1: Descompactar arquivos ZIP
    descompactar_arquivos_zip(pasta_mde)
    
    # Etapa 2: Juntar arquivos TIF
    juntar_arquivos_tif(pasta_mde, arquivo_saida)
