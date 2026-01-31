#!/bin/bash
# EvoBot Service Management Script
# For 24/7 operation

SERVICE_NAME="evobot_dashboard"
SERVICE_FILE="/home/ubuntu/personal/evobot/evobot_dashboard.service"
SYSTEMD_PATH="/etc/systemd/system/${SERVICE_NAME}.service"
LOG_DIR="/home/ubuntu/personal/evobot/logs"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=============================================="
echo "  EvoBot 24/7 Service Manager"
echo "=============================================="

# Create logs directory if not exists
mkdir -p "$LOG_DIR"

case "$1" in
    install)
        echo -e "${YELLOW}Installing EvoBot as a systemd service...${NC}"
        
        # Copy service file
        sudo cp "$SERVICE_FILE" "$SYSTEMD_PATH"
        
        # Reload systemd
        sudo systemctl daemon-reload
        
        # Enable service to start on boot
        sudo systemctl enable "$SERVICE_NAME"
        
        echo -e "${GREEN}Service installed successfully!${NC}"
        echo ""
        echo "Commands:"
        echo "  Start:   sudo systemctl start $SERVICE_NAME"
        echo "  Stop:    sudo systemctl stop $SERVICE_NAME"
        echo "  Status:  sudo systemctl status $SERVICE_NAME"
        echo "  Logs:    journalctl -u $SERVICE_NAME -f"
        ;;
        
    start)
        echo -e "${YELLOW}Starting EvoBot service...${NC}"
        sudo systemctl start "$SERVICE_NAME"
        sleep 2
        sudo systemctl status "$SERVICE_NAME" --no-pager
        ;;
        
    stop)
        echo -e "${YELLOW}Stopping EvoBot service...${NC}"
        sudo systemctl stop "$SERVICE_NAME"
        echo -e "${GREEN}Service stopped.${NC}"
        ;;
        
    restart)
        echo -e "${YELLOW}Restarting EvoBot service...${NC}"
        sudo systemctl restart "$SERVICE_NAME"
        sleep 2
        sudo systemctl status "$SERVICE_NAME" --no-pager
        ;;
        
    status)
        sudo systemctl status "$SERVICE_NAME" --no-pager
        echo ""
        echo "Recent logs:"
        tail -20 "$LOG_DIR/evobot.log" 2>/dev/null || echo "No logs yet"
        ;;
        
    logs)
        echo -e "${YELLOW}Following EvoBot logs (Ctrl+C to exit)...${NC}"
        journalctl -u "$SERVICE_NAME" -f
        ;;
        
    uninstall)
        echo -e "${YELLOW}Uninstalling EvoBot service...${NC}"
        sudo systemctl stop "$SERVICE_NAME" 2>/dev/null
        sudo systemctl disable "$SERVICE_NAME" 2>/dev/null
        sudo rm -f "$SYSTEMD_PATH"
        sudo systemctl daemon-reload
        echo -e "${GREEN}Service uninstalled.${NC}"
        ;;
        
    *)
        echo "Usage: $0 {install|start|stop|restart|status|logs|uninstall}"
        echo ""
        echo "Commands:"
        echo "  install   - Install EvoBot as a systemd service (runs on boot)"
        echo "  start     - Start the EvoBot service"
        echo "  stop      - Stop the EvoBot service"
        echo "  restart   - Restart the EvoBot service"
        echo "  status    - Show service status and recent logs"
        echo "  logs      - Follow live logs"
        echo "  uninstall - Remove the systemd service"
        exit 1
        ;;
esac
