%% ================================================================
% CONSTRUIR BASE DE DATOS ASA
%
% Recorre:
%
% base-datos/
%       evento/
%           ACEL/
%               ASA/
%                   *.ASA
%
% y genera:
%
%   Registros
%   Estaciones
%   Eventos
%   Errores
%
% ================================================================

clear
clc


%% ================================================================
% 1. SELECCIONAR BASE DE DATOS
% ================================================================

rutaBase = uigetdir(pwd, ...
    'Selecciona la carpeta BASE-DATOS');

if isequal(rutaBase,0)

    error('No se seleccionó ninguna carpeta.');

end

fprintf('\n========================================\n');
fprintf('BASE DE DATOS ASA\n');
fprintf('========================================\n');

fprintf('Ruta:\n%s\n\n', rutaBase);


%% ================================================================
% 2. OBTENER CARPETAS DE EVENTOS
% ================================================================

carpetas = dir(rutaBase);

carpetas = carpetas([carpetas.isdir]);

carpetas = carpetas(~ismember( ...
    {carpetas.name}, {'.','..'}));


fprintf('Carpetas de eventos encontradas: %d\n', ...
    length(carpetas));


%% ================================================================
% 3. INICIALIZAR
% ================================================================

RegistrosTemp = struct([]);
ErroresTemp = struct([]);

nRegistros = 0;
nErrores = 0;


%% ================================================================
% 4. RECORRER EVENTOS
% ================================================================

for i = 1:length(carpetas)

    nombreEvento = carpetas(i).name;

    fprintf('\n----------------------------------------\n');
    fprintf('Evento %d de %d\n', ...
        i, length(carpetas));

    fprintf('%s\n', nombreEvento);


    %% ------------------------------------------------------------
    % Ruta ACEL/ASA
    % ------------------------------------------------------------

    rutaASA = fullfile( ...
        rutaBase, ...
        nombreEvento, ...
        'ACEL', ...
        'ASA');


    if ~isfolder(rutaASA)

        fprintf('  [!] No existe ACEL/ASA\n');

        continue

    end


    %% ------------------------------------------------------------
    % Buscar archivos
    % ------------------------------------------------------------

    archivos = dir(rutaASA);

    archivos = archivos(~[archivos.isdir]);


    fprintf('  Archivos encontrados: %d\n', ...
        length(archivos));


    %% ------------------------------------------------------------
    % Leer archivos
    % ------------------------------------------------------------

    for j = 1:length(archivos)

        archivo = fullfile( ...
            rutaASA, ...
            archivos(j).name);


        try

            datos = leerASA(archivo);


            % ----------------------------------------------------
            % Agregar información de carpeta
            % ----------------------------------------------------

            datos.FechaCarpeta = string(nombreEvento);


            % ----------------------------------------------------
            % Contador
            % ----------------------------------------------------

            nRegistros = nRegistros + 1;


            RegistrosTemp(nRegistros) = datos;


        catch ME

            nErrores = nErrores + 1;


            ErroresTemp(nErrores).Archivo = ...
                string(archivo);

            ErroresTemp(nErrores).Mensaje = ...
                string(ME.message);


            fprintf('  [ERROR] %s\n', ...
                archivos(j).name);

        end

    end

end


%% ================================================================
% 5. CONVERTIR A TABLA
% ================================================================

if isempty(RegistrosTemp)

    error('No se pudo leer ningún archivo ASA.');

end


Registros = struct2table(RegistrosTemp);


%% ================================================================
% 6. TABLA DE ERRORES
% ================================================================

if isempty(ErroresTemp)

    Errores = table( ...
        strings(0,1), ...
        strings(0,1), ...
        'VariableNames', ...
        {'Archivo','Mensaje'});

else

    Errores = struct2table(ErroresTemp);

end


%% ================================================================
% 7. TABLA DE ESTACIONES
% ================================================================

columnasEstacion = { ...
    'ClaveEstacion', ...
    'Estacion', ...
    'LatitudEstacion', ...
    'LongitudEstacion', ...
    'Altitud', ...
    'TipoSuelo', ...
    'Institucion', ...
    'ModeloAcelerografo', ...
    'NumeroSerie'};


Estaciones = unique( ...
    Registros(:,columnasEstacion), ...
    'rows');


%% ================================================================
% 8. TABLA DE EVENTOS
% ================================================================

columnasEvento = { ...
    'ID_Evento', ...
    'FechaSismo', ...
    'HoraSismo', ...
    'Magnitud', ...
    'LatitudEpicentro', ...
    'LongitudEpicentro', ...
    'Profundidad', ...
    'FuenteEpicentro'};


Eventos = unique( ...
    Registros(:,columnasEvento), ...
    'rows');


%% ================================================================
% 9. ESTADISTICAS BASICAS
% ================================================================

fprintf('\n\n========================================\n');
fprintf('RESULTADOS\n');
fprintf('========================================\n');

fprintf('Eventos diferentes:    %d\n', ...
    height(Eventos));

fprintf('Estaciones diferentes: %d\n', ...
    height(Estaciones));

fprintf('Registros ASA:         %d\n', ...
    height(Registros));

fprintf('Archivos con error:    %d\n', ...
    height(Errores));


%% ================================================================
% 10. GUARDAR BASE MATLAB
% ================================================================

save('BaseASA.mat', ...
    'Registros', ...
    'Estaciones', ...
    'Eventos', ...
    'Errores');


%% ================================================================
% 11. EXPORTAR CSV
% ================================================================

writetable(Registros, ...
    'Registros_ASA.csv');

writetable(Estaciones, ...
    'Estaciones_ASA.csv');

writetable(Eventos, ...
    'Eventos_ASA.csv');

writetable(Errores, ...
    'Errores_ASA.csv');


%% ================================================================
% 12. FIN
% ================================================================

fprintf('\nArchivos generados:\n');

fprintf('  BaseASA.mat\n');
fprintf('  Registros_ASA.csv\n');
fprintf('  Estaciones_ASA.csv\n');
fprintf('  Eventos_ASA.csv\n');
fprintf('  Errores_ASA.csv\n');

fprintf('\nProceso terminado.\n');