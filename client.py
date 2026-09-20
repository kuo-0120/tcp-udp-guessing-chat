"""
簡易猜數字聊天室客戶端程式
---------------------------------
功能：
1. 使用 TCP 連線至伺服器，支援猜數字與聊天室功能。
2. 使用 UDP 接收廣播訊息。
3. 提供 GUI 介面讓使用者輸入猜測數字或聊天室訊息。
"""

import os
import socket
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext, simpledialog

# 設定伺服器 IP 和端口
SERVER_IP = os.getenv('CHAT_SERVER_IP', '127.0.0.1')
TCP_PORT = int(os.getenv('CHAT_TCP_PORT', '12345'))
UDP_PORT = int(os.getenv('CHAT_UDP_PORT', '54321'))

class GuessClient:
    def __init__(self, master, nickname):
        #初始化 GUI 並建立 TCP 連線
        self.master = master  # 主視窗
        self.nickname = nickname  # 使用者暱稱
        master.title(f"{nickname} 的猜數字聊天室")  # 設定視窗標題
        master.geometry("500x500")  # 設定視窗大小
        master.resizable(False, False)  # 禁止調整視窗大小

        # 主框架
        frame = tk.Frame(master, padx=10, pady=10)
        frame.pack(expand=True)

        # 猜數字區
        guess_frame = tk.LabelFrame(frame, text="猜數字區", padx=10, pady=10)
        guess_frame.pack(fill="x", pady=5)

        tk.Label(guess_frame, text="請輸入 1~100 的整數：").pack(anchor="w")
        guess_input_frame = tk.Frame(guess_frame)
        guess_input_frame.pack(fill="x")

        self.guess_entry = tk.Entry(guess_input_frame)  # 輸入框
        self.guess_entry.pack(side="left", fill="x", expand=True)
        self.guess_entry.bind("<Return>", lambda e: self.send_guess())  # 按下 Enter 發送猜測

        self.guess_button = tk.Button(guess_input_frame, text="送出猜測", command=self.send_guess)  # 按鈕
        self.guess_button.pack(side="left", padx=5)

        # 聊天區
        chat_frame = tk.LabelFrame(frame, text="聊天室", padx=10, pady=10)
        chat_frame.pack(fill="both", expand=True, pady=5)

        self.chat_display = scrolledtext.ScrolledText(chat_frame, height=12, state="disabled")  # 聊天顯示區
        self.chat_display.pack(fill="both", expand=True)

        chat_input_frame = tk.Frame(chat_frame)
        chat_input_frame.pack(fill="x", pady=5)

        self.chat_entry = tk.Entry(chat_input_frame)  # 聊天輸入框
        self.chat_entry.pack(side="left", fill="x", expand=True)
        self.chat_entry.bind("<Return>", lambda e: self.send_chat())  # 按下 Enter 發送訊息

        self.chat_button = tk.Button(chat_input_frame, text="發送聊天", command=self.send_chat)  # 按鈕
        self.chat_button.pack(side="left", padx=5)

        # 建立 TCP 連線
        self.tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_sock.connect((SERVER_IP, TCP_PORT))
        self.tcp_sock.sendall(f"LOGIN:{self.nickname}".encode())  # 登入訊息

        # 啟動接收資料的執行緒
        threading.Thread(target=self.tcp_listener, daemon=True).start()
        threading.Thread(target=self.udp_listener, daemon=True).start()

    def send_guess(self):
        #發送猜測數字的訊息
        guess = self.guess_entry.get().strip()  # 取得輸入的猜測數字
        if guess:
            self.tcp_sock.sendall(f"GUESS:{guess}".encode())  # 發送猜測
            self.guess_entry.delete(0, tk.END)  # 清空輸入框

    def send_chat(self):
        #發送聊天訊息
        msg = self.chat_entry.get().strip()  # 取得聊天訊息
        if msg:
            self.tcp_sock.sendall(f"CHAT:{msg}".encode())  # 發送聊天訊息
            self.chat_entry.delete(0, tk.END)  # 清空輸入框

    def tcp_listener(self):
        #接收來自伺服器的 TCP 資料
        while True:
            try:
                data = self.tcp_sock.recv(1024)
                if not data:
                    break
                msg = data.decode()
                self.append_message(msg)  # 顯示伺服器回傳的訊息
            except:
                break

    def udp_listener(self):
        #監聽 UDP 廣播訊息
        udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        udp_sock.bind(('', UDP_PORT))  # 綁定 UDP 端口
        while True:
            try:
                data, _ = udp_sock.recvfrom(1024)  # 接收 UDP 廣播訊息
                messagebox.showinfo("廣播訊息", data.decode())  # 顯示訊息
            except:
                break

    def append_message(self, msg):
        #將訊息顯示在聊天區域
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, msg + '\n')  # 插入新訊息
        self.chat_display.config(state=tk.DISABLED)  # 設為只讀模式
        self.chat_display.yview(tk.END)  # 滾動到最底部

if __name__ == "__main__":
    # 啟動 GUI 程式
    root = tk.Tk()
    root.withdraw()  # 隱藏主視窗
    nickname = simpledialog.askstring("登入", "請輸入你的暱稱：")  # 請使用者輸入暱稱
    if nickname:
        root.deiconify()  # 顯示主視窗
        app = GuessClient(root, nickname)  # 建立客戶端物件
        root.mainloop()  # 啟動主迴圈
    else:
        messagebox.showwarning("暱稱為空", "請輸入暱稱才能進入遊戲。")  # 提示未輸入暱稱
        root.destroy()  # 關閉程式
