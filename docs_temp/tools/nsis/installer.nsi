;--------------------------------
; NSIS include location
;
; DO NOT MODIFY THIS SECTION
;--------------------------------

  !addincludedir "$%COMMON_INSTALLER_DIR%\include"
  !include "template.nsi"

;--------------------------------
; Install/Uninstall Sections
;
; MODIFY THE SECTIONS BELOW
;
; Add your files, shortcuts, and
; registry entries for install
; and uninstall here.
;--------------------------------
; Project Specific code
; Create and Initialize any project
; specific variables/functions/etc.


;--------------------------------
; Installer Section

Section "${product_name} (required)"

  SectionIn RO

  ;Default 7-zip based install
  ;If you find you need customizations, improve the template
  !insertmacro "do_7z_install"

  ;Put any customization here if there are additional things you need to install
  ;CreateShortcut "$SMPROGRAMS\NVIDIA Corporation\${parent_product_name} ${product_name} Readme (html).lnk" "$INSTDIR\index.html" `${exe_cmdline}`

  ;Create uninstaller
  !insertmacro "create_uninstaller"

SectionEnd

;--------------------------------
;Uninstaller Section

Section "Uninstall"

  ;Stop the EXE if it's running so we can fully uninstall
  !insertmacro "delete_tasks"

  ;Put anything here that you want to clean up before the whole install directory is removed
  ;Delete "$SMPROGRAMS\NVIDIA Corporation\${parent_product_name} ${product_name} Readme (html).lnk"

  ;Clean up everything else
  !insertmacro "delete_files_and_registry"

SectionEnd

;--------------------------------
;Extra Directory Page Section

!ifdef show_extra_directory_page
; DO NOT CHANGE FUNCTION NAME
; This function is called from .oninit
; You can do your own initiazation here
Function ExtraDirectoryPageInit


FunctionEnd

; DO NOT CHANGE FUNCTION NAME
; This function is called before the
; Directory Page is displayed.
; You can put a check here to make sure
; your default value is valid, and if so
; you can skip the extra Directory Page.
; $ExtraDirectoryPath is the variable used
; by the DIRECTORY Page. 
Function DirectoryPre

  ${If} $ExtraDirectoryPath == "Some Value"
    ; Skip Page
    Abort
  ${EndIf}

FunctionEnd

; DO NOT CHANGE FUNCTION NAME
; This function is called when the
; user clicks Next on the Directory Page.
; You can check value and Abort if the path
; is invalid.
; $ExtraDirectoryPath is the variable used
; by the DIRECTORY Page.  Use it to get the
; path the user selected.
Function DirectoryLeave
  
  ${If} $ExtraDirectoryPath == "Some Value"
    MessageBox MB_OK "Unknown version of Program."
    Abort
  ${EndIf}

FunctionEnd

; You can add your own functions between
; here and the !endif and call them from
; the functions above.

!endif
