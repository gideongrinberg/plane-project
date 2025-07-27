#%%
import aerosandbox as asb
import aerosandbox.numpy as np
import warnings
warnings.filterwarnings("ignore")

if __name__ == "__main__":
    import ezdxf
    import pathlib
    from shapely import Polygon, box

#%%
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

airfoil_wing = asb.Airfoil(name="sd7037").repanel(200).set_TE_thickness(0.001) # this is necessary to prevent it from breaking in CAD
half_span = span / 2

x_wing = opti.variable(init_guess=0.02, lower_bound=-0.05, upper_bound=0.10)

wing = asb.Wing(
    name="Main Wing",
    symmetric=True,
    xsecs=[
        asb.WingXSec(
            xyz_le=[x_wing, 0, 0],
            chord=root_chord,
            airfoil=airfoil_wing
        ),
        asb.WingXSec(
            xyz_le=[x_wing + sweep_LE, half_span, 0],
            chord=tip_chord,
            airfoil=airfoil_wing
        ),
    ],
)

opti.subject_to([
    x_wing >= -0.03,  
    x_wing <= 0.08
])

# vtail
tail_arm = opti.variable(
    init_guess=0.60, lower_bound=0.45, upper_bound=1
)
v_dihedral_deg = 25

airfoil_tail = asb.Airfoil(name="naca0008").repanel(200).set_TE_thickness(0.001)
S_h_proj = 0.042
chord_tail_root = 0.10
taper_ratio_tail = 0.5  # From tip/root chord ratio
avg_chord_tail = chord_tail_root * (1 + taper_ratio_tail) / 2
span_tail_half = S_h_proj / (2 * avg_chord_tail * np.cos(np.radians(v_dihedral_deg)))

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
            xyz_le=vrot([tail_arm, span_tail_half, 0]),
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

x_battery = opti.variable(init_guess=-0.02, lower_bound=-0.15, upper_bound=0.05)
opti.subject_to([
    x_battery >= -0.18,
    x_battery <= 0.05
])

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
opti.subject_to(static_margin >= 0.8)

opti.subject_to(
    [
        tip_chord >= 0.06,
        tail_arm <= 0.75,
    ]
)

prop_efficiency_est = 0.67
power_required = aero["D"] * velocity / prop_efficiency_est
opti.minimize(power_required)

def solve():
    try:
        sol = opti.solve()
    except RuntimeError:
        sol = opti.debug
    return sol

if __name__ == "__main__":
    sol = solve()
else:
    import io
    import contextlib
    with contextlib.redirect_stdout(io.StringIO()):
        sol = solve()
        
airplane_sol = sol(airplane)
s = lambda x: sol.value(x)

# %%
def add_spar_channel(
    coords: np.ndarray,
    chord: float,
    spar_diameter: float = 0.008,
    spar_position_frac: float = 0.28,
    embedment_fraction: float = 0.6,
    clearance_factor: float = 1.1
):
    
    airfoil_poly = Polygon([tuple(pt) for pt in coords])
    spar_x = spar_position_frac * chord
    
    upper_points = coords[coords[:, 1] >= 0]
    lower_points = coords[coords[:, 1] <= 0]
    upper_y = np.interp(spar_x, upper_points[:, 0], upper_points[:, 1])
    lower_y = np.interp(spar_x, lower_points[:, 0], lower_points[:, 1])
    
    channel_width = spar_diameter * clearance_factor
    channel_depth = spar_diameter * embedment_fraction
    channel_center_y = lower_y - channel_depth/2
    
    cutout = box(
        spar_x - channel_width/2,
        channel_center_y - channel_depth/2,  
        spar_x + channel_width/2,
        channel_center_y + channel_depth/2
    )
    
    result = airfoil_poly.difference(cutout)
    if hasattr(result, 'exterior'):
        return np.array(result.exterior.coords)
    else:
        return np.array(result.geoms[0].exterior.coords)

def get_hinge_pos(
    coords: np.ndarray,
    chord: float,
    hinge_position_frac: float = 0.70,
):
    hinge_x = hinge_position_frac * chord
    
    upper_points = coords[coords[:, 1] >= 0]
    lower_points = coords[coords[:, 1] <= 0]
    upper_sorted = upper_points[np.argsort(upper_points[:, 0])]
    lower_sorted = lower_points[np.argsort(lower_points[:, 0])]
    upper_y = np.interp(hinge_x, upper_sorted[:, 0], upper_sorted[:, 1])
    lower_y = np.interp(hinge_x, lower_sorted[:, 0], lower_sorted[:, 1])

    return hinge_x, upper_y, lower_y

def save_wing(path, coords, chord):
    coords = coords * chord
    x, uy, ly = get_hinge_pos(coords, chord)
    coords = add_spar_channel(coords, chord)
    points = [tuple(pt) for pt in coords]

    doc = ezdxf.new(dxfversion='R2010')
    msp = doc.modelspace()
    msp.add_lwpolyline(points, close=True)

    color = 1
    layers = ["MARKS", "CHORD_LINE", "DIMENSIONS"]
    for layer in layers:
        doc.layers.new(name=layer, dxfattribs={'color': (color := color + 1)})
    
    msp.add_line(
        (x, uy), 
        (x, ly),
        dxfattribs={'layer': 'MARKS'}
    )

    msp.add_line(
        (0, 0),
        (chord, 0), 
        dxfattribs={'layer': 'CHORD_LINE'}
    )

    text_y = -0.015
    msp.add_text(
        text=f"Chord: {chord*1000:.1f}mm",
        height=0.008,
        dxfattribs={'layer': 'DIMENSIONS', 'insert': (chord/2, text_y)}
    )

    msp.doc.saveas(path)
    
# %%
if __name__ == "__main__":
    cg = sol(mass_tot).xyz_cg
    print(f"Center of Gravity (CG): x = {cg[0]:.3f} m, y = {cg[1]:.3f} m, z = {cg[2]:.3f} m")

# %% Export wings
    print("Exporting wing templates")
    templates_dir = pathlib.Path(__file__).parent.parent / "schematics" / "templates"
    subdir = lambda name: templates_dir / name
    print(templates_dir)
    wing_sol = sol(wing)
    tail_sol = sol(v_tail)
    save_wing(subdir("wing") / "root_template.dxf", wing_sol.xsecs[0].airfoil.coordinates, s(root_chord))
    save_wing(subdir("wing") / "tip_template.dxf", wing_sol.xsecs[1].airfoil.coordinates, s(tip_chord))

    save_wing(subdir("tail") / "root_template.dxf", tail_sol.xsecs[0].airfoil.coordinates, chord_tail_root)
    save_wing(subdir("tail") / "tip_template.dxf", tail_sol.xsecs[1].airfoil.coordinates, chord_tail_root * 0.5)
    print("Exported wing templates")