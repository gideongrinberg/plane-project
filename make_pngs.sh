#! /usr/bin/env bash
find . -name "*.dxf" | rush "./dxf2png {} ./{:}.png"