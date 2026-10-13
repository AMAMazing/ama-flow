Set fso = CreateObject("Scripting.FileSystemObject")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)

Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = scriptDir

' Run pythonw.exe silently with 0 window style (completely hidden background process)
WshShell.Run "pythonw.exe main.py", 0, False