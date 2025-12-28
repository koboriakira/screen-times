#!/usr/bin/osascript

-- アクティブなウィンドウのアプリケーション名を取得
try
    tell application "System Events"
        set active_app to name of first process whose frontmost is true
        return active_app
    end tell
on error
    return "Unknown"
end try
