%
%
% plot_constant_line(constant,miny,maxy,varargin)
%
% plots a constant value with a line
%
% input 
%        constant - constant to be plot
%        miny     - minimum value in y
%        maxy     - maximum value in y
%

%
% returns
%        the time axis
%   

function  plot_constant_line(constant, miny, maxy,varargin)

 optargin = size(varargin,2)

 x=[constant constant]
 y=[miny maxy]
 set(gcf,'renderer','zbuffer');
 if(optargin>0)
    plot(x,y,varargin{:});
 else
    plot(x,y); 
 end
 
return;
