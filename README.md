# TCP／UDP 多人猜數字聊天室

Python socket + Tkinter 的多人連線小遊戲。TCP 負責登入、猜數字與聊天室訊息；UDP broadcast 用於遊戲開始與勝者公告。伺服器以 thread-per-client 模式處理連線，並以 lock 保護共享 client 清單。

## 架構

```mermaid
flowchart LR
    C1[Client 1 GUI] <-->|TCP: LOGIN / GUESS / CHAT| S[Multi-threaded server]
    C2[Client 2 GUI] <-->|TCP| S
    S -->|UDP broadcast| C1
    S -->|UDP broadcast| C2
```

## 執行

伺服器：

```powershell
$env:CHAT_TCP_PORT = "12345"
$env:CHAT_UDP_PORT = "54321"
python server.py
```

在兩個終端啟動 client：

```powershell
$env:CHAT_SERVER_IP = "127.0.0.1"
python client.py
```

可設定 `CHAT_HOST`、`CHAT_SERVER_IP`、`CHAT_BROADCAST_IP`、`CHAT_TCP_PORT`、`CHAT_UDP_PORT`。

## 協定與限制

目前應用層協定使用 `LOGIN:`、`GUESS:`、`CHAT:` 前綴。TCP 是 byte stream，正式環境仍應加入換行或 length-prefix framing，以處理黏包／拆包；同時應補上關閉視窗、重複暱稱與異常斷線測試。
