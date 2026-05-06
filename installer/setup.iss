; Inno Setup — FakturyFZ Import FZ do Comarch XL (CEiM)
; Instalator offline — nie wymaga internetu na serwerze docelowym

#define AppName      "FakturyFZ Import"
#define AppVersion   "1.0"
#define AppPublisher "CEiM"
#define AppExeName   "FakturyFZ.exe"
#define AppDir       "CEIM\FakturyFZ"
#define SourceDir    "..\dist\FakturyFZ"

[Setup]
AppId={{B3A7F2C1-4D9E-4F8A-A2B1-CEiM-FakturyFZ}}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\{#AppDir}
DefaultGroupName={#AppName}
AllowNoIcons=yes
OutputDir=.
OutputBaseFilename=FakturyFZ_Setup_{#AppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "polish"; MessagesFile: "compiler:Languages\Polish.isl"

[Tasks]
Name: "desktopicon"; Description: "Utwórz skrót na pulpicie"; GroupDescription: "Skróty:"; Flags: unchecked

[Files]
; Cały bundle PyInstaller (exe + _internal/ + xl_proxy/ + config/)
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{group}\Odinstaluj {#AppName}"; Filename: "{uninstallexe}"
Name: "{commondesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Uruchom {#AppName}"; Flags: nowait postinstall skipifsilent

[Dirs]
; Katalog raportów — tworzony automatycznie, ale upewniamy się że istnieje
Name: "{app}\reports"
; Konfiguracja — xl_invoice_app.py tworzy config/ automatycznie, ale upewniamy się
Name: "{app}\config"
