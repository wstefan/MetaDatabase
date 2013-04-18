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

% get file paths
% Study id 7, all files (%) with meta info "complex=phase" and
% "complex=magnitude"
lp =db.searchFiles(8,'treatment. T-MAP RT TEMPORAL ORTHO 2 PLANE','complex=phase');
lm =db.searchFiles(8,'treatment. T-MAP RT TEMPORAL ORTHO 2 PLANE','complex=magnitude');
hotspot=[185 140 64];  loc=1;


% get meta tags for temperature from "phase" files
btemp = db.getMeta(lp,'Body Temperature');
btemp = arrayfun(@(x)cell2mat(textscan(char(x),'%f')),btemp); % convert java.lang.String[] to double
db.close();

%% read images
tic
dataset=MRImageSetMagPhase();
dataset.read(lm,lp);
toc

%% find temp maps

% Reference based thermometry
dataset2=MRImageSet(dataset); % copy to new image set
dataset2.times(conj(dataset2.image{4,loc}.getSignData()));  % Multiply with conj(x/|x|) of reference phase.

% unwrap phase and compute temperature of image in dataset2
Tmap_ref     = temperatureMapSupp(dataset2.image{hotspot(3),loc},struct('order',1))+btemp(dataset2.idx(hotspot(3),loc));

% refernce less thermometry (use original dataset): 
Tmap_refless = temperatureMapSupp(dataset.image{hotspot(3),loc},struct('order',3))+btemp(dataset.idx(hotspot(3),loc));

%% contour plots:
f=figure();
clf
contour(Tmap_ref,[45 50 55 60]); hold on
contour(Tmap_refless,[45 50 55 60],'--'); hold on
axis([hotspot(2)-32 hotspot(2)+32 hotspot(1)-32 hotspot(1)+32])
title('45C 50C 55C and 60C')
legend('ref method','ref less')
