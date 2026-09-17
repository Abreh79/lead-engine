#!/usr/bin/env bash
SESSION="contractor_engine"
DIR="/home/yayock79/lead_engine"
PYTHON="$DIR/venv/bin/python"
CLOUDFLARED="$DIR/cloudflared"
TUNNEL_FILE="$DIR/current_tunnel.txt"
LOG_FILE="$DIR/tunnel.log"

stop_services() {
    echo "[DAEMON] Stopping $SESSION services..."
    tmux kill-session -t "$SESSION" 2>/dev/null
    pkill -f "server.py" 2>/dev/null
    pkill -f "cloudflared" 2>/dev/null
    sleep 1
}

start_services() {
    stop_services
    echo "[DAEMON] Starting $SESSION tmux session..."
    
    # Window 0: Flask preview server (looping for auto-restart)
    tmux new-session -d -s "$SESSION" -n "server" "cd $DIR && while true; do $PYTHON server.py; sleep 2; done"
    
    # Window 1: Cloudflared tunnel
    tmux new-window -t "$SESSION" -n "tunnel" "cd $DIR && $CLOUDFLARED tunnel --url http://localhost:8080 > $LOG_FILE 2>&1"
    
    echo "[DAEMON] Waiting for services to initialize..."
    sleep 4
    
    # Parse tunnel URL and write to current_tunnel.txt
    if [ -f "$LOG_FILE" ]; then
        URL=$(grep -o "https://[a-zA-Z0-9-]*\.trycloudflare\.com" "$LOG_FILE" | tail -n 1)
        if [ -n "$URL" ]; then
            echo "$URL" > "$TUNNEL_FILE"
            echo "[DAEMON] Active Tunnel: $URL"
        else
            echo "[DAEMON] Warning: Tunnel URL not found in log yet."
        fi
    fi
}

status_services() {
    echo "=========================================="
    echo "CONTRACTOR ENGINE DAEMON STATUS"
    echo "=========================================="
    if tmux has-session -t "$SESSION" 2>/dev/null; then
        echo "Tmux Session  : ✅ ACTIVE ($SESSION)"
    else
        echo "Tmux Session  : ❌ INACTIVE"
    fi
    
    if pgrep -f "server.py" >/dev/null; then
        echo "Flask Server  : ✅ LISTENING (Port 8080)"
    else
        echo "Flask Server  : ❌ DOWN"
    fi
    
    if pgrep -f "cloudflared" >/dev/null; then
        echo "Cloudflared   : ✅ RUNNING"
    else
        echo "Cloudflared   : ❌ DOWN"
    fi
    
    if [ -f "$TUNNEL_FILE" ]; then
        echo "Public URL    : $(cat "$TUNNEL_FILE")"
    else
        echo "Public URL    : ❌ NOT FOUND"
    fi
    echo "=========================================="
}

case "$1" in
    start)
        start_services
        status_services
        ;;
    stop)
        stop_services
        status_services
        ;;
    status)
        status_services
        ;;
    *)
        echo "Usage: $0 {start|stop|status}"
        exit 1
        ;;
esac
