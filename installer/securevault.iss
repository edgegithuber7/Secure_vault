; SecureVault Windows Installer  (Inno Setup 6)
; Download Inno Setup: https://jrsoftware.org/isinfo.php
; Run:  iscc installer\securevault.iss

[Setup]
AppName=SecureVault
AppVersion=1.0.0
AppPublisher=SecureVault
AppPublisherURL=https://github.com/edgegithuber7/Secure_vault
AppSupportURL=https://github.com/edgegithuber7/Secure_vault/issues
DefaultDirName={autopf}\SecureVault
DefaultGroupName=SecureVault
OutputDir=..\dist
OutputBaseFilename=SecureVault-Setup-1.0.0
SetupIconFile=..\assets\icon.ico
UninstallDisplayIcon={app}\SecureVault.exe
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
MinVersion=10.0
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
Source: "..\dist\SecureVault\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\SecureVault";               Filename: "{app}\SecureVault.exe"
Name: "{group}\Uninstall SecureVault";     Filename: "{uninstallexe}"
Name: "{commondesktop}\SecureVault";       Filename: "{app}\SecureVault.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\SecureVault.exe"; Description: "&Launch SecureVault now"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Leave user vault data intact — stored in %APPDATA%\SecureVault, not in {app}
