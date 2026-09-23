%
%
% [time] = plot_nsamples_dt(signal,dt,t0)
%
% plots a signal with the t axis according to the initial time t0 and 
% sampling time dt
%
% input 
%        dt       - sampling time
%        t0       - initial time
%        varargin - color plot   % needs to be improved
%

%
% returns
%        the time axis
%   

function  [time]=plot_nsamples_dt(signal,dt,t0,varargin)

 optargin = size(varargin,2);

 n=length(signal);
 time=0:dt:dt*(n-1);
 time=time+t0;
 set(gcf,'renderer','zbuffer');
 if(optargin>0)
    plot(time,signal,varargin{:});
 else
    plot(time,signal); 
 end
 
return;
