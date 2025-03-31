.segment "CODE"
loop:
    adc #1
    jmp loop
.segment "RESET_VECTOR"
    .word $8000