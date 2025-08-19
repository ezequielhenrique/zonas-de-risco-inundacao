import rasterio
from rasterio.merge import merge
import glob
import os

pasta = "dados/mde_pe"
arquivos = glob.glob(os.path.join(pasta, "*.tif"))

rasters = [rasterio.open(arq) for arq in arquivos]

mosaico, transform = merge(rasters)

perfil = rasters[0].meta.copy()
perfil.update({
    "driver": "GTiff",
    "height": mosaico.shape[1],
    "width": mosaico.shape[2],
    "transform": transform
})

saida = "dados/mde_pernambuco.tif"

with rasterio.open(saida, "w", **perfil) as dst:
    dst.write(mosaico)
