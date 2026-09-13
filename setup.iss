#define MyAppName "Google Antigravity Localizer"
#define MyAppVersion "0.9.0"
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
DisableFinishedPage=yes
OutputBaseFilename=AntigravityLocalizer_v0.9.0
OutputDir=.
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
UninstallDisplayName={#MyAppName} (Русификатор)
VersionInfoVersion=0.9.0.0
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription=Google Antigravity Russian Localization Suite
VersionInfoProductVersion=0.9.0.0
VersionInfoProductName={#MyAppName}
VersionInfoCopyright=Copyright (c) 2026 Antigravity Open Source Community

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Files]
; Localization core files for Antigravity 2.0 Desktop
Source: "resources\app.asar"; DestDir: "{app}\resources"; Flags: ignoreversion; BeforeInstall: BackupOriginalAsar
Source: "resources\web_bundle_ru\*"; DestDir: "{app}\resources\web_bundle_ru"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "translations\ide_strings.json"; DestDir: "{app}\translations"; Flags: ignoreversion
; GUI Localizer
Source: "AntigravityLocalizer.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autodesktop}\Google Antigravity Р СѓСЃРёС„РёРєР°С‚РѕСЂ"; Filename: "{app}\AntigravityLocalizer.exe"

[Code]
var
  ShouldLaunchPatcher: Boolean;

function IsProcessRunning(const ProcName: String): Boolean;
var
  FSWbemLocator: Variant;
  FWMIService: Variant;
  FWbemObjectSet: Variant;
begin
  Result := False;
  try
    FSWbemLocator := CreateOleObject('WbemScripting.SWbemLocator');
    FWMIService := FSWbemLocator.ConnectServer('', 'root\CIMV2', '', '');
    FWbemObjectSet := FWMIService.ExecQuery(
      Format('SELECT ProcessId FROM Win32_Process WHERE Name = "%s"', [ProcName]));
    Result := (FWbemObjectSet.Count > 0);
    FWbemObjectSet := Unassigned;
    FWMIService := Unassigned;
    FSWbemLocator := Unassigned;
  except
    Result := False;
  end;
end;

procedure KillAntigravityProcesses();
var
  ResultCode: Integer;
begin
  Exec('taskkill.exe', '/F /IM Antigravity.exe /T', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  Exec('taskkill.exe', '/F /IM "Antigravity IDE.exe" /T', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  Sleep(800);
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  // Check and warn on pressing "Next" on Directory or Ready page
  if (CurPageID = wpSelectDir) or (CurPageID = wpReady) then
  begin
    if IsProcessRunning('Antigravity.exe') or IsProcessRunning('Antigravity IDE.exe') then
    begin
      if MsgBox('РћР±РЅР°СЂСѓР¶РµРЅС‹ Р·Р°РїСѓС‰РµРЅРЅС‹Рµ РїСЂРѕС†РµСЃСЃС‹ Google Antigravity.' + #13#10 + #13#10 +
                'Р”Р»СЏ Р±РµР·РѕРїР°СЃРЅРѕР№ СѓСЃС‚Р°РЅРѕРІРєРё СЂСѓСЃРёС„РёРєР°С‚РѕСЂР° РїСЂРёР»РѕР¶РµРЅРёРµ РЅРµРѕР±С…РѕРґРёРјРѕ Р·Р°РєСЂС‹С‚СЊ.' + #13#10 +
                'Р—Р°РєСЂС‹С‚СЊ Google Antigravity СЃРµР№С‡Р°СЃ Рё РїСЂРѕРґРѕР»Р¶РёС‚СЊ СѓСЃС‚Р°РЅРѕРІРєСѓ?',
                mbConfirmation, MB_YESNO) = idYes then
      begin
        KillAntigravityProcesses();
        Result := True;
      end
      else
      begin
        Result := False;
      end;
    end;
  end;
end;

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

    // Set flag to launch patcher AFTER installer closes completely
    ShouldLaunchPatcher := True;
  end;
end;

procedure DeinitializeSetup();
var
  ResultCode: Integer;
begin
  // When setup window is completely closed, launch the GUI localizer window
  if ShouldLaunchPatcher then
  begin
    Exec(ExpandConstant('{app}\AntigravityLocalizer.exe'), '', '', SW_SHOW, ewNoWait, ResultCode);
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
