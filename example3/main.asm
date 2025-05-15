.import _entry

.segment "BOOT"
    jsr _entry
    LDA #127
    STA $FE
    
.segment "RESET_VECTOR"
    .word $8000