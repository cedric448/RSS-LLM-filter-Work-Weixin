#!/bin/bash
# 检查生产环境部署状态

echo "=========================================="
echo "📊 生产环境部署状态检查"
echo "=========================================="

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

check_item() {
    local name=$1
    local command=$2
    
    echo -n "   $name... "
    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
        return 0
    else
        echo -e "${RED}✗${NC}"
        return 1
    fi
}

echo ""
echo "🔍 环境检查:"
check_item "Python3     " "command -v python3"
check_item "Nginx       " "command -v nginx"
check_item "Systemd     " "command -v systemctl"

echo ""
echo "📦 项目文件:"
check_item "项目目录    " "[ -d /root/project-wb/n8n/admin ]"
check_item "主程序      " "[ -f /root/project-wb/n8n/admin/app.py ]"
check_item "配置文件    " "[ -f /root/project-wb/n8n/admin/.env ]"
check_item "模板目录    " "[ -d /root/project-wb/n8n/admin/templates ]"

echo ""
echo "🔧 服务状态:"
check_item "Systemd服务 " "[ -f /etc/systemd/system/rss-admin.service ]"
check_item "服务运行中  " "systemctl is-active --quiet rss-admin"
check_item "Nginx配置   " "[ -f /etc/nginx/conf.d/rss-admin.conf ]"
check_item "Nginx运行中 " "systemctl is-active --quiet nginx"

echo ""
echo "📂 日志目录:"
check_item "日志目录    " "[ -d /var/log/rss-admin ]"
check_item "访问日志    " "[ -f /var/log/rss-admin/access.log ]"
check_item "错误日志    " "[ -f /var/log/rss-admin/error.log ]"

echo ""
echo "🔐 SSL 证书:"
check_item "SSL目录     " "[ -d /etc/nginx/ssl ]"
if [ -f /etc/nginx/ssl/rss-admin.crt ]; then
    echo -e "   证书文件     ${GREEN}✓${NC}"
    echo "   证书信息:"
    openssl x509 -in /etc/nginx/ssl/rss-admin.crt -noout -subject -dates 2>/dev/null | sed 's/^/      /'
else
    echo -e "   证书文件     ${YELLOW}⊗ 未配置${NC}"
fi

echo ""
echo "🌐 网络端口:"
check_item "5002端口    " "netstat -tuln | grep -q ':5002.*LISTEN'"
check_item "80端口      " "netstat -tuln | grep -q ':80.*LISTEN'"
check_item "443端口     " "netstat -tuln | grep -q ':443.*LISTEN'"

echo ""
echo "🧪 连接测试:"
echo -n "   HTTP (80)   ... "
if curl -s http://localhost:80 > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
fi

echo -n "   HTTPS (443) ... "
if curl -k -s https://localhost:443 > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
fi

echo -n "   健康检查    ... "
if curl -k -s https://localhost:443/health | grep -q "ok"; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
fi

echo ""
echo "📝 配置信息:"
if [ -f /root/project-wb/n8n/admin/.env ]; then
    AUTH_CODE=$(grep RSS_ADMIN_AUTH_CODE /root/project-wb/n8n/admin/.env | cut -d '=' -f2)
    if [ -n "$AUTH_CODE" ]; then
        echo "   授权码: ${AUTH_CODE:0:5}...${AUTH_CODE: -5}"
    fi
fi

if [ -f /etc/nginx/conf.d/rss-admin.conf ]; then
    DOMAIN=$(grep "server_name" /etc/nginx/conf.d/rss-admin.conf | head -1 | awk '{print $2}' | tr -d ';')
    echo "   域名: $DOMAIN"
fi

SERVER_IP=$(hostname -I | awk '{print $1}')
echo "   服务器IP: $SERVER_IP"

echo ""
echo "=========================================="

# 统计结果
echo ""
echo "💡 访问地址:"
if [ "$DOMAIN" != "_" ] && [ -n "$DOMAIN" ]; then
    echo "   https://$DOMAIN"
else
    echo "   https://$SERVER_IP"
    echo "   （自签名证书需忽略浏览器警告）"
fi

echo ""
echo "🔧 管理命令:"
echo "   systemctl status rss-admin    # 查看服务状态"
echo "   journalctl -u rss-admin -f    # 查看服务日志"
echo "   tail -f /var/log/rss-admin/*.log  # 查看应用日志"
echo "   nginx -t                      # 测试 Nginx 配置"
echo "   systemctl reload nginx        # 重载 Nginx"
echo ""
