Set WshShell = CreateObject("WScript.Shell")
strCurrentDir = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = strCurrentDir

REM Verifica se existe pythonw no venv, senao usa python normal
strPython = strCurrentDir & "\.venv\Scripts\pythonw.exe"
Set fso = CreateObject("Scripting.FileSystemObject")
If Not fso.FileExists(strPython) Then
    strPython = strCurrentDir & "\.venv\Scripts\python.exe"
End If

strCommand = """" & strPython & """ """ & strCurrentDir & "\supervisor.py"""
WshShell.Run strCommand, 0, False
