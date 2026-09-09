%% MAPA_MEXICO_AVANZADO.m
% Mapa de México con relieve/batimetría (TerrainBase) y fronteras estatales
% (shapefile del INEGI). Requiere:
%   1) GSHHS instalado en m_map/private  -> https://www.eoas.ubc.ca/~rich/map.html
%   2) TerrainBase instalado en m_map/private (mismo link, secc. 9-10.1)
%   3) Shapefile de estados del Marco Geoestadístico Nacional (INEGI)
%      -> https://www.inegi.org.mx/app/mapas/  (descarga "Entidades federativas")
%
% Si aún no tienes 1) y 2), comenta esas secciones y usa m_coast en su lugar
% (ver mapa_mexico_basico.m).
%
% Autor: (tu nombre)

clear; clc; close all;

%% 1. Proyección
lon_lim = [-118 -86];
lat_lim = [ 14  33];
m_proj('lambert', 'long', lon_lim, 'lat', lat_lim);

figure('Color','w','Position',[100 100 850 700]);

%% 2. Relieve/batimetría (requiere TerrainBase instalado)
try
    [ELEV, LON, LAT] = m_tbase([lon_lim lat_lim]);
    m_pcolor(LON, LAT, ELEV); shading interp; hold on;

    % Colormap tierra/mar (usa cmocean('topo') si lo tienes instalado,
    % si no, un colormap simple funciona bien):
    colormap([m_colmap('blues',64); m_colmap('gland',64)]);
    caxis([-6000 4000]);
    cb = colorbar('southoutside');
    xlabel(cb,'Elevación / Profundidad (m)');
catch
    warning('TerrainBase no está instalado. Usando m_coast como respaldo.');
    m_coast('patch',[0.85 0.85 0.75],'edgecolor','k'); hold on;
end

%% 3. Costa de alta resolución (requiere GSHHS instalado)
try
    m_gshhs_i('color','k','linewidth',0.5); % 'i' = intermedia
catch
    warning('GSHHS no está instalado. La costa usará la resolución por defecto.');
end

%% 4. Fronteras estatales (shapefile INEGI)
shp_path = 'shapefiles/00ent.shp';  % <-- ajusta a la ruta de tu shapefile
if exist(shp_path, 'file')
    m_shaperead(shp_path); % dibuja automáticamente los polígonos
else
    warning('No se encontró el shapefile de estados en: %s', shp_path);
end

%% 5. Cuadrícula
m_grid('box','fancy','tickdir','in','fontsize',9,...
    'xtick',(-118:4:-86), 'ytick',(14:2:33));

title('México — relieve, batimetría y límites estatales', ...
    'FontSize', 13, 'FontWeight','bold');

% Para exportar en alta calidad:
% print('-dpng','-r300','mapa_mexico_avanzado.png');