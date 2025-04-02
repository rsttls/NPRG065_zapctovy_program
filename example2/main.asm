
.segment "BOOT"
    jmp code


.segment "RODATA"
    msg:
    .asciiz "You are running on pure assembly!!!"

.segment "CODE"
code:
    LDX #0
printLoop:
    LDA msg,X
    BEQ endOfStr
    STA $FF
    LDA #1
    STA $FE
waitForZero:
    LDY $FE
    BNE waitForZero
    INX
    JMP printLoop
endOfStr:
    LDA #$0A
    STA $FF
    LDA #1
    STA $FE
loop:
    INC $200
    INC $220
    INC $240
    INC $260
    INC $280
    JMP loop








.segment "RESET_VECTOR"
    .word $8000