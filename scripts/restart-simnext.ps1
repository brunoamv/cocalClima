# ==================== CONFIGURAÇÕES ====================
$simNextPath = "C:\Program Files\Intelbras\SIMNext\SimNext.exe"
$ffmpegPath  = "C:\Program Files\Intelbras\SIMNext\broadcaster\ffmpeg-simnext.exe"
$logPath     = "C:\Scripts\simnext-log.txt"

$defaultArgs = '-rtsp_transport udp -thread_queue_size 4096 -i "rtsp://admin:CoraRosa@192.168.3.62:554/cam/realmonitor?channel=1&subtype=0" -f lavfi -i anullsrc=channel_layout=mono:sample_rate=8000 -vcodec h264 -tune zerolatency -g 20 -pix_fmt + -c:a aac -strict experimental -f flv -vf scale=640:360,setsar=1:1 "rtmp://a.rtmp.youtube.com/live2/yx67-vfxc-q2vb-4rkb-402d"'

# ==================== FUNÇÕES ====================
function Write-Log {
    param([string]$message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -Path $logPath -Value "[$timestamp] $message"
}

function Stop-ProcessSafe {
    param([string]$processName)
    try {
        $proc = Get-Process -Name $processName -ErrorAction SilentlyContinue
        if ($proc) {
            Stop-Process -Name $processName -Force -ErrorAction Stop
            Write-Log "Processo $processName parado com sucesso."
        } else {
            Write-Log "Processo $processName já estava parado."
        }
    } catch {
        $errorMsg = $_ | Out-String
        Write-Log ("Erro ao parar processo $processName:`n" + $errorMsg)
    }
}

function Restart-ServiceSafe {
    param([string]$serviceName)
    try {
        Write-Log "Parando serviço $serviceName..."
        Stop-Service -Name $serviceName -Force -ErrorAction Stop
        Start-Sleep -Seconds 3
        Start-Service -Name $serviceName -ErrorAction Stop
        Write-Log "Serviço $serviceName reiniciado com sucesso."
    } catch {
        $errorMsg = $_ | Out-String
        Write-Log ("Erro ao reiniciar serviço $serviceName:`n" + $errorMsg)
    }
}

function Start-ProcessSafe {
    param(
        [string]$path,
        [string]$arguments = ""
    )
    try {
        if ($arguments) {
            Start-Process -FilePath $path -ArgumentList $arguments -WindowStyle Hidden
        } else {
            Start-Process -FilePath $path -WindowStyle Hidden
        }
        Write-Log "Processo iniciado: $path $arguments"
    } catch {
        $errorMsg = $_ | Out-String
        Write-Log ("Erro ao iniciar processo $path:`n" + $errorMsg)
    }
}

# ==================== INÍCIO DO SCRIPT ====================
Write-Log "==== Iniciando rotina de manutenção ===="

# 1. Parar o ffmpeg-simnext
Stop-ProcessSafe -processName "ffmpeg-simnext"
Start-Sleep -Seconds 5

# 2. Reiniciar o serviço FFmpeg-SIMNext
Restart-ServiceSafe -serviceName "FFmpeg-SIMNext"

# 3. Garantir que o SIMNext esteja rodando
$simNextRunning = Get-Process -Name "SIMNext" -ErrorAction SilentlyContinue
if (-not $simNextRunning) {
    Write-Log "SIMNext não está rodando. Iniciando..."
    Start-ProcessSafe -path $simNextPath
    Start-Sleep -Seconds 10
} else {
    Write-Log "SIMNext já está rodando."
}

# 4. Iniciar o ffmpeg-simnext novamente com os argumentos
$ffmpegProc = Get-CimInstance Win32_Process | Where-Object { $_.Name -eq "ffmpeg-simnext.exe" }
if ($ffmpegProc) {
    $previousArgs = $ffmpegProc.CommandLine
    Write-Log "Reiniciando ffmpeg-simnext com argumentos anteriores: $previousArgs"
    Start-ProcessSafe -path $ffmpegPath -arguments $previousArgs
} else {
    Write-Log "Nenhum argumento anterior encontrado. Usando padrão."
    Start-ProcessSafe -path $ffmpegPath -arguments $defaultArgs
}

Write-Log "==== Rotina finalizada ===="
exit
