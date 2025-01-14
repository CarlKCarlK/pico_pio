# PIO Pin Instruction Reference

| Example | Description | Pin Base Used | # of Pins |
|------------|-------------|---------------|-----------|
| `in_(pins, 3)` | Reads 3 bits to ISR | `in_base` | given |
| `out(pins, 4)` | Write 4 bits from OSR | `out_base` | given |
| `set(pins, 0b10101)` | Set pin(s) w/ const bit-pattern | `set_base` | `set_init` |
| `jmp(pin, "label")` | Jump if pin is "1" | `jmp_pin` | 1 |
| `wait(1, pin, 2)` | Wait until pin #2 is 1 (or 0) | `in_base` | index |
| `mov(pins, x)` | Moves data to pins | `out_base` | `out_init` |
| `mov(x, pins)` | Moves data from pins | `in_base` | `in_init` |
| `nop().side(1)` | Side-set pins | `sideset_base` | `sideset_init` |

- All instructions use consecutive pins starting at their respective base pins
