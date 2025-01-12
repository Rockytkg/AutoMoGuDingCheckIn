#!/bin/bash

# 检查是否是 root 用户
check_root_user() {
    if [[ $EUID -ne 0 ]]; then
        echo "错误：首次运行需要以 root 权限执行。"
        exit 1
    fi
}

# 依赖检查并安装（仅首次运行）
initialize_environment() {
    echo "开始环境初始化..."

    # 检查并安装指定依赖
    check_and_install() {
        PACKAGE_NAME=$1
        PACKAGE_CMD=$2
        if ! command -v $PACKAGE_CMD &>/dev/null; then
            echo "$PACKAGE_NAME 未安装，正在尝试安装..."
            if [[ "$OSTYPE" == "linux-gnu"* ]]; then
                sudo apt-get update
                sudo apt-get install -y $PACKAGE_NAME
            elif [[ "$OSTYPE" == "darwin"* ]]; then
                brew install $PACKAGE_NAME
            else
                echo "不支持的操作系统，无法安装 $PACKAGE_NAME"
                exit 1
            fi
        else
            echo "$PACKAGE_NAME 已安装"
        fi
    }

    # 检查 cron 和 python3-venv 是否安装
    check_and_install "cron" "cron"
    check_and_install "python3-venv" "python3"

    # 确保存在 Python 3
    PYTHON_CMD=$(command -v python3 || command -v python)
    if [ -z "$PYTHON_CMD" ]; then
        echo "错误：未找到 Python 3 或 Python 命令"
        exit 1
    fi

    # 创建虚拟环境（仅首次）
    if [ ! -d ".venv" ]; then
        echo "创建 Python 虚拟环境 .venv"
        $PYTHON_CMD -m venv .venv
        echo "激活虚拟环境并安装依赖（如果有 requirements.txt）"
        source .venv/bin/activate
        if [ -f "requirements.txt" ]; then
            if ! pip install -r requirements.txt; then
                echo "错误：安装依赖时发生错误"
                exit 1
            fi
        fi
    else
        echo "虚拟环境已存在，跳过创建步骤"
    fi

    # 设置定时任务（仅首次）
    SCRIPT_PATH="$(realpath "$0")" # 动态获取当前脚本的绝对路径
    if ! crontab -l | grep -q "$SCRIPT_PATH"; then
        echo "首次运行，设置定时任务..."
        read -p "请输入定时任务的小时（0-23，以逗号分隔，例如 8,12,16,20这样写将在8点12点16点20点执行打卡）： " HOURS
        read -p "请输入定时任务的分钟（0-59，默认 0）： " MINUTES
        MINUTES=${MINUTES:-0}

        CRON_JOB="$MINUTES $HOURS * * * $SCRIPT_PATH"
        (
            crontab -l
            echo "$CRON_JOB"
        ) | crontab -
        echo "定时任务已设置为：$CRON_JOB"
    else
        echo "定时任务已存在，无需重复设置。"
    fi
}

# 执行主逻辑
run_main_script() {
    echo "激活虚拟环境"
    source .venv/bin/activate

    if [ -f "main.py" ]; then
        echo "执行 main.py"
        python main.py
    else
        echo "错误：未找到 main.py 文件"
        exit 1
    fi
}

# 获取脚本所在的绝对路径并切换到该目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR" || { echo "无法切换到脚本目录: $SCRIPT_DIR"; exit 1; }

# 检查是否是首次运行
if [ ! -f ".initialized" ]; then
    echo "首次运行脚本，执行初始化..."
    check_root_user # 首次运行时检查是否为 root 用户
    initialize_environment
    touch .initialized

    # 询问是否立即执行 main.py
    read -p "是否立即执行 main.py？(y/n): " EXECUTE_NOW
    if [[ "$EXECUTE_NOW" =~ ^[Yy]$ ]]; then
        run_main_script
    else
        echo "您选择不立即执行 main.py。"
    fi
else
    echo "脚本已初始化，直接运行 main.py"
    run_main_script
fi
