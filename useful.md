# Flowchart for Pin Conditions in PIO

```mermaid
graph TD
    A[Start] --> B[Wait for pin to go high]
    B --> C[Load max echo wait in Y]
    C --> D{Is pin high?}
    D --> E[Echo Active]
    D --> F[Measurement Complete]
    E --> G[Decrement Y]
    G --> H{Loop or Timeout?}
    H --> E[Echo Active]
    H --> F[Measurement Complete]

    classDef active fill:#a2d2ff,stroke:#0077b6,stroke-width:2px;
    classDef complete fill:#ffc8dd,stroke:#d00000,stroke-width:2px;
