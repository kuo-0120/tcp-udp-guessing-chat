"""
簡易猜數字聊天室伺服器
---------------------------------
功能：
1. 使用 TCP 與每個 Client 建立可靠連線 (SOCK_STREAM)。
2. 使用 UDP Broadcast 廣播遊戲開始訊息與公佈獲勝者。
3. 採用 multi‑thread 模式，為每位 Client 開啟一條執行緒處理 I/O。
4. 支援指令：
   - LOGIN:<暱稱>
   - GUESS:<數字>
   - CHAT:<訊息>
"""

import os
import socket
import threading
import random
import time

# ────────────────────────────────────────
# TCP 參數設定
# ────────────────────────────────────────
HOST = os.getenv('CHAT_HOST', '0.0.0.0')
TCP_PORT = int(os.getenv('CHAT_TCP_PORT', '12345'))

# ────────────────────────────────────────
# UDP 廣播設定 (Broadcast)
# ────────────────────────────────────────
BROADCAST_IP = os.getenv('CHAT_BROADCAST_IP', '255.255.255.255')
UDP_PORT = int(os.getenv('CHAT_UDP_PORT', '54321'))

# ────────────────────────────────────────
# 遊戲狀態與同步資源
# ────────────────────────────────────────
guess_number = random.randint(1, 100)  # 產生 1~100 的隨機答案
clients = []            # 在線 TCP 連線清單
client_names = {}       # {conn: nickname}
lock = threading.Lock() # 保護共用資源的互斥鎖

# ────────────────────────────────────────
# UDP 廣播函式
# ────────────────────────────────────────

def broadcast_message(message: str) -> None:
    """將 message 以 UDP Broadcast 送出"""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_sock:
        udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        udp_sock.sendto(message.encode(), (BROADCAST_IP, UDP_PORT))

# ────────────────────────────────────────
# TCP 廣播 (群播至所有已連線客戶) 函式
# ────────────────────────────────────────

def send_to_all_clients(msg: str, exclude=None) -> None:
    """將 msg 傳給所有 client；exclude 可排除某特定 conn"""
    with lock:
        for c in clients:
            if c != exclude:
                try:
                    c.sendall(msg.encode())
                except Exception:
                    pass

# ────────────────────────────────────────
# 子執行緒：處理單一 Client 的所有 TCP I/O
# ────────────────────────────────────────

def handle_client(conn: socket.socket, addr):
    print(f"[連線] {addr} 已連線")
    with lock:
        clients.append(conn)

    nickname = ""  # 當前連線的暱稱
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break  # Client 正常關閉
            msg = data.decode().strip()

            # ---------- 處理各種指令 ----------
            if msg.startswith("LOGIN:"):
                # 1. 處理登入 (設定暱稱)
                nickname = msg.split(":", 1)[1]
                client_names[conn] = nickname
                send_to_all_clients(f"[系統] {nickname} 加入聊天室。", exclude=None)
                conn.sendall("遊戲開始！猜一個 1～100 的數字，或輸入聊天訊息：\n".encode())

            elif msg.startswith("GUESS:"):
                # 2. 處理猜數字
                try:
                    guess = int(msg.split(":", 1)[1])
                    if guess < guess_number:
                        conn.sendall("太小了\n".encode())
                    elif guess > guess_number:
                        conn.sendall("太大了\n".encode())
                    else:
                        conn.sendall("答對了！\n".encode())
                        winner = client_names.get(conn, str(addr))
                        # 以 UDP 廣播宣佈結果
                        broadcast_message(f"玩家 {winner} 猜中了答案！遊戲結束")
                        send_to_all_clients(f"[系統] 玩家 {winner} 猜中了答案！\n", exclude=conn)
                        break  
                except ValueError:
                    conn.sendall("請輸入正確格式：GUESS:數字\n".encode())

            elif msg.startswith("CHAT:"):
                # 3. 處理聊天訊息
                chat_msg = msg.split(":", 1)[1]
                nickname = client_names.get(conn, str(addr))
                send_to_all_clients(f"[{nickname}] {chat_msg}", exclude=None)

            else:
                # 4. 未知指令
                conn.sendall("格式錯誤，請用 GUESS:數字 或 CHAT:訊息\n".encode())

    finally:
        # ---------- 斷線清理 ----------
        with lock:
            clients.remove(conn)
        left_name = client_names.pop(conn, str(addr))
        send_to_all_clients(f"[系統] {left_name} 離開聊天室。", exclude=conn)
        conn.close()
        print(f"[離線] {addr} 已離線")

# ────────────────────────────────────────
# 主程式：啟動伺服器並等待連線
# ────────────────────────────────────────

def start_server() -> None:
    print("等待 client 連線中...")
    time.sleep(2)  # 稍等 2 秒，避免 Client 尚未啟動收不到第一次廣播
    broadcast_message("遊戲開始！請連線參與猜數字！")

    # 建立 TCP 監聽 socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_sock.bind((HOST, TCP_PORT))
        server_sock.listen()
        print(f"[啟動] 伺服器啟動於 {HOST}:{TCP_PORT}")

        while True:
            # 接受新 Client
            conn, addr = server_sock.accept()
            # 為每位 Client 建立子執行緒
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.start()

if __name__ == '__main__':
    start_server()
