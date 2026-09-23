%
%
% [energ,dur,iti,itf]=movint(a,dt,ll,ul)
%
%  a  =  signal
%  dt = delta time
%  ll = lower limt of total energy (0-1)
%  ul = upper limt of total energy (0-1)
function [energ,dur,iti,itf]=movint(a,dt,ll,ul)
a=a.*a;
energ=cumsum(a);
if(sum(energ) >0)
    energ=energ/energ(end);
    iti=find(energ>=ll,1);
    itf=find(energ>=ul,1);
    dur=(itf-iti)*dt;
    clear energ;
    energ=(1/dt)*trapz(a);
else
    energ=0;
    iti=1;
    itf=1;
    dur=0;    
end

