function datos = leerASA(archivo)
%LEERASA Extrae metadatos de un archivo ASA v2.0
%
%   datos = leerASA(archivo)
%
%   Archivo Estandar de Aceleracion
%   Instituto de Ingenieria, UNAM

%% ================================================================
% 1. Leer archivo
% ================================================================

texto = fileread(archivo);

[~, nombreArchivo, extension] = fileparts(archivo);

datos.NombreArchivo = string(nombreArchivo + extension);
datos.Ruta = string(archivo);


%% ================================================================
% 2. INFORMACION DEL ARCHIVO
% ================================================================

datos.VersionFormato = obtenerCampo(texto, ...
    'VERSION DEL FORMATO');

datos.FechaCreacion = obtenerCampo(texto, ...
    'FECHA Y HORA DE CREACION');

datos.NombreArchivoASA = obtenerCampo(texto, ...
    'NOMBRE DEL ARCHIVO');


%% ================================================================
% 3. DATOS DE LA ESTACION
% ================================================================

datos.Estacion = obtenerCampo(texto, ...
    'NOMBRE DE LA ESTACION');

datos.ClaveEstacion = obtenerCampo(texto, ...
    'CLAVE DE LA ESTACION');

datos.LatitudEstacion = obtenerCoordenada(texto, ...
    'COORDENADAS DE LA ESTACION', 'LAT');

datos.LongitudEstacion = obtenerCoordenada(texto, ...
    'COORDENADAS DE LA ESTACION', 'LONG');

datos.Altitud = obtenerNumero(texto, ...
    'ALTITUD \(msnm\)');

datos.TipoSuelo = obtenerCampo(texto, ...
    'TIPO DE SUELO');

datos.Institucion = obtenerCampo(texto, ...
    'INSTITUCION RESPONSABLE');


%% ================================================================
% 4. DATOS DEL ACELEROGRAFO
% ================================================================

datos.ModeloAcelerografo = obtenerCampo(texto, ...
    'MODELO DEL ACELEROGRAFO');

datos.NumeroSerie = obtenerCampo(texto, ...
    'NUMERO DE SERIE DEL ACELEROGRAFO');

datos.NumeroCanales = obtenerNumero(texto, ...
    'NUMERO DE CANALES');

datos.Orientacion = obtenerLista(texto, ...
    'ORIENTACION C1-C6');

datos.VelMuestreo = obtenerListaNumerica(texto, ...
    'VEL. DE MUESTREO, C1-C6');

datos.Dt = obtenerListaNumerica(texto, ...
    'INTERVALO DE MUESTREO, C1-C6');


%% ================================================================
% 5. DATOS DEL SISMO
% ================================================================

datos.FechaSismo = obtenerCampo(texto, ...
    'FECHA DEL SISMO \[GMT\]');

datos.HoraSismo = obtenerCampo(texto, ...
    'HORA EPICENTRO \(GMT\)');

datos.Magnitud = obtenerMagnitud(texto);

datos.LatitudEpicentro = obtenerCoordenada(texto, ...
    'COORDENADAS DEL EPICENTRO', 'LAT');

datos.LongitudEpicentro = obtenerCoordenada(texto, ...
    'COORDENADAS DEL EPICENTRO', 'LONG');

datos.Profundidad = obtenerNumero(texto, ...
    'PROFUNDIDAD FOCAL \(Km\)');

datos.FuenteEpicentro = obtenerCampo(texto, ...
    'FUENTE DE LOS DATOS EPICENTRALES');


%% ================================================================
% 6. DATOS DEL REGISTRO
% ================================================================

datos.HoraPrimeraMuestra = obtenerCampo(texto, ...
    'HORA DE LA PRIMERA MUESTRA \(GMT\)');

datos.Duracion = obtenerListaNumerica(texto, ...
    'DURACION DEL REGISTRO \(s\), C1-C6');

datos.NumMuestras = obtenerListaNumerica(texto, ...
    'NUM. TOTAL DE MUESTRAS, C1-C6');

datos.PGA = obtenerListaNumerica(texto, ...
    'ACEL. MAX.\(Gal\), C1-C6');

datos.MuestraPGA = obtenerListaNumerica(texto, ...
    'ACEL. MAX\. C1-C6, EN LA MUESTRA');

datos.Unidades = obtenerCampo(texto, ...
    'UNIDADES DE LOS DATOS');

datos.FactorDecimacion = obtenerNumero(texto, ...
    'FACTOR DE DECIMACION');

datos.FormatoDatos = obtenerCampo(texto, ...
    'FORMATO DATOS');


%% ================================================================
% 7. COMENTARIOS
% ================================================================

datos.ArchivoOrigen = obtenerComentarioSEISAN(texto);


%% ================================================================
% 8. INFORMACION DERIVADA
% ================================================================

% Frecuencia de muestreo
datos.Fs = NaN;

if ~isempty(datos.VelMuestreo)

    if ~isnan(datos.VelMuestreo(1))
        datos.Fs = datos.VelMuestreo(1);
    end

end


% Identificador del evento
datos.ID_Evento = "";

if strlength(datos.FechaSismo) > 0 && ...
        strlength(datos.HoraSismo) > 0

    fecha = replace(datos.FechaSismo, "/", "");
    hora  = replace(datos.HoraSismo, ":", "");

    datos.ID_Evento = fecha + "_" + hora;

end

end


%% =================================================================
% FUNCIONES AUXILIARES
% =================================================================

function valor = obtenerCampo(texto, etiqueta)

patron = [etiqueta '\s*:\s*([^\r\n]*)'];

token = regexp(texto, patron, 'tokens', 'once');

if isempty(token)
    valor = "";
else
    valor = string(strtrim(token{1}));
end

end


function valor = obtenerNumero(texto, etiqueta)

cadena = obtenerCampo(texto, etiqueta);

if strlength(cadena) == 0
    valor = NaN;
    return
end

token = regexp(char(cadena), ...
    '[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?', ...
    'match', 'once');

if isempty(token)
    valor = NaN;
else
    valor = str2double(token);
end

end


function valor = obtenerLista(texto, etiqueta)

cadena = obtenerCampo(texto, etiqueta);

if strlength(cadena) == 0
    valor = strings(1,0);
    return
end

partes = split(cadena, '/');
partes = strtrim(partes);

partes(partes == "") = [];

valor = partes';

end


function valor = obtenerListaNumerica(texto, etiqueta)

lista = obtenerLista(texto, etiqueta);

valor = NaN(1,length(lista));

for k = 1:length(lista)

    valor(k) = str2double(lista(k));

end

end


function valor = obtenerMagnitud(texto)

cadena = obtenerCampo(texto, 'MAGNITUD\(ES\)');

valor = NaN;

if strlength(cadena) == 0
    return
end

token = regexp(char(cadena), ...
    'M\s*=\s*([-+]?\d*\.?\d+)', ...
    'tokens', 'once');

if ~isempty(token)
    valor = str2double(token{1});
end

end


function valor = obtenerCoordenada(texto, etiqueta, tipo)

% Obtener bloque de texto alrededor de la etiqueta
posicion = regexp(texto, etiqueta, 'once');

valor = NaN;

if isempty(posicion)
    return
end

% Tomamos varias líneas posteriores
bloque = texto(posicion:min(length(texto), posicion + 500));


if strcmpi(tipo,'LAT')

    patron = '([-+]?\d*\.?\d+)\s*LAT\.\s*([NS])';

else

    patron = '([-+]?\d*\.?\d+)\s*LONG\.\s*([EW])';

end

token = regexp(bloque, patron, 'tokens', 'once');

if isempty(token)
    return
end

valor = str2double(token{1});

direccion = upper(token{2});

if strcmp(direccion,'S') || strcmp(direccion,'W')
    valor = -abs(valor);
end

end


function valor = obtenerComentarioSEISAN(texto)

patron = ...
    'Archivo de origen en formato SEISAN\s*:\s*([^\r\n]*)';

token = regexp(texto, patron, 'tokens', 'once');

if isempty(token)
    valor = "";
else
    valor = string(strtrim(token{1}));
end

end