%**************************************************************************
%
%  readstationBMSF.m - Read a station using the BMSF (Base Mexicana de
%                      Sismos Fuertes) format.
%  input  - file path
%  output - station structure
%
%                 lat: latitude
%                 lon: longitude
%       earthquakelat: epicenter lat
%       earthquakelon: epicenter lon
%    numberOfChannels: number of channels 
%             channel: array of number of channels size
%                       string
%                       dt !!! it is a string !!!!! 
%                       acc
%                       polarity
%                       angle  - azimuth
%          origintime: in s from time 00:00:00 of the day (wont work when
%                      it is close to the next day!!!!)
%         northsignal: acc north
%          eastsignal: acc east
%            vertical: vertical
%
%   Author: Leo Ramírez
%           leoramirezg@gmail.com or lramirezg@iingen.unam.mx
%**************************************************************************
function station=readstationBMSF_beta(fname)

[header, data]=hdrload(fname);

% Go through the header to get the location of the station
sizeHeader=size(header);

% 
stringsToSearch(1).val='COORDENADAS DE LA ESTACION';
stringsToSearch(2).val='COORDENADAS DEL EPICENTRO';
stringsToSearch(3).val='NUMERO DE CANALES';
stringsToSearch(4).val='CANAL-';

stringsToSearch(5).val.op(1).val='INTERVALO DE MUESTREO, C1-C6 (s)'
stringsToSearch(5).val.op(2).val='INTERVALO DE MUESTREO, C1-C6, (s)'
stringsToSearch(6).val='INTERVALO DE MUESTREO, C7-C12 (s)'
stringsToSearch(7).val='HORA DE LA PRIMERA MUESTRA (GMT)';
stringsToSearch(8).val='MAGNITUD(ES)';

% ************* Station location*******************************************
station.lat= str2num(retrieve_value_fromheader(header,stringsToSearch(1).val,...
                                                         2,0,':',' ','nan'))
station.lon=-str2num(retrieve_value_fromheader(header,stringsToSearch(1).val,...
                                                         2,1,':',' ','nan')) 
                                                     
station.Mw=str2num(retrieve_value_fromheader(header,stringsToSearch(8).val,...
                                                         2,0,':','/M=','nan'))                                                      
                                                     

% ***********Earthquake location ******************************************
station.earthquakelat= str2num(retrieve_value_fromheader(header, ...
                                 stringsToSearch(2).val,2,0,':',' ','nan'))
station.earthquakelon=-str2num(retrieve_value_fromheader(header, ...
                                 stringsToSearch(2).val,2,1,':',' ','nan'))  

% ************** Channels' info********************************************
station.numberOfChannels=str2num(retrieve_value_fromheader(header,...
                                 stringsToSearch(3).val,2,0,':',' ','nan'))
for iCh=1:station.numberOfChannels
    station.channel(iCh).string=retrieve_value_fromheader(header,...
                              stringsToSearch(4).val,iCh-1,1,' ',' ','nan')
    default=-999999
    dt=default;
    iOp=0
    while(dt==default)
        iOp=iOp+1
        dt=retrieve_value_fromheader(header,...
                stringsToSearch(5).val.op(iOp).val,iCh+1,0,':','/',default)  
    end
    station.channel(iCh).dt=str2num(dt);
end

if(isempty(str2num(retrieve_value_fromheader(header, ...
        stringsToSearch(7).val,1,0,':',':','nan'))))
    station.origintime=[];
else
    
    station.origintime=3600*str2num(retrieve_value_fromheader(header, ...
        stringsToSearch(7).val,1,0,':',':','nan')) + ...
        60*str2num(retrieve_value_fromheader(header, ...
        stringsToSearch(7).val,2,0,':',': ','nan')) + ...
        str2num(retrieve_value_fromheader(header, ...
        stringsToSearch(7).val,3,0,':',': ','nan'));
end
%  **********Now obtain the data*******************************************
for iCh=1:station.numberOfChannels
    station.channel(iCh).acc=data(:,iCh)
end

% Postprocess the info to obtain the channel orientation, working with
% azimuth=angle
for iCh=1:station.numberOfChannels  
    station.channel(iCh).polarity=1;
    orientation=upper(station.channel(iCh).string);
    station.channel(iCh).polarity=nan
    angle=nan
    angleI=nan
    % vertical
    if((findstr(orientation,'V')>0) | (findstr(orientation,'v'))>0)
        station.channel(iCh).polarity=0;
        station.channel(iCh).angle=0;
        if((strfind(orientation,'-'))==1)
            station.channel(iCh).acc= -station.channel(iCh).acc;
        end        
    end
    % S
    if(isempty(strfind(orientation,'S')) ~= 1)
        
       
       angle=180;       
       if(isempty(strfind(orientation,'W'))~=1)
           indexA=findstr(orientation,'S')
           indexB=findstr(orientation,'W')
           angleI=str2num(orientation(indexA+1:indexB-1))                                
       end
       if(isempty(strfind(orientation,'E'))~=1)
           indexA=findstr(orientation,'S')
           indexB=findstr(orientation,'E')
           angleI=-str2num(orientation(indexA+1:indexB-1))                                
       end   
       
       
    end    
    
    % N
    if(isempty((strfind(orientation,'N'))) ~= 1)
       angle=0;       
       if(isempty(strfind(orientation,'W'))~=1)
           indexA=findstr(orientation,'N')
           indexB=findstr(orientation,'W')
           angleI=-str2num(orientation(indexA+1:indexB-1))                                
       end
       if(isempty(strfind(orientation,'E'))~=1)
           indexA=findstr(orientation,'N')
           indexB=findstr(orientation,'E')
           angleI=str2num(orientation(indexA+1:indexB-1))                                
       end                                 
    end
        
    station.channel(iCh).angle=angle+angleI;    
    
end
station.northsignal=station.channel(1).acc*0;
station.eastsignal=station.northsignal;
% compute using the two channels with info the North and East components
for iChn=1:3
    if(isnan(station.channel(iChn).angle)~=1)
   
        e=[cosd(station.channel(iChn).angle)  sind(station.channel(iChn).angle)];
        north=[1 0];
        east=[0 1];
        station.northsignal=station.northsignal+dot(e,north)*station.channel(iChn).acc;
        station.eastsignal=station.eastsignal+dot(e,east)*station.channel(iChn).acc;
        
    else
        
        station.vertical=station.channel(iChn).acc;
        
    end
end





    
    
    
    
