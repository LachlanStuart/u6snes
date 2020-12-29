# Camp anywhere

The camping function is at `b64d` (loaded into memory at `$1b64d`). It does a number of checks:
* If `$a3 & 0x40 == 0x40` (on a boat?), camping fails with a "Not here!" message
* If `$a2 != 0` (indoors), camping fails with "Not inside the building!"
* If `$75 != 0` (in sewer?), the next next check about being in town is skipped
* If subroutine `$01b961` sets the C flag, it fails because Avatar is in town
* If subroutine `$01b809` sets the C flag, it fails because foes are nearby
* If subroutine `$01b839` sets the C flag, it fails because there's not enough room
    * This subroutine also chooses appropriate locations for the party, so if skipped, they move all over the place

Overriding these checks:
* Recommended: To camp anywhere where there's enough room: at `b651` change `A9 9B` to `80 1c` (`jmp $b66f`)
* To skip all checks entirely (can be glitchy): at `b651` change `A9 9B` to `80 21` (`jmp $b674`)
* To disable the "Not here!" case: at `b655` change `70 06` (`bvs $b65d`) to `EA EA` (`nop nop`)
* To allow camping indoors: at `b659` change `F0 06` (`beq $b661`) to `80 06` (`bra $b661`)
* To allow camping in town: at `b665` change `20 61 b9` (`jsr $01b961`) to `EA EA EA` (`nop nop nop`)
* To allow camping with foes near: at `b66a` change `20 09 B8` (`jsr $01b809`) to `EA EA EA` (`nop nop nop`)
* To allow camping when there's not enough room: at `b66f` change `20 39 B8` (`jsr $01b839`) to `EA EA EA` (`nop nop nop`)


