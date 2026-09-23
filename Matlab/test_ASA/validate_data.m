%% registros
clear
clc
close

ruta = 'C:\Users\MCarrilloL\Documents\Doctorado\FallaFinita_Registros\base_datos\2023_12_03_0029_02_M2_CDMX\ACEL\ASA';
archivos = dir(ruta);
% Eliminar carpetas
archivos = archivos(~[archivos.isdir]);
N = length(archivos);
fprintf('Número de archivos encontrados: %d\n\n', N);

for i=1:N
    stationCUP=readstationBMSF_beta('*');

end
%dt=(stationCUP.channel(1).dt);

%vs_cup=stationCUP.channel(1).acc;
%ns_cup=stationCUP.channel(2).acc;
%es_cup=stationCUP.channel(3).acc;
%t=0:dt:(length(vs_cup)-1)*dt;

% figure(1)
% subplot(3,1,1)
% plot(t,vs_cup)
% title(' Componente vertical ','FontSize',16)
% %xlabel(' Tiempo [s] ','FontSize',16)
% ylabel(' [cm/s^2] ','FontSize',16)
% 
% subplot(3,1,2)
% plot(t,ns_cup)
% title(' Componente norte-sur ','FontSize',16)
% %xlabel(' Tiempo [s] ','FontSize',16)
% ylabel(' [cm/s^2] ','FontSize',16)
% 
% 
% subplot(3,1,3)
% plot(t,es_cup)
% title(' Componente este-oeste ','FontSize',16)
% xlabel(' Tiempo [s] ','FontSize',16)
% ylabel(' [cm/s^2] ','FontSize',16)
% 
% 
% %%%%%%%%%%%%%%%%%%%%%%%%%%%% VALIDACIÓN %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% 
% %%% Extraer registros de la simulación (TACY, SCT2, CUP5)
% %%% Buscar coordenadas
% 
% %for iCh=1:3
% %    subplot(3,1,iCh)
% %    str2num(station.channel(iCh).dt);
% %    dt=(station.channel(1).dt);
% %    s=station.channel(iCh).acc;
% %    t=0:dt:(length(s)-1)*dt;
% %    plot(t,s,'b')%,'LineWidth',1)
% %    title(' Acelerograma ','FontSize',16)
% %    xlabel(' Tiempo [s] ','FontSize',16)
% %    ylabel(' [cm/s^2] ','FontSize',16)
% %    axis([0 200 min(s) max(s)])
% %    grid on
% %end
% %print('Acelerograma','-dpng');
% 
% stationSCT=readstationBMSF_beta('SCT21709.191');
% dt1=(stationSCT.channel(1).dt);
% 
% vs_sct=stationSCT.channel(1).acc;
% ns_sct=stationSCT.channel(2).acc;
% es_sct=stationSCT.channel(3).acc;
% t=0:dt1:(length(vs_sct)-1)*dt1;
% 
% figure(2)
% subplot(3,1,1)
% plot(t,vs_sct)
% title(' Componente vertical ','FontSize',16)
% %xlabel(' Tiempo [s] ','FontSize',16)
% ylabel(' [cm/s^2] ','FontSize',16)
% 
% subplot(3,1,2)
% plot(t,ns_sct)
% title(' Componente norte-sur ','FontSize',16)
% %xlabel(' Tiempo [s] ','FontSize',16)
% ylabel(' [cm/s^2] ','FontSize',16)
% 
% subplot(3,1,3)
% plot(t,es_sct)
% title(' Componente este-oeste ','FontSize',16)
% xlabel(' Tiempo [s] ','FontSize',16)
% ylabel(' [cm/s^2] ','FontSize',16)
% 
% %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% 
% stationTAC=readstationBMSF_beta('TACY1709.191');
% dt2=(stationTAC.channel(1).dt);
% 
% vs_tac=stationTAC.channel(1).acc;
% ns_tac=stationTAC.channel(2).acc;
% es_tac=stationTAC.channel(3).acc;
% t=0:dt2:(length(vs_tac)-1)*dt2;
% 
% figure(3)
% subplot(3,1,1)
% plot(t,vs_tac)
% title(' Componente vertical ','FontSize',16)
% %xlabel(' Tiempo [s] ','FontSize',16)
% ylabel(' [cm/s^2] ','FontSize',16)
% 
% subplot(3,1,2)
% plot(t,ns_tac)
% title(' Componente norte-sur ','FontSize',16)
% %xlabel(' Tiempo [s] ','FontSize',16)
% ylabel(' [cm/s^2] ','FontSize',16)
% 
% subplot(3,1,3)
% plot(t,es_tac)
% title(' Componente este-oeste ','FontSize',16)
% xlabel(' Tiempo [s] ','FontSize',16)
% ylabel(' [cm/s^2] ','FontSize',16)
% 
