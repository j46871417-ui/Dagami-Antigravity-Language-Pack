#define MyAppName "Google Antigravity Localizer"
#define MyAppVersion "0.0.7"
#define MyAppPublisher "Antigravity Open Source Community"
#define MyAppURL "https://github.com/j46871417-ui/Antigravity-Localizer"

[Setup]
AppId={{D8156170-D57B-4E3E-8153-62529BAA245E}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={localappdata}\Programs\antigravity
DisableDirPage=no
DirExistsWarning=no
DisableProgramGroupPage=yes
OutputBaseFilename=AntigravityLocalizer_v0.0.7
OutputDir=.
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
CloseApplications=yes
CloseApplicationsFilter=Antigravity*.exe
UninstallDisplayName={#MyAppName} (Русификатор)
VersionInfoVersion=0.0.7.0
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription=Google Antigravity Russian Localization Suite
VersionInfoProductVersion=0.0.7.0
VersionInfoProductName={#MyAppName}
VersionInfoCopyright=Copyright (c) 2026 Antigravity Open Source Community

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Files]
; Localization core files for Antigravity 2.0 Desktop
Source: "resources\app.asar"; DestDir: "{app}\resources"; Flags: ignoreversion; BeforeInstall: BackupOriginalAsar
Source: "resources\web_bundle_ru\*"; DestDir: "{app}\resources\web_bundle_ru"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "translations\ide_strings.json"; DestDir: "{app}\translations"; Flags: ignoreversion

[Code]
procedure BackupOriginalAsar();
var
  TargetAsar: String;
  BackupAsar: String;
begin
  TargetAsar := ExpandConstant('{app}\resources\app.asar');
  BackupAsar := ExpandConstant('{app}\resources\app.asar.original_backup');
  if FileExists(TargetAsar) and not FileExists(BackupAsar) then
  begin
    CopyFile(TargetAsar, BackupAsar, False);
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  IdePath: String;
  PkgJsonPath: String;
  PkgBackup: String;
begin
  if CurStep = ssPostInstall then
  begin
    // Check if Antigravity IDE is installed and backup package.json
    IdePath := ExpandConstant('{localappdata}\Programs\Antigravity IDE');
    if not DirExists(IdePath) then
      IdePath := ExpandConstant('{commonpf}\Antigravity IDE');
    
    if DirExists(IdePath) then
    begin
      PkgJsonPath := IdePath + '\resources\app\extensions\antigravity\package.json';
      PkgBackup := PkgJsonPath + '.bak.original';
      if FileExists(PkgJsonPath) and not FileExists(PkgBackup) then
      begin
        CopyFile(PkgJsonPath, PkgBackup, False);
      end;
    end;
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  TargetAsar: String;
  BackupAsar: String;
  WebBundleDir: String;
  IdePath: String;
  PkgJsonPath: String;
  PkgBackup: String;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    // Restore original Desktop app.asar
    TargetAsar := ExpandConstant('{app}\resources\app.asar');
    BackupAsar := ExpandConstant('{app}\resources\app.asar.original_backup');
    if FileExists(BackupAsar) then
    begin
      CopyFile(BackupAsar, TargetAsar, False);
      DeleteFile(BackupAsar);
    end;
    
    // Remove web_bundle_ru
    WebBundleDir := ExpandConstant('{app}\resources\web_bundle_ru');
    if DirExists(WebBundleDir) then
    begin
      DelTree(WebBundleDir, True, True, True);
    end;

    // Restore IDE if needed
    IdePath := ExpandConstant('{localappdata}\Programs\Antigravity IDE');
    if not DirExists(IdePath) then
      IdePath := ExpandConstant('{commonpf}\Antigravity IDE');
    if DirExists(IdePath) then
    begin
      PkgJsonPath := IdePath + '\resources\app\extensions\antigravity\package.json';
      PkgBackup := PkgJsonPath + '.bak.original';
      if FileExists(PkgBackup) then
      begin
        CopyFile(PkgBackup, PkgJsonPath, False);
        DeleteFile(PkgBackup);
      end;
    end;
  end;
end;
