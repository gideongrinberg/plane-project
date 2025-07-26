"""
UAV design and optimization
Author: Gideon Grinberg
Date: July 25, 2025
"""
import pathlib
import aerosandbox as asb
import aerosandbox.numpy as np
import aerosandbox.tools.pretty_plots as p
import matplotlib.pyplot as plt

# Optimization setup and variables
opti = asb.Opti()

battery_energy_Wh = 30  # fixed
battery_energy_J = battery_energy_Wh * 3600  # 108 kJ
design_mass_TOGW = 0.700  # kg

velocity = opti.variable(init_guess=15, lower_bound=8, upper_bound=25)  # m/s
alpha_deg = opti.variable(init_guess=4, lower_bound=-5, upper_bound=10)  # deg
op_point = asb.OperatingPoint(velocity=velocity, alpha=alpha_deg)

# Geometry
# Wing
span = 1.50  # m  (fixed)
root_chord = opti.variable(init_guess=0.24, lower_bound=0.15, upper_bound=0.30)
taper_ratio = 0.5
tip_chord = root_chord * taper_ratio
sweep_LE = 0  # straight wing

airfoil_wing = asb.Airfoil(name="sd7037")
half_span = span / 2
wing = asb.Wing(
    name="Main Wing",
    symmetric=True,
    xsecs=[
        # Root section positioned at pod's widest point (~x=0.02 m)
        asb.WingXSec(
            xyz_le=[0.02, 0, 0],  # Moved wing rearward to pod max radius
            chord=root_chord,
            airfoil=airfoil_wing
        ),
        asb.WingXSec(
            xyz_le=[0.02 + sweep_LE, half_span, 0],
            chord=tip_chord,
            airfoil=airfoil_wing
        ),
    ],
)

# vtail
tail_arm = opti.variable(
    init_guess=0.60, lower_bound=0.45, upper_bound=0.75
)
v_dihedral_deg = 35

airfoil_tail = asb.Airfoil(name="naca0008")
S_h_proj = 0.042
chord_tail_root = 0.10
span_tail_half = (
    np.sqrt(S_h_proj / (2 * 0.6 * np.cos(np.radians(v_dihedral_deg)) ** 2)) * 2
)

def vrot(xyz):
    R = np.rotation_matrix_3D(angle=np.radians(v_dihedral_deg), axis="X")
    return R @ np.array(xyz)

v_tail = asb.Wing(
    name="V-Tail",
    symmetric=True,
    xsecs=[
        asb.WingXSec(
            xyz_le=vrot([tail_arm, 0, 0]), chord=chord_tail_root, airfoil=airfoil_tail
        ),
        asb.WingXSec(
            xyz_le=vrot([tail_arm, span_tail_half / 2, 0]),
            chord=chord_tail_root * 0.5,
            airfoil=airfoil_tail,
        ),
    ],
)

# Fuselage design
pod_radius = 0.03  # 60 mm max diameter
boom_radius = 0.007  # 14 mm dia carbon tube

# Optimize fuselage nose cone
nose_radius = opti.variable(init_guess=0.03, lower_bound=0.02, upper_bound=0.05)
mid_radius  = opti.variable(init_guess=0.03, lower_bound=0.02, upper_bound=0.05)
aft_radius  = opti.variable(init_guess=0.015, lower_bound=0.01, upper_bound=0.03)
fuselage_pod = asb.Fuselage(
    xsecs = [
        asb.FuselageXSec(xyz_c=[-0.22,0,0], radius=0.0),
        asb.FuselageXSec(xyz_c=[-0.20,0,0], radius=nose_radius),
        asb.FuselageXSec(xyz_c=[ 0.02,0,0], radius=mid_radius),
        asb.FuselageXSec(xyz_c=[ 0.07,0,0], radius=aft_radius),
    ]
)

min_internal_vol = 0.0005 # ~30 cubic inches
opti.subject_to(fuselage_pod.volume() >= min_internal_vol)

fuselage_boom = asb.Fuselage(
    name="Tail Boom",
    xsecs=[
        asb.FuselageXSec(xyz_c=[0.07,     0, 0], radius=boom_radius),
        asb.FuselageXSec(xyz_c=[tail_arm, 0, 0], radius=boom_radius),
    ],
)

airplane = asb.Airplane(
    name="700 g Endurance UAV", wings=[wing, v_tail], fuselages=[fuselage_pod, fuselage_boom]
)

# Mass properties
mp_struct = asb.mass_properties_from_radius_of_gyration(
    mass=0.200, x_cg=0.05
)
mp_power = asb.mass_properties_from_radius_of_gyration(
    mass=0.055, x_cg=-0.05
)
mp_batt = asb.mass_properties_from_radius_of_gyration(
    mass=0.280, x_cg=-0.02
)
mp_elec = asb.mass_properties_from_radius_of_gyration(
    mass=0.045, x_cg=0.00
)
mp_tail = asb.mass_properties_from_radius_of_gyration(
    mass=0.095, x_cg=tail_arm
)
mp_glue = (mp_struct + mp_tail) * 0.08

mass_tot = mp_struct + mp_power + mp_batt + mp_elec + mp_tail + mp_glue
W = design_mass_TOGW * 9.81  # N (fixed)

# Aero analysis
aero = asb.AeroBuildup(
    airplane=airplane, op_point=op_point, xyz_ref=mass_tot.xyz_cg
).run_with_stability_derivatives(
    alpha=True,
    beta=False,
    p=False,
    q=False,
    r=False
)

# Constraints
opti.subject_to(
    [
        aero["L"] >= W,
        aero["Cm"] == 0,
    ]
)

static_margin = (aero["x_np"] - mass_tot.x_cg) / wing.mean_aerodynamic_chord()
opti.subject_to(static_margin >= 0.05)

opti.subject_to(
    [
        tip_chord >= 0.06,
        tail_arm <= 0.75,
    ]
)

prop_efficiency_est = 0.67
power_required = aero["D"] * velocity / prop_efficiency_est
opti.minimize(power_required)

try:
    sol = opti.solve()
except RuntimeError:
    sol = opti.debug

s = lambda x: sol.value(x)
endurance_sec = battery_energy_J / s(power_required)

# Make outputs
outdir = pathlib.Path(__file__).parent / "figures"
outdir.mkdir(exist_ok=True)

# # Geometry
airplane_sol = sol(airplane)
airplane_sol.draw_three_view(show=False)
p.show_plot(tight_layout=False, savefig="figures/three_view.png")

# Weight budget
mass_components = {
    "Structure": s(mp_struct.mass),
    "Motor + Mount": s(mp_power.mass),
    "Battery": s(mp_batt.mass),
    "Electronics": s(mp_elec.mass),
    "Tail & Boom": s(mp_tail.mass),
}

mp_glue = sum(mass_components.values()) * 0.08
mass_components["Glue"] = mp_glue

labels = list(mass_components.keys())
values = [v*1000 for v in list(mass_components.values())] # convert to g

def make_autopct(values, suffix="g"):
    def autopct(pct):
        total = sum(values)
        val = int(round(pct * total / 100.0))
        return f"{val}{suffix}"
    return autopct

plt.figure()
plt.pie(values, labels=labels, autopct=make_autopct(values, "g"))
plt.show()


print("==== SOLUTION SUMMARY ====")
print(f"Cruise   : {s(velocity):.2f} m/s  @ α {s(alpha_deg):.1f}°")
print(f"Drag     : {s(aero['D']):.2f} N")
print(f"PowerReq : {s(power_required):.1f} W (est.)")
print(f"L/D      : {s(aero['L']/aero['D']):.2f}")
print(f"Endurance: {endurance_sec / 60} min")
print(f"Static Margin: {s(static_margin)*100:.1f} % MAC")