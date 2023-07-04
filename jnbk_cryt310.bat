set root=%USERPROFILE%\anaconda3
set rootdirr=%USERPROFILE%\Documents\Github\cryptotradr
call %root%\Scripts\activate.bat %root%

call conda activate cryt310

call cd %rootdirr%

call jupyter notebook

pause