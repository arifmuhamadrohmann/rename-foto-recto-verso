#define MyAppName "Rename Foto RECTO VERSO"
#define MyAppVersion "1.0.3"
#define MyAppPublisher "Aip - arif.muhamadrohman@gmail.com"
#define MyAppExeName "RenameFotoRectoVerso.exe"

[Setup]
AppId={{D5E8C4DB-475F-4F56-A34E-9CA06A4DB0C5}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\RenameFotoRectoVerso
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=installer
OutputBaseFilename=Setup-RenameFotoRectoVerso-{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
UninstallDisplayIcon={app}\{#MyAppExeName}
VersionInfoCompany=Aip
VersionInfoCopyright=Copyright © 2026 Aip - arif.muhamadrohman@gmail.com
VersionInfoDescription=Installer Rename Foto RECTO VERSO
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion=1.0.3
VersionInfoVersion=1.0.3.0

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Buat ikon di Desktop"; GroupDescription: "Ikon tambahan:"; Flags: unchecked

[Files]
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Jalankan {#MyAppName}"; Flags: nowait postinstall skipifsilent
