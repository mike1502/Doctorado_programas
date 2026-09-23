%% REVISION DE UN EVENTO ASA
% Revisión individual de todos los registros de una carpeta ASA
%
% El programa:
%   1. Lee todos los archivos ASA
%   2. Extrae metadatos
%   3. Verifica consistencia del evento y epicentro
%   4. Calcula distancia estación-epicentro
%   5. Grafica los acelerogramas
%   6. Genera mapa de estaciones y epicentro
%   7. Guarda tablas y figuras de revisión
%
% No modifica los archivos originales.

clear;
close all;
clc;

%% ============================================================
% 1. RUTA DE LA CARPETA ASA
% =============================================================

rutaASA = fullfile( ...
    getenv('USERPROFILE'), ...
    'Documents', ...
    'Doctorado', ...
    'FallaFinita_Registros', ...
    'base_datos', ...
    '2023_12_03_0029_02_M2_CDMX', ...
    'ACEL', ...
    'ASA');
% ------------------------------------------------------------
% Verificar que exista
% ------------------------------------------------------------

if ~isfolder(rutaASA)
    error('No se encontró la carpeta ASA:\n%s', rutaASA);
end

fprintf('\n============================================\n');
fprintf(' REVISION DE EVENTO ASA\n');
fprintf('============================================\n');
fprintf('Carpeta:\n%s\n\n', rutaASA);


%% ============================================================
% 2. CARPETA DE RESULTADOS
% =============================================================

carpetaEvento = fileparts(fileparts(rutaASA));
nombreEvento = string( ...
    extractAfter(string(carpetaEvento), ...
    strlength(string(fileparts(fileparts(carpetaEvento))))) );

% Más sencillo y robusto:
[~, nombreEvento] = fileparts(fileparts(fileparts(rutaASA)));

carpetaResultados = fullfile(carpetaEvento, 'revision');

if ~isfolder(carpetaResultados)
    mkdir(carpetaResultados);
end

carpetaGraficas = fullfile(carpetaResultados, 'registros');

if ~isfolder(carpetaGraficas)
    mkdir(carpetaGraficas);
end


%% ============================================================
% 3. BUSCAR ARCHIVOS
% =============================================================

archivos = dir(rutaASA);

% Eliminar carpetas
archivos = archivos(~[archivos.isdir]);

if isempty(archivos)
    error('No se encontraron archivos en la carpeta ASA.');
end

fprintf('Archivos encontrados: %d\n\n', numel(archivos));


%% ============================================================
% 4. LEER TODOS LOS ARCHIVOS
% =============================================================

registros = struct([]);
nValidos = 0;

for k = 1:numel(archivos)

    nombreArchivo = archivos(k).name;
    rutaArchivo = fullfile(archivos(k).folder, nombreArchivo);

    fprintf('[%3d/%3d] Leyendo: %s\n', ...
        k, numel(archivos), nombreArchivo);

    try

        datos = leer_archivo_ASA(rutaArchivo);

        nValidos = nValidos + 1;
        registros(nValidos) = datos;

    catch ME

        fprintf('       ERROR: %s\n', ME.message);

    end

end

fprintf('\n============================================\n');
fprintf('Archivos leídos correctamente: %d/%d\n', ...
    nValidos, numel(archivos));
fprintf('============================================\n\n');


if isempty(registros)
    error('No fue posible leer ningún archivo ASA.');
end


%% ============================================================
% 5. CONSTRUIR TABLA DE REGISTROS
% =============================================================

N = numel(registros);

Archivo          = strings(N,1);
Estacion         = strings(N,1);
ClaveEstacion    = strings(N,1);

FechaSismo       = strings(N,1);
HoraSismo        = strings(N,1);

Magnitud         = nan(N,1);

LatEstacion      = nan(N,1);
LonEstacion      = nan(N,1);

LatEpicentro     = nan(N,1);
LonEpicentro     = nan(N,1);

Profundidad      = nan(N,1);

Modelo            = strings(N,1);

Dt               = nan(N,1);
Fs               = nan(N,1);

Duracion         = nan(N,1);
NumMuestras      = nan(N,1);

PGA_HLZ          = nan(N,1);
PGA_HLN          = nan(N,1);
PGA_HLE          = nan(N,1);

HoraPrimeraMuestra = strings(N,1);

ArchivoSEISAN    = strings(N,1);

for k = 1:N

    Archivo(k)       = registros(k).Archivo;
    Estacion(k)      = registros(k).Estacion;
    ClaveEstacion(k) = registros(k).ClaveEstacion;

    FechaSismo(k)    = registros(k).FechaSismo;
    HoraSismo(k)     = registros(k).HoraSismo;

    Magnitud(k)      = registros(k).Magnitud;

    LatEstacion(k)   = registros(k).LatEstacion;
    LonEstacion(k)   = registros(k).LonEstacion;

    LatEpicentro(k)  = registros(k).LatEpicentro;
    LonEpicentro(k)  = registros(k).LonEpicentro;

    Profundidad(k)   = registros(k).Profundidad;

    Modelo(k)        = registros(k).Modelo;

    Dt(k)            = registros(k).Dt;
    Fs(k)            = registros(k).Fs;

    Duracion(k)      = registros(k).Duracion;
    NumMuestras(k)   = registros(k).NumMuestras;

    PGA_HLZ(k)       = registros(k).PGA_HLZ;
    PGA_HLN(k)       = registros(k).PGA_HLN;
    PGA_HLE(k)       = registros(k).PGA_HLE;

    HoraPrimeraMuestra(k) = registros(k).HoraPrimeraMuestra;

    ArchivoSEISAN(k) = registros(k).ArchivoSEISAN;

end


%% ============================================================
% 6. DISTANCIA ESTACION - EPICENTRO
% =============================================================

% Radio aproximado de la Tierra
R = 6371.0; % km

lat1 = deg2rad(LatEpicentro);
lon1 = deg2rad(LonEpicentro);

lat2 = deg2rad(LatEstacion);
lon2 = deg2rad(LonEstacion);

dlat = lat2 - lat1;
dlon = lon2 - lon1;

a = sin(dlat/2).^2 + ...
    cos(lat1).*cos(lat2).*sin(dlon/2).^2;

c = 2*atan2(sqrt(a),sqrt(1-a));

DistanciaEpicentro_km = R*c;


%% ============================================================
% 7. TABLA FINAL
% =============================================================

TablaRegistros = table( ...
    Archivo, ...
    Estacion, ...
    ClaveEstacion, ...
    FechaSismo, ...
    HoraSismo, ...
    Magnitud, ...
    LatEstacion, ...
    LonEstacion, ...
    LatEpicentro, ...
    LonEpicentro, ...
    Profundidad, ...
    DistanciaEpicentro_km, ...
    Modelo, ...
    Dt, ...
    Fs, ...
    Duracion, ...
    NumMuestras, ...
    PGA_HLZ, ...
    PGA_HLN, ...
    PGA_HLE, ...
    HoraPrimeraMuestra, ...
    ArchivoSEISAN);


%% ============================================================
% 8. MOSTRAR TABLA
% =============================================================

fprintf('\nRESUMEN DE REGISTROS\n');
disp(TablaRegistros);


%% ============================================================
% 9. VERIFICAR CONSISTENCIA DEL EVENTO
% =============================================================

fprintf('\n============================================\n');
fprintf(' VALIDACION DEL EVENTO\n');
fprintf('============================================\n');

% Fechas
fechasUnicas = unique(FechaSismo);

fprintf('Fechas encontradas: %d\n', numel(fechasUnicas));

for k = 1:numel(fechasUnicas)
    fprintf('   %s\n', fechasUnicas(k));
end


% Horas
horasUnicas = unique(HoraSismo);

fprintf('\nHoras epicentrales encontradas: %d\n', ...
    numel(horasUnicas));

for k = 1:numel(horasUnicas)
    fprintf('   %s\n', horasUnicas(k));
end


% Magnitudes
magnitudesUnicas = unique(Magnitud);

fprintf('\nMagnitudes encontradas:\n');
disp(magnitudesUnicas);


% Epicentros
epicentros = unique( ...
    [LatEpicentro LonEpicentro], ...
    'rows');

fprintf('Epicentros diferentes encontrados: %d\n', ...
    size(epicentros,1));

for k = 1:size(epicentros,1)

    fprintf('   %.6f N, %.6f W\n', ...
        epicentros(k,1), ...
        epicentros(k,2));

end


% Profundidades
profundidades = unique(Profundidad);

fprintf('\nProfundidades encontradas:\n');
disp(profundidades);


%% ============================================================
% 10. ESTACIONES ÚNICAS
% =============================================================

[~,idxEstaciones] = unique(ClaveEstacion);

TablaEstaciones = TablaRegistros(idxEstaciones,:);

TablaEstaciones = sortrows( ...
    TablaEstaciones, ...
    'DistanciaEpicentro_km');


fprintf('\n============================================\n');
fprintf(' ESTACIONES\n');
fprintf('============================================\n');

disp(TablaEstaciones(:, { ...
    'ClaveEstacion', ...
    'Estacion', ...
    'LatEstacion', ...
    'LonEstacion', ...
    'DistanciaEpicentro_km'}));


%% ============================================================
% 11. GUARDAR TABLAS
% =============================================================

writetable( ...
    TablaRegistros, ...
    fullfile(carpetaResultados, ...
    'resumen_registros.csv'));

writetable( ...
    TablaEstaciones, ...
    fullfile(carpetaResultados, ...
    'estaciones_evento.csv'));


%% ============================================================
% 12. MAPA
% =============================================================

figure('Color','w');

hold on;
grid on;
box on;

% Estaciones
scatter( ...
    LonEstacion, ...
    LatEstacion, ...
    70, ...
    'filled');

% Epicentro
scatter( ...
    LonEpicentro(1), ...
    LatEpicentro(1), ...
    140, ...
    'p', ...
    'filled');

% Etiquetas
for k = 1:N

    text( ...
        LonEstacion(k) + 0.005, ...
        LatEstacion(k), ...
        ClaveEstacion(k), ...
        'FontSize',8);

end

xlabel('Longitud');
ylabel('Latitud');

title(sprintf( ...
    'Evento %s: estaciones y epicentro', ...
    nombreEvento), ...
    'Interpreter','none');

legend( ...
    'Estaciones', ...
    'Epicentro', ...
    'Location','best');

axis equal;

% Guardar
saveas( ...
    gcf, ...
    fullfile(carpetaResultados, ...
    'mapa_evento.png'));


%% ============================================================
% 13. GRAFICAR TODOS LOS REGISTROS
% =============================================================

fprintf('\nGenerando gráficas de acelerogramas...\n');

for k = 1:N

    datos = registros(k);

    figure( ...
        'Color','w', ...
        'Visible','off');

    t = (0:length(datos.HLZ)-1) * datos.Dt;

    subplot(3,1,1)

    plot(t, datos.HLZ, 'k');
    grid on;
    ylabel('HLZ (Gal)');
    title(sprintf('%s - %s', ...
        datos.ClaveEstacion, ...
        datos.Archivo), ...
        'Interpreter','none');


    subplot(3,1,2)

    plot(t, datos.HLN, 'k');
    grid on;
    ylabel('HLN (Gal)');


    subplot(3,1,3)

    plot(t, datos.HLE, 'k');
    grid on;
    ylabel('HLE (Gal)');
    xlabel('Tiempo (s)');


    sgtitle(sprintf( ...
        '%s | Distancia = %.2f km | PGA = %.4f Gal', ...
        datos.Estacion, ...
        DistanciaEpicentro_km(k), ...
        max(abs([ ...
        datos.PGA_HLZ ...
        datos.PGA_HLN ...
        datos.PGA_HLE]))));


    nombreFigura = sprintf( ...
        '%s.png', ...
        datos.Archivo);

    saveas( ...
        gcf, ...
        fullfile(carpetaGraficas,nombreFigura));

    close;

end


%% ============================================================
% 14. GUARDAR INFORMACION MATLAB
% =============================================================

save( ...
    fullfile(carpetaResultados, ...
    'revision_evento.mat'), ...
    'registros', ...
    'TablaRegistros', ...
    'TablaEstaciones');


fprintf('\n============================================\n');
fprintf(' REVISION TERMINADA\n');
fprintf('============================================\n');

fprintf('Resultados guardados en:\n%s\n\n', ...
    carpetaResultados);

fprintf('Archivos generados:\n');
fprintf('  - resumen_registros.csv\n');
fprintf('  - estaciones_evento.csv\n');
fprintf('  - mapa_evento.png\n');
fprintf('  - revision_evento.mat\n');
fprintf('  - registros/*.png\n\n');