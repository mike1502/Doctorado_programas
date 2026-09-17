%% MAPA_MIXCOAC.m
% Mapa detallado de la colonia Mixcoac, Ciudad de México.
%
% NOTA TÉCNICA: este script usa el sistema "axesm-based" de Mapping
% Toolbox (worldmap + geoshow), NO geoaxes/geobasemap. El motivo es que
% geoshow (necesaria para mostrar el raster de topografía) NO es
% compatible con geoaxes -- son dos sistemas de mapas distintos que no
% se pueden mezclar. Con worldmap + geoshow podemos mostrar en el mismo
% mapa: imagen de fondo (basemap), raster de elevación, shapefile de
% alcaldías y puntos de referencia, todo de forma consistente.
%
% Requiere Mapping Toolbox R2022a o superior (por readBasemapImage).
% IMPORTANTE: readBasemapImage descarga la imagen en línea, necesitas
% internet la primera vez (se cachea después).
%
% Autor: (tu nombre)

clear; clc; close all;

%% 1. Límites geográficos de Mixcoac (con margen)
lat_lim = [19.355 19.385];
lon_lim = [-99.205 -99.175];

%% 2. Puntos de referencia dentro de la colonia
puntos = {
    'Metro Mixcoac',            19.3672, -99.1917;
    'Parroquia de Mixcoac',     19.3721, -99.1934;
    'Deportivo Mixcoac',        19.3752, -99.1888;
    'Plaza Mixcoac',            19.3785, -99.1855
};

%% 3. Cargar shapefile de alcaldías (opcional)
shp_alcaldias = 'alcaldias.shp';
if exist(shp_alcaldias, 'file')
    alcaldias = readgeotable(shp_alcaldias);
else
    warning('No se encontró %s. Continuando sin límites de alcaldías.', shp_alcaldias);
    alcaldias = [];
end

%% 4. Cargar datos de topografía (.mat con struct topo.loni/lati/raster)
archivo_topo = 'topo_cdmx.mat';
if exist(archivo_topo, 'file')
    S_topo = load(archivo_topo);
    topo = S_topo.topo;   % desempaquetar la struct anidada
else
    warning('No se encontró %s. Continuando sin capa de topografía.', archivo_topo);
    topo = [];
end

%% 5. Graficar con estilo gris simple (por defecto que pediste)
graficar_mapa_mixcoac('grayland', lat_lim, lon_lim, puntos, alcaldias, topo);
title('Colonia Mixcoac, Ciudad de México', 'FontSize', 13, 'FontWeight', 'bold');

%% 6. Ejemplos para cuando quieras otros estilos de fondo
% Simplemente llama a la misma función con otro nombre de estilo:
%
%   graficar_mapa_mixcoac('satellite',   lat_lim, lon_lim, puntos, alcaldias, topo); % satelital
%   graficar_mapa_mixcoac('streets',     lat_lim, lon_lim, puntos, alcaldias, topo); % calles
%   graficar_mapa_mixcoac('topographic', lat_lim, lon_lim, puntos, alcaldias, topo); % topográfico
%
% Otros estilos válidos: 'streets-light','streets-dark','landcover',
% 'colorterrain','grayterrain','bluegreen','darkwater'


%% ===================== FUNCIONES LOCALES =====================
function graficar_mapa_mixcoac(estilo, lat_lim, lon_lim, puntos, alcaldias, topo)
% GRAFICAR_MAPA_MIXCOAC Dibuja el mapa de Mixcoac: basemap de imagen,
% topografía (opcional), límites de alcaldías (opcional) y puntos.

    if nargin < 5, alcaldias = []; end
    if nargin < 6, topo = [];      end

    figure('Color', 'w', 'Position', [100 100 800 700]);
    worldmap(lat_lim, lon_lim);   % crea ejes axesm-based con proyección adecuada

    % --- Basemap como imagen (equivalente a geobasemap, pero compatible
    % con geoshow) ---
    try
        [A, R] = readBasemapImage(estilo, lat_lim, lon_lim);
        % El basemap viene en Web Mercator (proyectado), pero nuestro mapa
        % usa el sistema geográfico (axesm/geoshow) -> hay que "desproyectar"
        % la cuadrícula de píxeles a lat/lon antes de mostrarla.
        [xGrid, yGrid] = worldGrid(R);
        [latGrid, lonGrid] = projinv(R.ProjectedCRS, xGrid, yGrid);
        geoshow(latGrid, lonGrid, A);
    catch ME
        warning('No se pudo descargar/mostrar el basemap "%s": %s', estilo, ME.message);
    end
    hold on;

    % --- Topografía (raster), encima del basemap ---
    if ~isempty(topo)
        agregar_topografia(topo, lat_lim, lon_lim);
    end

    % --- Límites de alcaldías ---
    if ~isempty(alcaldias)
        agregar_alcaldias(alcaldias, lat_lim, lon_lim);
    end

    % --- Puntos de referencia ---
    for k = 1:size(puntos, 1)
        plotm(puntos{k,2}, puntos{k,3}, 'o', ...
              'MarkerFaceColor', 'r', 'MarkerEdgeColor', 'k', 'MarkerSize', 7);
        textm(puntos{k,2}, puntos{k,3}, ['  ' puntos{k,1}], ...
              'FontSize', 9, 'FontWeight', 'bold', 'Color', 'k');
    end

    gridm on;
    mlabel on; plabel on;
    setm(gca, 'FontSize', 8);
end


function agregar_topografia(topo, lat_lim, lon_lim)
% AGREGAR_TOPOGRAFIA Recorta y dibuja el raster de elevación (campos
% loni, lati, raster) sobre el área [lat_lim, lon_lim] usando geoshow
% (requiere un mapa axesm-based ya creado, p.ej. con worldmap).

    lon = double(topo.loni(:));
    lat = double(topo.lati(:));
    Z_completo = double(topo.raster);

    if isequal(size(Z_completo), [numel(lon), numel(lat)])
        Z_completo = Z_completo';
    elseif ~isequal(size(Z_completo), [numel(lat), numel(lon)])
        error(['Las dimensiones de "raster" (%dx%d) no coinciden con ' ...
               'numel(lati)=%d y numel(loni)=%d.'], ...
               size(Z_completo,1), size(Z_completo,2), numel(lat), numel(lon));
    end

    % Recorte a la zona de interés (con margen) por rendimiento
    margen = 0.005;
    idx_lat = find(lat >= lat_lim(1)-margen & lat <= lat_lim(2)+margen);
    idx_lon = find(lon >= lon_lim(1)-margen & lon <= lon_lim(2)+margen);

    if isempty(idx_lat) || isempty(idx_lon)
        warning('El área solicitada no cae dentro de la cobertura del raster de topografía.');
        return;
    end

    lat_sub = lat(idx_lat);
    lon_sub = lon(idx_lon);
    Z = Z_completo(idx_lat, idx_lon);

    latlim = [min(lat_sub) max(lat_sub)];
    lonlim = [min(lon_sub) max(lon_sub)];
    R = georefcells(latlim, lonlim, size(Z));

    % Si el relieve sale "de cabeza" o espejeado, descomenta:
    % Z = flipud(Z);
    % Z = fliplr(Z);

    h = geoshow(Z, R, 'DisplayType', 'surface');
    h.FaceAlpha = 0.6;   % semitransparente para que se note el basemap debajo

    try
        cmap = demcmap(Z);
        colormap(cmap);
    catch
        colormap('turbo');
    end

    cb = colorbar;
    cb.Label.String = 'Elevación (m)';
end


function agregar_alcaldias(alcaldias, lat_lim, lon_lim)
% AGREGAR_ALCALDIAS Dibuja el contorno de un geotable (leído con
% readgeotable) como LÍNEA sobre un mapa axesm-based, usando geoshow.
%
% Se dibuja como línea (no como polígono relleno) porque así evitamos
% por completo los problemas de topología/orientación de anillos que dan
% error al recortar o proyectar polígonos complejos. El recorte al área
% de interés se hace a mano, reemplazando por NaN los puntos fuera de
% rango (NaN "corta" la línea en geoshow, igual que en plot normal).

    T = geotable2table(alcaldias, ["Latitude" "Longitude"]);
    [lat, lon] = polyjoin(T.Latitude', T.Longitude');

    fprintf(['agregar_alcaldias: rango de datos -> lat [%.4f, %.4f], ' ...
             'lon [%.4f, %.4f] (%d puntos)\n'], ...
            min(lat), max(lat), min(lon), max(lon), numel(lat));

    % Recorte manual: los puntos fuera del área (con margen) se vuelven
    % NaN, lo que corta la línea en vez de intentar cerrarla/rellenarla.
    margen = 0.01;
    fuera = lat < lat_lim(1)-margen | lat > lat_lim(2)+margen | ...
            lon < lon_lim(1)-margen | lon > lon_lim(2)+margen;
    lat(fuera) = NaN;
    lon(fuera) = NaN;

    if all(isnan(lat))
        warning('El límite de alcaldías no pasa por el área solicitada.');
        return;
    end

    geoshow(lat, lon, 'DisplayType', 'line', ...
            'Color', [0.2 0.2 0.2], 'LineWidth', 1.5);

    % Etiqueta (solo si es una sola alcaldía y tiene campo NOMGEO; ajusta
    % el nombre del campo si el tuyo se llama distinto)
    if height(alcaldias) == 1 && any(strcmp(alcaldias.Properties.VariableNames, 'NOMGEO'))
        idx_validos = ~isnan(lat);
        lat_c = mean(lat(idx_validos));
        lon_c = mean(lon(idx_validos));
        textm(lat_c, lon_c, char(alcaldias.NOMGEO(1)), ...
              'FontSize', 8, 'Color', [0.3 0.3 0.3], ...
              'HorizontalAlignment', 'center', 'FontWeight', 'bold');
    end
end

% Para exportar en alta calidad:
% exportgraphics(gcf, 'mapa_mixcoac.png', 'Resolution', 300);