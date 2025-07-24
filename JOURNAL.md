# UAV Project

## July 24 &mdash; Project Start
(I am using this to store my research, so it's a little chaotic)

I've decided I would like to build an RC plane with some kind of long-distance, autonomous capability. Based on my research, the only legal restriction on this project is that it has to be under 55 lbs. I subsequently spent a while researching telemetry and control systems for long-distance projects. It seems like the typical approach is to use some kind of LoRa system like ELRS or OpenLRS for telemetry and control inputs. Another less conventional approach is to use cellular for long-range telemetry and video streaming, combined with a regular RC controller for lower-latency short-range control during takeoff and landing. Arduino offers a [4G modem](https://store-usa.arduino.cc/products/4g-module-global?variant=43479310139599&utm_source=chatgpt.com) with builtin GNSS. Some other projects use a Raspberry Pi with a USB modem.

I think I'd like to avoid using prebuilt flight control components as much as possible, and make this as DIY as I can. 

I spent some time researching the design itself. In terms of airfoils, the AG35 seems to be the most efficient for gliding, but it has poor stall characteristics and requires a large tail to counteract its negative pitching moment, so I think I will go with the SD7037. I also intend to use a V-tail design, where the elevators and rudders are combined. The V-tail is less draggy than a T-tail. The downside is that it requires a longer tail boom, but I intend to do that anyway. The formula for mixing simultaneous pitch and rudder inputs is:

```math
\delta_L = \delta_E + k \cdot \delta_{Ru}\\
\delta_R = \delta_E - k \cdot \delta_{Ru}
```

Where $\delta_L$ and $\delta_R$ represent the left and right ruddervator deflections $\delta_E$ represents the elevator (pitch) input, and $\delta_{Ru}$ represents the rudder (yaw) input. The tail will be a symmetrical airfoil like NACA 0008.

Other than that, I basically spent a bunch of time researching aeronautics, drones, and what I will need to understand for this project.

Time spent: 2.5hr