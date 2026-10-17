#define MyAppName "Dagami Antigravity Language Pack"
#define MyAppVersion "1.2.0"
[Setup]
SetupIconFile=assets\app-icon.ico
AppId={{D8156170-D57B-4E3E-8153-62529BAA245E}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
DefaultDirName={localappdata}\Programs\DagamiLanguagePack
DefaultGroupName=Dagami Language Pack
PrivilegesRequired=lowest
OutputBaseFilename=DagamiLanguagePack-Setup
OutputDir=release_dist
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\AntigravityLocalizer.exe
[Files]
#ifdef FolderBuild
Source: "dist\AntigravityLocalizer\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
#else
Source: "AntigravityLocalizer.exe"; DestDir: "{app}"; Flags: ignoreversion
#endif
Source: "LICENSE"; DestDir: "{app}"; Flags: ignoreversion
[Icons]
Name: "{group}\Dagami Language Pack"; Filename: "{app}\AntigravityLocalizer.exe"; Parameters: "--gui"
[Run]
Filename: "{app}\AntigravityLocalizer.exe"; Parameters: "--gui"; Description: "Открыть"; Flags: nowait postinstall skipifsilent
