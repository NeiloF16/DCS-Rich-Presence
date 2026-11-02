#define MyAppName "DCS World Rich Presence"
#define MyAppVersion "1.0.0"
#define MyAppExeName "DCSRichPresence.exe"

[Setup]
AppId={{79C9D02D-1B14-4F61-BDEE-93197A8C7863}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher=Neilo Community
DefaultDirName={localappdata}\Programs\DCSRichPresence
DefaultGroupName=DCS World Rich Presence
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\release
OutputBaseFilename=DCS-Rich-Presence-Setup-v{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
SetupIconFile=..\assets\app.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
MinVersion=10.0
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=yes
RestartApplications=no
VersionInfoVersion=1.0.0.0
VersionInfoDescription=DCS World Rich Presence Community Installer
VersionInfoCompany=Neilo Community
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion={#MyAppVersion}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Files]
Source: "..\dist\DCSRichPresence\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\DCS World Rich Presence"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall DCS World Rich Presence"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Configure DCS Rich Presence / Configurer DCS Rich Presence"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "{app}\{#MyAppExeName}"; Parameters: "--uninstall-clean"; Flags: runhidden waituntilterminated
