During normal exploration, only the D-Pad and A button are bound to actions. 
Inputs from B, X, Y, L, R, Start and Select are all discarded, requiring navigating through the menu to 
perform any action other than opening the menu. This is an affront to UX design and cannot be allowed to stand.

Inject this to overwrite the old A-button handler at 09a0: `4C 73 FB EA` (should overwrite values `29 0F F0 34`)

Source:
```asm
      jmp $fb73 ; jump to the new code
      nop
```

Inject the new code at 7b73:
```
290FC900D007227684034CFA89C901D0
07220080034CFA89C902D0034CD889C9
03D0034C168AC904D00CA9088F51017E
A93B8F52017EC905D0004CA489
```
(should overwrite values `FF FF FF FF ...`, compiled with https://www.asm80.com/onepage/asm65816.html)

Source:
```asm
      and #$0f
A     cmp #$00
      bne X
      jsr $038476 ; B - Look
      jmp $0089fa ; Close menu (required to clean up)
X     cmp #$01
      bne B
      jsr $038000 ; X - Talk
      jmp $0089fa ; Close menu (required to clean up)
B     cmp #$02
      bne Y
      jmp $89d8   ; A - Open menu
Y     cmp #$03
      bne SEL
      jmp $008a16 ; Y - Open Inven. from menu
SEL   cmp #$04
      bne STAR
      ldx #$083b  ; Select - Cheat: set time to 8:59 am.
      stx $7e0151 ; Set hour to 8
      lda #$3b
      sta $7e0152 ; Set minute to 59
STAR  cmp #$05
      bne EXIT
                  ; Start - unbound
EXIT  jmp $89a4   ; Button not handled - return to original function
```
    