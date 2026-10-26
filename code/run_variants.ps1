cd D:\Thanapon\Paper1_CRH\R14_StateSpace\code
$env:ONLY="main"; py s1_fit.py
py diag_plot.py main
$jobs = @()
foreach ($v in "drop_truncated","naive_truncated","sensor_jump","mean_anchor","no_anchor") {
  $jobs += Start-Process -FilePath cmd.exe -ArgumentList "/c set ONLY=$v&& set OMP_NUM_THREADS=2&& py s1_fit.py > ..\results\log_$v.txt 2>&1" -NoNewWindow -PassThru
}
$jobs | Wait-Process
"variants done"
