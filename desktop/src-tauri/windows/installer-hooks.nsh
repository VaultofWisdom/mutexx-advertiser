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

; With "delete app data" ticked: take the shared data folder too - configuration,
; keys, campaigns, the account session. The manufacturer folders go only once
; they are empty; RMDir without /r leaves the neighbouring Mutexx products alone.
; Never during an update: an update is an uninstall followed by an install, and
; that must not cost anyone their campaigns.
!macro NSIS_HOOK_POSTUNINSTALL
  ${If} $DeleteAppDataCheckboxState = 1
  ${AndIf} $UpdateMode <> 1
    SetShellVarContext current
    RmDir /r "$LOCALAPPDATA\${MANUFACTURER}\${PRODUCTNAME}"
    RMDir "$LOCALAPPDATA\${MANUFACTURER}"
  ${EndIf}
  RMDir "$PROGRAMFILES64\${MANUFACTURER}"
!macroend
