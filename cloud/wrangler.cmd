@echo off
rem Runs the local Wrangler with Node on PATH. Usage: "C:\Users\aweb9\Music App\cloud\wrangler.cmd" login
set "PATH=C:\Program Files\nodejs;%PATH%"
cd /d "%~dp0"
call "%~dp0node_modules\.bin\wrangler.cmd" %*
