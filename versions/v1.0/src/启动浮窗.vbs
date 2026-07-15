Set ws = CreateObject("WScript.Shell")
ws.CurrentDirectory = ws.CurrentDirectory & ""
scriptPath = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName) & "\claude_floating_launcher.py"
ws.Run "pythonw.exe """ & scriptPath & """", 0, False
