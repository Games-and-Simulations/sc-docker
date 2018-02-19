SET /A "index=1"
SET /A "boundary=1000"

:while
if %index% leq %boundary% (
   bwapi-data\AI\CherryPi.exe -hostname 127.0.0.1 -bandit 1
   SET /A "index=index + 1"
   goto :while
)

exit