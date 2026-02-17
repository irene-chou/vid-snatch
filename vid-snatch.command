#!/bin/bash
# vid-snatch 一鍵啟動腳本
# 雙擊此檔案即可使用

cd "$(dirname "$0")"

# 檢查 Docker
if ! command -v docker &> /dev/null; then
    echo "============================================"
    echo "  需要先安裝 Docker Desktop"
    echo "  下載：https://docker.com/products/docker-desktop/"
    echo "============================================"
    read -n 1 -p "按任意鍵開啟下載頁面..."
    open "https://www.docker.com/products/docker-desktop/"
    exit 1
fi

# 檢查 Docker 是否正在執行
if ! docker info &> /dev/null 2>&1; then
    echo "正在啟動 Docker Desktop..."
    open -a Docker
    while ! docker info &> /dev/null 2>&1; do
        sleep 2
    done
    echo "Docker 已就緒！"
fi

# 首次 build
if ! docker image inspect vid-snatch &> /dev/null 2>&1; then
    echo ""
    echo "首次使用，正在建置環境（約 3-5 分鐘）..."
    echo ""
    docker build -t vid-snatch .
    echo ""
    echo "建置完成！"
fi

# 主迴圈
while true; do
    echo ""
    echo "============================================"
    echo "  vid-snatch"
    echo "============================================"
    echo ""
    echo "  1) 下載音檔 (MP3)"
    echo "  2) 下載音檔 + 去人聲 (MP3)"
    echo "  3) 下載影片 (MP4)"
    echo "  4) 重新建置 (更新程式後使用)"
    echo "  q) 離開"
    echo ""
    read -p "請選擇 [1/2/3/4/q]: " choice

    case "$choice" in
        1|2|3)
            echo ""
            read -p "請貼上 YouTube 網址: " url

            if [ -z "$url" ]; then
                echo "網址不能為空！"
                continue
            fi

            # 組裝指令
            cmd=()
            case "$choice" in
                2) cmd+=("--no-vocals" "--keep-vocals") ;;
                3) cmd+=("--video") ;;
            esac

            echo ""
            echo "處理中..."
            [ "$choice" = "2" ] && echo "(去人聲需要 1-2 分鐘，請耐心等候)"
            echo ""

            docker run --rm -it \
                -v "$HOME/Music/vid-snatch:/app/output" \
                vid-snatch "$url" "${cmd[@]}"

            echo ""
            echo "============================================"
            echo "  完成！檔案已存到："
            echo "  ~/Music/vid-snatch/"
            echo "============================================"

            # 開啟資料夾
            open "$HOME/Music/vid-snatch/" 2>/dev/null
            ;;
        4)
            echo ""
            echo "移除舊版本..."
            docker rmi vid-snatch 2>/dev/null
            docker builder prune -f 2>/dev/null
            echo "重新建置中（約 3-5 分鐘）..."
            docker build -t vid-snatch .
            echo ""
            echo "建置完成！舊的暫存檔已清除。"
            ;;
        q|Q)
            echo "Bye!"
            exit 0
            ;;
        *)
            echo "無效選擇，請輸入 1、2、3、4 或 q"
            ;;
    esac
done
