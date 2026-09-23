% if position == 0 the val

function value=retrieve_value_fromheader(inputheader,stringtosearch,position,linesahead,delimiter,delimitert,default)

sizeHeader=size(inputheader);
value=[]  
iCount=0
doit=1
while ((doit==1) && (iCount<sizeHeader(1)))
    iCount=iCount+1;
    if(isempty(strfind(inputheader(iCount,:), stringtosearch)))
        doit=1
    else
        doit=0
        % The String was found thus retrieve the requiered info
            [val , remain ] = strtok(inputheader(iCount+linesahead,:),delimiter);
            token=strtok_all(remain,delimitert)
            if(position == 0)
                value=val;
            else
                value=(token(position).val);
            end
            clear('token','val','remain')
                    
    end
end
if(isempty(value))
    value=default;
end
return

