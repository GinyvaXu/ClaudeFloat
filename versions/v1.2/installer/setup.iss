; Claude Code 浮窗 — Inno Setup 安装脚本
; 编译: "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" setup.iss

#define MyAppName "Claude Code 浮窗"
#define MyAppVersion "1.1"
#define MyAppPublisher "Claude Code"
#define MyAppExeName "ClaudeFloat.exe"
#define MyAppURL "https://claude.ai"

[Setup]
AppId={{CB80F83A-EE67-491B-B6AF-8AFF048ECF40}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
VersionInfoVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
DefaultDirName={localappdata}\ClaudeFloat
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=.
OutputBaseFilename=ClaudeFloat_Setup_v{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
WizardSizePercent=120
UninstallDisplayName={#MyAppName}
UninstallDisplayIcon={app}\资源素材\claude_icon.ico
PrivilegesRequired=lowest
SetupIconFile=..\..\资源素材\claude_icon.ico
; 安装程序窗口标题
SetupMutex=ClaudeFloatSetup

[Languages]
Name: "chinesesimp"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "附加快捷方式:"
Name: "startup"; Description: "开机自动启动 Claude Code 浮窗"; GroupDescription: "启动选项:"

[Files]
Source: "..\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\资源素材\claude_icon.ico"; DestDir: "{app}\资源素材"; Flags: ignoreversion
Source: "..\..\资源素材\claude_icon.png"; DestDir: "{app}\资源素材"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; \
    IconFilename: "{app}\资源素材\claude_icon.ico"; \
    Comment: "快速启动 Claude Code 的桌面浮窗"
Name: "{group}\卸载 Claude Code 浮窗"; Filename: "{uninstallexe}"
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; \
    IconFilename: "{app}\资源素材\claude_icon.ico"; \
    Tasks: desktopicon
Name: "{userstartup}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; \
    IconFilename: "{app}\资源素材\claude_icon.ico"; \
    Tasks: startup

[Run]
Filename: "{app}\{#MyAppExeName}"; \
    Description: "启动 Claude Code 浮窗"; \
    Flags: nowait postinstall skipifsilent unchecked

[UninstallRun]
Filename: "taskkill"; Parameters: "/f /im {#MyAppExeName}"; Flags: runhidden

[Code]
// 安装完成后的自定义消息
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // 安装完成后自动清理
  end;
end;
