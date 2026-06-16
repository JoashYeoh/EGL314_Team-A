# System Architecure Documentation
In this document, you will find explaination of the software pipeline in this project.


## Overarching Data Flow
```Mermaid
flowchart TD
    A[AI Thinker UWB Kit] -->|UART frame via Serial| B[Sensor Pi -> uart.py]
    B -->|Distances via OSC| C[Game Pi -> game.py]
    C -->|Distances go through| D(Trilateration, 
    Kalman Filtering, 
    Zone Detection, 
    Game Logic)
    C -->|Commands via OSC| E[Multiplay]
```


## UART Frame via Serial
```Mermaid
flowchart LR
    A[AI Thinker UWB Kit] -->|UART frame via Serial| B[Sensor Pi -> uart.py]
```

When `uart.py` is running on the **Senor Pi**, it is actively reading **raw UART frames** from the **BU03-Kit** via the serial port.


## Distances via OSC  
```Mermaid
flowchart LR
    B[Sensor Pi -> uart.py] -->|Distances via OSC| C[Game Pi -> game.py]
```
`uart.py` parses them into 12 distances (m) per tag *(x and y distance per anchor from tag)*, applies per-anchor calibration offsets, then **broadcasts each frame over OSC** to the **Game Pi** running game.py.





