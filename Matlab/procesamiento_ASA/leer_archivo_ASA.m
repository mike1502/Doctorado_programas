function datos = leer_archivo_ASA(rutaArchivo)
%LEER_ARCHIVO_ASA Lee un archivo ASA versión 2.0
%
% Extrae:
%   - estación
%   - coordenadas
%   - evento
%   - epicentro
%   - magnitud
%   - profundidad
%   - dt
%   - número de muestras
%   - PGA
%   - acelerogramas HLZ, HLN y HLE
%
% La señal se conserva en Gal (cm/s^2).

%% ============================================================
% LEER ARCHIVO COMPLETO
% =============================================================

fid = fopen(rutaArchivo,'r');

if fid == -1
    error('No se pudo abrir el archivo: %s', rutaArchivo);
end

C = textscan(fid,'%s','Delimiter','\n', ...
    'Whitespace','');

fclose(fid);

lineas = C{1};

if isempty(lineas)
    error('El archivo está vacío.');
end


%% ============================================================
% NOMBRE DEL ARCHIVO
% =============================================================

[~,nombreArchivo,extension] = fileparts(rutaArchivo);

datos.Archivo = string([nombreArchivo extension]);


%% ============================================================
% ESTACION
% =============================================================

datos.Estacion = extraerCampo( ...
    lineas, ...
    'NOMBRE DE LA ESTACION');

datos.ClaveEstacion = extraerCampo( ...
    lineas, ...
    'CLAVE DE LA ESTACION');


%% ============================================================
% COORDENADAS DE LA ESTACION
% =============================================================

texto = strjoin(lineas,newline);

pat = ['COORDENADAS DE LA ESTACION' ...
       '[\s\S]{0,300}?([0-9]+\.[0-9]+)\s*LAT\.\s*N' ...
       '[\s\S]{0,100}?([0-9]+\.[0-9]+)\s*LONG\.\s*W'];

tokens = regexp(texto,pat,'tokens','once');

if isempty(tokens)

    datos.LatEstacion = NaN;
    datos.LonEstacion = NaN;

else

    datos.LatEstacion = str2double(tokens{1});
    datos.LonEstacion = -str2double(tokens{2});

end


%% ============================================================
% MODELO
% =============================================================

datos.Modelo = extraerCampo( ...
    lineas, ...
    'MODELO DEL ACELEROGRAFO');


%% ============================================================
% DATOS DEL SISMO
% =============================================================

datos.FechaSismo = extraerCampo( ...
    lineas, ...
    'FECHA DEL SISMO \[GMT\]');

datos.HoraSismo = extraerCampo( ...
    lineas, ...
    'HORA EPICENTRO \(GMT\)');


%% ============================================================
% MAGNITUD
% =============================================================

magnitudTexto = extraerCampo( ...
    lineas, ...
    'MAGNITUD\(ES\)');

tokens = regexp( ...
    magnitudTexto, ...
    'M\s*=\s*([0-9]+\.?[0-9]*)', ...
    'tokens','once');

if isempty(tokens)
    datos.Magnitud = NaN;
else
    datos.Magnitud = str2double(tokens{1});
end


%% ============================================================
% EPICENTRO
% =============================================================

idx = encontrarLinea( ...
    lineas, ...
    'COORDENADAS DEL EPICENTRO');

if idx > 0

    bloque = strjoin( ...
        lineas(idx:min(idx+3,length(lineas))), ...
        ' ');

    tokens = regexp( ...
        bloque, ...
        '([0-9]+\.[0-9]+)\s*LAT\.\s*N.*?' ...
        '([0-9]+\.[0-9]+)\s*LONG\.\s*W', ...
        'tokens','once');

    if ~isempty(tokens)

        datos.LatEpicentro = str2double(tokens{1});
        datos.LonEpicentro = -str2double(tokens{2});

    else

        datos.LatEpicentro = NaN;
        datos.LonEpicentro = NaN;

    end

else

    datos.LatEpicentro = NaN;
    datos.LonEpicentro = NaN;

end


%% ============================================================
% PROFUNDIDAD
% =============================================================

profTexto = extraerCampo( ...
    lineas, ...
    'PROFUNDIDAD FOCAL \(Km\)');

tokens = regexp( ...
    profTexto, ...
    '([-+]?[0-9]+\.?[0-9]*)', ...
    'tokens','once');

if isempty(tokens)
    datos.Profundidad = NaN;
else
    datos.Profundidad = str2double(tokens{1});
end


%% ============================================================
% DT
% =============================================================

dtTexto = extraerCampo( ...
    lineas, ...
    'INTERVALO DE MUESTREO, C1-C6');

tokens = regexp( ...
    dtTexto, ...
    '/\s*([0-9.]+)', ...
    'tokens');

if isempty(tokens)

    datos.Dt = NaN;

else

    datos.Dt = str2double(tokens{1}{1});

end


%% ============================================================
% FRECUENCIA DE MUESTREO
% =============================================================

if ~isnan(datos.Dt)

    datos.Fs = 1/datos.Dt;

else

    datos.Fs = NaN;

end


%% ============================================================
% DURACION
% =============================================================

durTexto = extraerCampo( ...
    lineas, ...
    'DURACION DEL REGISTRO \(s\), C1-C6');

tokens = regexp( ...
    durTexto, ...
    '/\s*([0-9.]+)', ...
    'tokens');

if isempty(tokens)

    datos.Duracion = NaN;

else

    datos.Duracion = str2double(tokens{1}{1});

end


%% ============================================================
% NUMERO DE MUESTRAS
% =============================================================

muestrasTexto = extraerCampo( ...
    lineas, ...
    'NUM\. TOTAL DE MUESTRAS, C1-C6');

tokens = regexp( ...
    muestrasTexto, ...
    '/\s*([0-9]+)', ...
    'tokens');

if isempty(tokens)

    datos.NumMuestras = NaN;

else

    datos.NumMuestras = str2double(tokens{1}{1});

end


%% ============================================================
% PGA
% =============================================================

pgaTexto = extraerCampo( ...
    lineas, ...
    'ACEL\. MAX\.\(Gal\), C1-C6');

tokens = regexp( ...
    pgaTexto, ...
    '/\s*([-+]?[0-9.]+)', ...
    'tokens');

if numel(tokens) >= 3

    datos.PGA_HLZ = abs(str2double(tokens{1}{1}));
    datos.PGA_HLN = abs(str2double(tokens{2}{1}));
    datos.PGA_HLE = abs(str2double(tokens{3}{1}));

else

    datos.PGA_HLZ = NaN;
    datos.PGA_HLN = NaN;
    datos.PGA_HLE = NaN;

end


%% ============================================================
% HORA PRIMERA MUESTRA
% =============================================================

datos.HoraPrimeraMuestra = extraerCampo( ...
    lineas, ...
    'HORA DE LA PRIMERA MUESTRA \(GMT\)');


%% ============================================================
% ARCHIVO SEISAN DE ORIGEN
% =============================================================

idx = encontrarLinea( ...
    lineas, ...
    'Archivo de origen en formato SEISAN');

if idx > 0

    linea = strtrim(lineas{idx});

    pos = strfind( ...
        linea, ...
        'Archivo de origen en formato SEISAN:');

    if ~isempty(pos)

        datos.ArchivoSEISAN = string( ...
            strtrim(linea(pos + ...
            length('Archivo de origen en formato SEISAN:'):end)));

    else

        datos.ArchivoSEISAN = "";

    end

else

    datos.ArchivoSEISAN = "";

end


%% ============================================================
% DATOS DE ACELERACION
% =============================================================

idxDatos = encontrarLinea( ...
    lineas, ...
    'DATOS DE ACELERACION');

if idxDatos == 0

    error('No se encontró la sección DATOS DE ACELERACION.');

end


% Buscar la primera línea numérica después de la cabecera
inicio = 0;

for k = idxDatos+1:length(lineas)

    linea = strtrim(lineas{k});

    numeros = sscanf(linea,'%f');

    if numel(numeros) >= 3

        inicio = k;
        break;

    end

end

if inicio == 0
    error('No se encontraron datos numéricos de aceleración.');
end


%% ============================================================
% LEER ACELERACIONES
% =============================================================

A = [];

for k = inicio:length(lineas)

    linea = strtrim(lineas{k});

    if isempty(linea)
        continue;
    end

    numeros = sscanf(linea,'%f');

    if numel(numeros) >= 3

        A(end+1,1:3) = numeros(1:3).';

    end

end


if isempty(A)

    error('No fue posible extraer los datos de aceleración.');

end


datos.HLZ = A(:,1);
datos.HLN = A(:,2);
datos.HLE = A(:,3);


%% ============================================================
% COMPROBACION DEL NUMERO DE MUESTRAS
% =============================================================

if ~isnan(datos.NumMuestras)

    if size(A,1) ~= datos.NumMuestras

        warning( ...
            'Archivo %s: se esperaban %d muestras y se encontraron %d.', ...
            datos.Archivo, ...
            datos.NumMuestras, ...
            size(A,1));

    end

end


end


%% ================================================================
% FUNCIONES AUXILIARES
% ================================================================

function valor = extraerCampo(lineas,patron)

valor = "";

idx = encontrarLinea(lineas,patron);

if idx == 0
    return;
end

linea = lineas{idx};

partes = regexp( ...
    linea, ...
    [patron '\s*:\s*(.*)$'], ...
    'tokens','once');

if ~isempty(partes)

    valor = string(strtrim(partes{1}));

end

end


function idx = encontrarLinea(lineas,patron)

idx = 0;

for k = 1:length(lineas)

    if ~isempty(regexp( ...
            lineas{k}, ...
            patron, ...
            'once'))

        idx = k;
        return;

    end

end

end