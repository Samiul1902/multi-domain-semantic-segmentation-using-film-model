@echo off
REM Phase-14 clean-v3 regional refiner training launcher.
REM
REM This launcher changes ONLY the execution mechanism, never the science.
REM It always passes --resume so that any relaunch after an external process
REM termination continues from the last completed epoch. When no checkpoint
REM exists the flag degrades gracefully and training starts from epoch 0.
REM
REM The trainer implementation bound in the freeze manifest is unchanged by
REM this launcher; resume restores model/optimizer/scheduler/scaler AND the
REM full RNG state so the continuation is bit-exact.
cd /d D:\Softfors\jup
.venv\Scripts\python.exe -u scripts\training\train_phase14_refiner.py --resume >> logs\phase14_train.log 2>&1
echo EXITCODE=%ERRORLEVEL% >> logs\phase14_train.log
