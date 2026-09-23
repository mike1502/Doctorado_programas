function token=strtok_all(strinput,delimiter)

remain=strinput;
iCount=0
token(1).val=''

while true
    [str, remain] = strtok(remain,delimiter);
    if isempty(str),  break;  end
    iCount=iCount+1;
    token(iCount).val=str
    disp(sprintf('%s', str))
end