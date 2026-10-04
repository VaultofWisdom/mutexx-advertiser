; Mutexx Advertiser - additions to the NSIS installer.
;
;   Program   C:\Program Files\Mutexx Production\Mutexx Advertiser
;   Data      %LOCALAPPDATA%\Mutexx Production\Mutexx Advertiser
;   Start     Programs\Mutexx Production\Mutexx Advertiser.lnk
;
; The Advertiser never had a per-user installation, so there is nothing to
; migrate on install. Only uninstalling needs help: Tauri's own clean-up step
; knows %LOCALAPPDATA%\<identifier>, where nothing of ours lives.

!macro NSIS_HOOK_PREINSTALL
!macroend

; The start menu entry, on every install AND every update.
;
; Tauri's template creates it on a fresh install only and skips it in update mode
; on purpose - it assumes the first install made it. When that one did not (on
; 04.10.2026 the first installation of 0.5.0 ended up without any entry), no update
; would ever bring it back. So it is checked here, after the template's own step,
; and created when missing. /NS ("no shortcuts") is still honoured.
!macro NSIS_HOOK_POSTINSTALL
  ${If} $NoShortcutMode <> 1
    !if "${STARTMENUFOLDER}" != ""
      ${IfNot} ${FileExists} "$SMPROGRAMS\${STARTMENUFOLDER}\${PRODUCTNAME}.lnk"
        CreateDirectory "$SMPROGRAMS\${STARTMENUFOLDER}"
        CreateShortcut "$SMPROGRAMS\${STARTMENUFOLDER}\${PRODUCTNAME}.lnk" "$INSTDIR\${MAINBINARYNAME}.exe"
        !insertmacro SetLnkAppUserModelId "$SMPROGRAMS\${STARTMENUFOLDER}\${PRODUCTNAME}.lnk"
      ${EndIf}
    !endif
  ${EndIf}
!macroend

; With "delete app data" ticked: take the shared data folder too - configuration,
; keys, campaigns, the account session. The manufacturer folders go only once
; they are empty; RMDir without /r leaves the neighbouring Mutexx products alone.
; Never during an update: an update is an uninstall followed by an install, and
; that must not cost anyone their campaigns.
!macro NSIS_HOOK_POSTUNINSTALL
  ; The entry the install hook may have made, and the group once it is empty -
  ; never during an update, which uninstalls first and installs right after.
  ${If} $UpdateMode <> 1
    !if "${STARTMENUFOLDER}" != ""
      Delete "$SMPROGRAMS\${STARTMENUFOLDER}\${PRODUCTNAME}.lnk"
      RMDir "$SMPROGRAMS\${STARTMENUFOLDER}"
    !endif
  ${EndIf}
  ${If} $DeleteAppDataCheckboxState = 1
  ${AndIf} $UpdateMode <> 1
    SetShellVarContext current
    RmDir /r "$LOCALAPPDATA\${MANUFACTURER}\${PRODUCTNAME}"
    RMDir "$LOCALAPPDATA\${MANUFACTURER}"
  ${EndIf}
  RMDir "$PROGRAMFILES64\${MANUFACTURER}"
!macroend
