%mksqlite('close')
clear java
close all
if 0
    addpath('../../MATLAB/libs/mksqlite')
    addpath('../../MATLAB/libs/mksqlite')
    javaaddpath('.')
    javaaddpath('../../MATLAB/libs/mysql-connector-java-5.1.24/mysql-connector-java-5.1.24-bin.jar')
end

db=meta_db();

% First look for the first study that has a meta tag type=trash
st=db.searchStudies('%','type=trash');
study=st(1);
fprintf('Using study: %i\n',study)

% Then look for all file descriptions that contains Cor T2
n=db.searchFileDescription(study,'%Cor T2%','');
series_name=char(n(1));
fprintf('Using series: %s\n',series_name)

% Get all files with name that was fitst from the query above
l=db.searchFiles(study,series_name,'');

comp=db.getMeta(l,'Series Date'); % Get meta data for the files


% Ccompute the mean of all images and save result as string
for i=1:length(l);
    dcm=dicomread(char(l(i)));
    test(i)=java.lang.String(sprintf('%f',mean(dcm(:))));
end
% Remove all meta tags that are called test and mean
db.deleteMeta(l,'test')
db.deleteMeta(l,'mean')
% Save mean as meta tag
db.saveMeta(l,'mean',test);
   