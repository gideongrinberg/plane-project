---
title: "UAV Project"
author: "Gideon Grinberg"
description: "A long-range semi-autonomous UAV"
created_at: "2025-07-24"
---

# UAV Project

Total time spent as of July 26: 11 hours and 0 minutes

## July 24 &mdash; Project Start
(I am using this to store my research, so it's a little chaotic)

I've decided I would like to build an RC plane with some kind of long-distance, autonomous capability. Based on my research, the only legal restriction on this project is that it has to be under 55 lbs. I subsequently spent a while researching telemetry and control systems for long-distance projects. It seems like the typical approach is to use some kind of LoRa system like ELRS or OpenLRS for telemetry and control inputs. Another less conventional approach is to use cellular for long-range telemetry and video streaming, combined with a regular RC controller for lower-latency short-range control during takeoff and landing. Arduino offers a [4G modem](https://store-usa.arduino.cc/products/4g-module-global?variant=43479310139599) with builtin GNSS. Some other projects use a Raspberry Pi with a USB modem.

I think I'd like to avoid using prebuilt flight control components as much as possible, and make this as DIY as I can. 

I spent some time researching the design itself. In terms of airfoils, the AG35 seems to be the most efficient for gliding, but it has poor stall characteristics and requires a large tail to counteract its negative pitching moment, so I think I will go with the SD7037. I also intend to use a V-tail design, where the elevators and rudders are combined. The V-tail is less draggy than a T-tail. The downside is that it requires a longer tail boom, but I intend to do that anyway. The formula for mixing simultaneous pitch and rudder inputs is:

```math
\delta_L = \delta_E + k \cdot \delta_{Ru}\\
\delta_R = \delta_E - k \cdot \delta_{Ru}
```

Where $\delta_L$ and $\delta_R$ represent the left and right ruddervator deflections $\delta_E$ represents the elevator (pitch) input, and $\delta_{Ru}$ represents the rudder (yaw) input. The tail will be a symmetrical airfoil like NACA 0008.

Other than that, I basically spent a bunch of time researching aeronautics, drones, and what I will need to understand for this project.

Time spent: 2.5hr

## July 25 &mdash; Start Designing 

I found a cool python tool called AeroSandbox that enables users to design and optimize aerospace vehicles, and I'm using it to prototype my vehicle. So far, I've sketched out the basic design in ASB. I've also used it to produce some basic graphs of various flight characteristics, which should help me catch issues in the design. One thing I want to look at further is the trim curve, which had some apparent issues I don't have time to investigate. I also plan to use ASB to estimate some of the basic characteristics of my design, such as endurance. The information I've gained from the ASB design will help me select parts for my drone. You can see some of the output in ./design/design.md. That file is generated from design.qmd using Quarto (basically RMarkdown for Python). The main.py code is basically identical to the Quarto code less the graphs. 

Link to [the current design document](https://github.com/gideongrinberg/plane-project/blob/main/design/design.md).

Time spent: 4hr (roughly 1 hour on researching and 3 hours tweaking the ASB design)

## July 26 &mdash; Continued Design Work

### Morning – Flight Control Edits
I found an issue in the design of the tail that would have introduced instability and cause the aircraft to pitch uncontrollably up in flight. By changing the dimensions of the tail, I was able to ensure that the aircraft will be more stable in flight. In particular, it should be stable in cruise, although it is still unstable around very low angles of attack, so I will need to be careful while landing it. Additionally, I optimized the center of gravity by shifting the nose cone back a bit. I have begun to identify my materials. I will use EPS foam for the wings with a 6mm carbon fiber spar down the middle. I will need to purchase a foam cutter, and will need to make or order templates for the airfoil.

Time spent: 1hr

### Afternoon – Wing Design and Templates

I decided to start my design with the wings. The wings will be made of foam and cut using a hot wire. The main wings will be connected by one spar, which attaches the fuselage. The control surface servos will be mounted in the wing and wired through the spar. I will cut the wings as two separate pieces then create the hinges for the control surfaces. I've been researching various hinge constructions and they all seem simple. Mounting the v-tail will require more thought – I will either put the servos on the boom in the back, or in the fuselage and run a long pushrod down the side. I will decide once I have figured out the issue of weight. 

Using my python script (and after a lot more effort than expected), I was able to export DXF templates for the wings and tail airfoils. I added slots for the wing spars and marked the control surfaces. I will need to make some kind of jig for the V-tail. I will also need to add the wing incidence angle to the templates to ensure proper AoA.

(Edit: I forgot to add this, but you can view the resulting DXF templates in schematics/. The code is still in design/.)

Time spent: 3.5hr (a mix of researching and working on the templates. i know it doesn't seem like i accomplished a lot, but the templates were very difficult to debug. maybe cad is a better approach in the future.)
