During normal exploration, only the D-Pad and A button are bound to actions. 
Inputs from B, X, Y, L, R, Start and Select are all discarded, requiring navigating through the menu to 
perform any action other than opening the menu. This is an affront to UX design and cannot be allowed to stand.

Inject this to overwrite the old A-button handler at 09a0: `4C 73 FB EA` (should overwrite values `29 0F F0 34`)

Source:
```asm
      jmp $fb73 ; jump to the new code
      nop
```

Inject this at 08c2 to allow L/R to be used: `29 f0 f0` (should overwrite values `29 c0 f0` meaning `and #$f0c0`)

Inject this at 2572 to make the muxer generate values for L and R. 
This function already has a 4-bit muxer loop for the BYST bits, it just needs to be duplicated for the AXLR bits. 
Previously this function returned values 123456 for buttons AXBYST, with this mod it returns 12345678 for AXLRBYST.
```
A5 01 4A 4A 4A 4A 05 00 0A B0 0C E8 E0 00 09 90
F7 EA EA EA
```
Should replace:
```
A5 00 30 13 E8 0A 30 0F E8 A5 01 0A B0 09 E8 E0
0A 00 90 F7
```
Source:
```asm
.x16
      lda $01      ; loads BYST0000
      lsr          ; shift into 0000BYST
      lsr
      lsr
      lsr
      ora $00      ; loads AXLR0000
LOOP: asl
      bcs $17      ; relative jump to a589 assuming base address a572 (where the script starts)
      inx
      db $E0        ; E0 00 09 = cpx #$0009 but this compiler is generating the 8-bit version for some reason 
      db $00 
      db $09
      bcc LOOP
      nop
      nop
      nop
```



Inject the new button handler at 7b73:

Without cheats:
```
290FC900D00622768403802FC901D003
4C168AC902D00622328403801EC903D0
0622BB82038014C904D0034CD889C905
D0062200800380034CA4894CFA89
```

With cheats:
```
290FC900D006227684038042C901D003
4C168AC902D006223284038031C903D0
0622BB82038027C904D0034CD889C905
D006220080038016C906D006A2083B8E
5101C907D00520AFE180034CA4894CFA
89
```
(should overwrite values `FF FF FF FF ...`, compiled with https://www.asm80.com/onepage/asm65816.html)


Source:
```asm
.x16
      and #$0f
A:    cmp #$00
      bne X
      jsr $038476   ; A - Look
      bra CLEANUP
X:    cmp #$01
      bne L
      jmp $008a16   ; X - Inventory
L:    cmp #$02
      bne R
      jsr $038432   ; L - Cast
      bra CLEANUP
R:    cmp #$03
      bne B
      jsr $0382bb   ; R - Attack
      bra CLEANUP
B:    cmp #$04
      bne Y
      jmp $89d8     ; B - Open menu
Y:    cmp #$05
      bne SEL
      jsr $038000   ; Y - Talk
      bra CLEANUP
SEL:  cmp #$06
      bne STA
      ldx #$3b08    ; Select - Cheat: set time to 8:59 am.
      stx $7e0151
      ;lda #$3b
      ;sta $7e0152
STA:  cmp #$07
      bne EXIT
      jsr $e1af     ; Start - Cheat: show minimap (cast peer with no cost)
      bra CLEANUP
EXIT: jmp $89a4     ; Button not handled - return to original function
CLEANUP: jmp $89fa  ; Clean up by closing the menu. This is needed to fix state after Look,Talk,etc. however
                    ; it also re-runs the framerule causing moving NPCs to teleport one step ahead. 

```

