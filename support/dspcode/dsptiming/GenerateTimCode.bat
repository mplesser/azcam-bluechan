@echo off
rem Creates .lod files for ARC timing boards
rem MPL 13Aug08

rem arguments => CONTROLLER CONFIG
rem CONTROLLER is   gen1 gen2 gen3
rem CONFIG is       config0 config1 config2 config3

rem Directory paths - change as needed
set ROOT=\azcam\MotorolaDSPTools\
set ROOT3=%ROOT%CLAS563\BIN\
set ROOT0=%ROOT%CLAS56\BIN\

@echo on

rem *** set CONFIG flag -> default is 0 ***
set CONFIG=config0
set CONFIGFLAG=-d CONFIG0 1 -d CONFIG1 0 -d CONFIG2 0 -d CONFIG3 0

if /i %2 EQU Config0 (
set CONFIGFLAG=-d CONFIG0 1 -d CONFIG1 0 -d CONFIG2 0 -d CONFIG3 0
set CONFIG=config0
)
if /i %2 EQU Config1 (
set CONFIGFLAG=-d CONFIG0 0 -d CONFIG1 1 -d CONFIG2 0 -d CONFIG3 0
set CONFIG=config1
)
if /i %2 EQU Config2 (
set CONFIGFLAG=-d CONFIG0 0 -d CONFIG1 0 -d CONFIG2 1 -d CONFIG3 0
set CONFIG=config2
)
if /i %2 EQU Config3 (
set CONFIGFLAG=-d CONFIG0 0 -d CONFIG1 0 -d CONFIG2 0 -d CONFIG3 1
set CONFIG=config3
)

rem *** assemble gen1 code ***
if /i %1 EQU gen1 (

rem *** assemble boot code ***
%ROOT0%asm56000 -b -ltim1_boot.ls tim1_boot.asm

%ROOT0%asm56000 -ltim1_%TYPE%_%CONFIG%.ls -b -d DOWNLOAD 1 %CONFIGFLAG% tim1.asm
%ROOT0%dsplnk -b tim1.cld -v tim1_boot.cln tim1.cln
del tim1.cln
%ROOT0%cldlod tim1.cld > tim1_%CONFIG%.lod
del tim1.cld

del tim1_boot.cln
)

rem *** assemble gen2 code ***
if /i %1 EQU gen2 (

rem *** assemble boot code ***
%ROOT0%asm56000 -b -ltim2_boot.ls tim2_boot.asm

%ROOT0%asm56000 -ltim2_%TYPE%_%CONFIG%.ls -b -d DOWNLOAD HOST %CONFIGFLAG% tim2.asm
%ROOT0%dsplnk -b tim2.cld -v tim2_boot.cln tim2.cln 
del tim2.cln
%ROOT0%cldlod tim2.cld > tim2_%CONFIG%.lod
del tim2.cld

del tim2_boot.cln
)

rem *** assemble gen3 code ***
if /i %1 EQU gen3 (

%ROOT3%asm56300 -ltim3_%TYPE%_%CONFIG%.ls -b -d DOWNLOAD HOST %CONFIGFLAG% tim3.asm
%ROOT3%dsplnk -b tim3.cld -v tim3.cln 
del tim3.cln
%ROOT3%cldlod tim3.cld > tim3_%CONFIG%.lod
del tim3.cld
)

rem pause
